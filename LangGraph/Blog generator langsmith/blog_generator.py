import os
from dotenv import load_dotenv
from typing import TypedDict, Annotated, List
import operator
from langgraph.graph import StateGraph, START, END
from langgraph.constants import Send
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from youtube_transcript_api import YouTubeTranscriptApi
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# Load environment variables
load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

# Initialize LLM
llm = ChatGroq(model="qwen-2.5-32b", temperature=0)

# Schema for structured output used in planning
class Section(BaseModel):
    name: str = Field(description="Name for this section of the blog.")
    description: str = Field(description="Brief overview of the main topics and concepts to be covered in this section.")

class Sections(BaseModel):
    sections: List[Section] = Field(description="Sections of the blog.")

# Augment the LLM with structured output for planning
planner = llm.with_structured_output(Sections)

# Graph state
class State(TypedDict):
    url: str                        # URL of the video
    transcript: str                 # Transcript of the video
    sections: List[Section]         # List of blog sections from the planner
    completed_sections: Annotated[List, operator.add]  # Workers write their output here in parallel
    final_blog: str                 # Synthesized final blog content (formatted as Markdown)
    review_feedback: str            # Feedback from the AI reviewer
    # This key will be updated via LangSmith's UI for human input.
    human_response: str             

# Worker state (for blog_writer)
class WorkerState(TypedDict):
    section: Section
    completed_sections: Annotated[List, operator.add]

# 📍 1️⃣ YouTube Transcript Generator Node
def youtube_transcript(state: State):
    """Fetches transcript from a YouTube video."""
    video_id = state["url"].split("v=")[-1]  # Extract video ID
    transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
    transcript = " ".join([entry["text"] for entry in transcript_data])
    return {"transcript": transcript}

# 📍 2️⃣ Orchestrator Node
def orchestrator(state: State):
    """Orchestrator that generates a plan for writing the blog."""
    transcript_sections = planner.invoke([
        SystemMessage(content="Generate a plan for workers to write a blog."),
        HumanMessage(content=f"Here is the blog transcript: {state['transcript']}"),
    ])
    return {"sections": transcript_sections.sections}

# 📍 3️⃣ Worker Node (Parallel Blog Writing)
def blog_writer(state: WorkerState):
    """Worker writes a section of the blog."""
    section = llm.invoke([
        SystemMessage(content="Write a blog section following the provided name and description. Include no preamble for each section. Use markdown formatting."),
        HumanMessage(content=f"Section Name: {state['section'].name}\nDescription: {state['section'].description}")
    ])
    return {"completed_sections": [section.content]}

# 📍 4️⃣ Synthesizer Node
def synthesizer(state: State):
    """Synthesizes the final blog from completed sections and formats it in Markdown."""
    completed_blog_sections = "\n\n---\n\n".join(state["completed_sections"])
    markdown_blog = f"# Final Blog\n\n{completed_blog_sections}"
    return {"final_blog": markdown_blog}

# 📍 5️⃣ Blog Review Node
def reviewer(state: State):
    """Reviews the synthesized blog."""
    feedback = llm.invoke([
        SystemMessage(content="Review the blog for accuracy, readability, and engagement."),
        HumanMessage(content=f"Blog Content: {state['final_blog']}")
    ])
    return {"review_feedback": feedback.content}

# 📍 6️⃣ Human Feedback Node (Modified for LangSmith/Web UI)
def human_feedback(state: State):
    """
    Checks for human input via the state.
    If 'human_response' is not provided or empty, returns a marker ("awaiting_feedback")
    and instructs the user to update the state on the LangSmith webpage.
    """
    if not state.get("human_response"):
        print("Human feedback required. Please update the 'human_response' key on the LangSmith webpage (e.g., 'yes' or 'no').")
        return {"review_feedback": "awaiting_feedback"}
    else:
        decision = state["human_response"].strip().lower()
        return {"review_feedback": "positive" if decision == "yes" else "negative"}

# 📍 Conditional Routing Function
def check_review(state: State):
    """
    Routes based on human feedback.
    If review_feedback is "awaiting_feedback", the workflow pauses.
    If the feedback is "negative", the workflow loops back to the orchestrator.
    If the feedback is "positive", the workflow ends.
    """
    if state.get("review_feedback") == "awaiting_feedback":
        raise Exception("Workflow paused: human feedback required. Please update 'human_response' in the state and resume.")
    return "orchestrator" if state["review_feedback"] == "negative" else END

# 🌐 Building the LangGraph Workflow
workflow = StateGraph(State)

# Add nodes
workflow.add_node("youtube_transcript", youtube_transcript)
workflow.add_node("orchestrator", orchestrator)
workflow.add_node("blog_writer", blog_writer)
workflow.add_node("synthesizer", synthesizer)
workflow.add_node("reviewer", reviewer)
workflow.add_node("human_feedback", human_feedback)

# Define edges
workflow.add_edge(START, "youtube_transcript")
workflow.add_edge("youtube_transcript", "orchestrator")
# Launch parallel blog writer workers for each section
workflow.add_conditional_edges("orchestrator", lambda state: [Send("blog_writer", {"section": s}) for s in state["sections"]], ["blog_writer"])
workflow.add_edge("blog_writer", "synthesizer")
workflow.add_edge("synthesizer", "reviewer")
workflow.add_edge("reviewer", "human_feedback")
workflow.add_conditional_edges("human_feedback", check_review, {"orchestrator": "orchestrator", END: END})

# Compile workflow (set to interrupt before human_feedback for human input)
agent = workflow.compile()



