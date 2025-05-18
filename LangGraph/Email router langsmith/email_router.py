import os
from dotenv import load_dotenv
from typing_extensions import Literal, TypedDict
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

# Load environment variables
load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

# Initialize LLM
llm = ChatGroq(model="qwen-2.5-32b", temperature=0)

# Define Routing Schema
class Route(BaseModel):
    step: Literal["Support Team", "Technical Team", "Marketing Team"] = Field(
        None, description="The next step in the routing process"
    )

# Augment the LLM to ensure structured output
router = llm.with_structured_output(Route)

# Define State for LangGraph
class State(TypedDict):
    email_text: str
    decision: str
    response: str

#Router Node: Determines which team to route the email to
def email_router(state: State):
    """Routes the email to the correct team based on content."""
    
    decision = router.invoke([
        SystemMessage(content="Classify the following email and route it to Support Team, Technical Team, or Marketing Team."),
        HumanMessage(content=state["email_text"]),
    ])

    return {"decision": decision.step}

#Support Team Node: Generates a support team response
def support_team(state: State):
    """Generate a response from the support team."""
    response = llm.invoke(f"As a support agent, reply professionally to this email:\n{state['email_text']}")
    return {"response": response.content}

#Technical Team Node: Generates a technical team response
def technical_team(state: State):
    """Generate a response from the technical team."""
    response = llm.invoke(f"As a technical expert, provide a detailed response to this email:\n{state['email_text']}")
    return {"response": response.content}

#Marketing Team Node: Generates a marketing team response
def marketing_team(state: State):
    """Generate a response from the marketing team."""
    response = llm.invoke(f"As a marketing representative, craft a professional reply to this email:\n{state['email_text']}")
    return {"response": response.content}

#Conditional Routing Function
def route_decision(state: State):
    """Determines the next node based on LLM decision."""
    if state["decision"] == "Support Team":
        return "support_team"
    elif state["decision"] == "Technical Team":
        return "technical_team"
    elif state["decision"] == "Marketing Team":
        return "marketing_team"

#Build the Graph Workflow
workflow = StateGraph(State)

# Add nodes
workflow.add_node("email_router", email_router)
workflow.add_node("support_team", support_team)
workflow.add_node("technical_team", technical_team)
workflow.add_node("marketing_team", marketing_team)

# Add edges to connect nodes
workflow.add_edge(START, "email_router")
workflow.add_conditional_edges(
    "email_router",
    route_decision,
    {
        "support_team": "support_team",
        "technical_team": "technical_team",
        "marketing_team": "marketing_team",
    },
)
workflow.add_edge("support_team", END)
workflow.add_edge("technical_team", END)
workflow.add_edge("marketing_team", END)

# Compile Workflow
agent = workflow.compile()




