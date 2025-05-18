import os
from dotenv import load_dotenv
from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, START, END
from langgraph.constants import Send
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from youtube_transcript_api import YouTubeTranscriptApi
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from IPython.display import Image, display, Markdown
import operator

# Load environment variables
load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

# Initialize LLM
llm = ChatGroq(model="deepseek-r1-distill-llama-70b", temperature=0)
# Schema for structured output used in planning the script outline
class Scene(BaseModel):
    title: str = Field(description="Title of this scene in the movie script.")
    description: str = Field(description="Brief overview of what happens in this scene.")

class Scenes(BaseModel):
    scenes: List[Scene] = Field(description="Scenes of the movie script.")

# Augment the LLM with structured output for planning the script outline
planner = llm.with_structured_output(Scenes)
from langgraph.constants import Send


class State(TypedDict):
    concept: str                 # Movie concept or idea
    script_outline: List[Scene]    # List of planned scenes for the script
    completed_scenes: Annotated[List, operator.add]  # Outputs from parallel scene writing
    final_script: str            # Final synthesized movie script
    review_feedback: str         # Feedback from the AI reviewer
    human_response: str          # Human feedback input (updated via LangSmith UI)

# Worker state
class WorkerState(TypedDict):
    section: Scene
    completed_sections: Annotated[list, operator.add]


# Node 1: Outline Generator Node
def outline_generator(state: State):
    """Generates a detailed movie script outline based on the movie concept."""
    outline_request = (
        f"Generate a detailed movie script outline based on the following concept:\n\n"
        f"{state['concept']}\n\n"
        f"Include multiple scenes, each with a title and a brief description."
    )
    outline = planner.invoke(outline_request)
    print("Script Outline:", outline)
    # Limit the number of scenes to a maximum specified in the state, defaulting to 5 if not provided.
    max_scenes = state.get("max_scenes", 3)
    limited_scenes = outline.scenes[:max_scenes]
    return {"script_outline": limited_scenes}


# Node 2: Scene Writer Node (Parallel Workers)
def scene_writer(state: WorkerState):
    """Worker writes a detailed scene for the movie script."""
    scene_content = llm.invoke([
        SystemMessage(content="Write a detailed movie script scene based on the provided title and description. "
                                "Include dialogue, actions, and scene direction in markdown format, with no preamble."),
        HumanMessage(content=f"Scene Title: {state['scene'].title}\nDescription: {state['scene'].description}")
    ])
    return {"completed_scenes": [scene_content.content]}


# Node 3: Synthesizer Node
def synthesizer(state: State):
    """Synthesizes the final movie script by concatenating all completed scenes."""
    final_script = "\n\n---\n\n".join(state["completed_scenes"])
    return {"final_script": final_script}


# Node 4: Reviewer Node
def reviewer(state: State):
    """Reviews the synthesized movie script for pacing, dialogue, and overall structure."""
    feedback = llm.invoke([
        SystemMessage(content="Review the movie script for pacing, dialogue quality, and overall structure."),
        HumanMessage(content=f"Movie Script:\n{state['final_script']}")
    ])
    return {"review_feedback": feedback.content}

# Node 5: Human Feedback Node (Using LangSmith/Web UI)
def human_feedback(state: State):
    """
    Checks for human input via the state.
    If 'human_response' is not provided or is empty, returns a marker value ("awaiting_feedback")
    and instructs the user (via logs) to update the state on the LangSmith webpage.
    """
    if not state.get("human_response"):
        print("Human feedback required. Please update the 'human_response' key on the LangSmith webpage (e.g., 'yes' or 'no').")
        return {"review_feedback": "awaiting_feedback"}
    else:
        decision = state["human_response"].strip().lower()
        return {"review_feedback": "positive" if decision == "yes" else "negative"}

# Conditional Routing Function for Human Feedback
def check_review(state: State):
    """
    Routes based on the human feedback.
    If feedback is "awaiting_feedback", the workflow pauses.
    If the feedback is "negative", loop back to regenerate the outline.
    If the feedback is "positive", end the workflow.
    """
    if state.get("review_feedback") == "awaiting_feedback":
        raise Exception("Workflow paused: human feedback required. Update 'human_response' in the state and resume.")
    return "outline_generator" if state["review_feedback"] == "negative" else END
# Building the LangGraph Workflow for Movie Script Generation
workflow = StateGraph(State)

# Add nodes to the workflow
workflow.add_node("outline_generator", outline_generator)
workflow.add_node("scene_writer", scene_writer)
workflow.add_node("synthesizer", synthesizer)
workflow.add_node("reviewer", reviewer)
workflow.add_node("human_feedback", human_feedback)

# Define edges
workflow.add_edge(START, "outline_generator")
# Launch parallel scene writer workers for each scene in the outline
workflow.add_conditional_edges("outline_generator", lambda state: [Send("scene_writer", {"scene": s}) for s in state["script_outline"]], ["scene_writer"])
workflow.add_edge("scene_writer", "synthesizer")
workflow.add_edge("synthesizer", "reviewer")
workflow.add_edge("reviewer", "human_feedback")
workflow.add_conditional_edges("human_feedback", check_review, {"outline_generator": "outline_generator", END: END})

# Compile the workflow
agent = workflow.compile()

