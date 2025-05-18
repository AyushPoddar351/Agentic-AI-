from typing import Annotated
from typing_extensions import TypedDict
from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
os.environ["LANGSMITH_API_KEY"]=os.getenv("LANGCHAIN_API_KEY")

# Initialize LLM
llm = ChatGroq(model="qwen-2.5-32b", temperature=0)

# Graph states
class State(TypedDict):
    task : str
    reviewer : str
    manager : str
    
def code_peer_review_agent():
    """Code peer review agent"""
    
    def generate_code(state: State):
        """First LLM call to generate code for the given input task"""

        msg = llm.invoke(f"Write a python code for solving the problem {state['task']}")
        
        return {'reviewer' : msg.content}

    def review(state: State):
        """Review the generated code with detailed feedback"""
        
        prompt = f"""
        Review the following Python code:
        {state['reviewer']}
        
        Look for:
        - Syntax errors
        - Logical errors
        - Best practices
        - Code efficiency

        Provide a structured review with a summary of issues and a final verdict:
        - 'Code is perfect' if no issues.
        - 'Code needs improvement' if issues exist.
        """
        
        msg = llm.invoke(prompt)
        return {'manager': msg}

    def check_code(state: State):
        """Function to check if the code is perfect or needs improvement"""

        if state['reviewer'] == 'Code needs improvement':
            return 'Fail'
        return 'Pass'
    
    def document(state: State):
        """Third LLM call so that the code can be documented"""
        
        msg = llm.invoke(f"Document the code for {state['task']}")

        return {'manager' : msg.content}

    # Build workflow
    workflow = StateGraph(State)

    # Add nodes
    workflow.add_node("generate_code", generate_code)
    workflow.add_node("review", review)
    workflow.add_node("document", document)

    # Add edges to connect nodes
    workflow.add_edge(START, "generate_code")
    workflow.add_edge("generate_code", "review")
    workflow.add_conditional_edges("review",check_code,{'Pass':'document','Fail':'generate_code'})
    workflow.add_edge("document", END)

    graph = workflow.compile()
    return graph

# Compile
agent = code_peer_review_agent()
