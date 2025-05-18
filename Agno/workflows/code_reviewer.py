from textwrap import dedent
from typing import Iterator

from agno.agent import Agent
from agno.models.groq import Groq
from agno.utils.log import logger
from agno.workflow import RunEvent, RunResponse, Workflow
from pydantic import BaseModel, Field
from agno.utils.pprint import pprint_run_response


class CodeGenerator(BaseModel):
    code: str = Field(..., description="Generated code according to user input.")


class Reviewer(BaseModel):
    review: str = Field(..., description="Review of the generated code.")


class Documentation(BaseModel):
    doc: str = Field(..., description="Documentation of the final code.")


class CodeReviewer(Workflow):
    """Advanced workflow for generating, reviewing, and documenting code as per user query."""

    description: str = dedent("""\
    An intelligent code reviewer that generates, refines, and documents high-quality code.
    This workflow orchestrates multiple AI agents to generate code from user input, review it 
    for best practices and potential improvements, and produce comprehensive documentation.
    The system ensures that the final code is efficient, robust, and well-commented, merging
    technical accuracy with clarity for maintainability.
    """)

    # Agent that generates code based on a coding query.
    code_generator: Agent = Agent(
        model=Groq("llama-3.3-70b-versatile"),
        description=dedent("""\
        You are CodeGen-X, an elite code generation agent specializing in transforming user requirements into clean, efficient, and maintainable code. Your expertise includes:
        
        - Translating natural language requirements into structured, executable code
        - Implementing best coding practices and design patterns
        - Ensuring optimal performance and scalability
        - Handling multiple programming languages and paradigms
        - Producing code that is robust, well-documented, and easy to maintain
        """),
        instructions=dedent("""\
        1. Requirement Analysis 🔍
           - Parse and fully understand the provided coding requirements
           - Identify essential functions, classes, and potential edge cases
        2. Code Generation 💻
           - Generate code that accurately fulfills the specified requirements
           - Adhere to best practices for clarity, structure, and maintainability
           - Embed inline comments and documentation where appropriate
        3. Quality Assurance ✔️
           - Ensure the generated code is efficient, error-free, and optimized for performance
           - Validate that the code meets the desired specifications and handles edge cases
           - Include error handling and, where applicable, unit tests for critical components
        """),
        response_model=CodeGenerator,
    )

    # Agent that reviews the generated code.
    code_reviewer: Agent = Agent(
        model=Groq("llama-3.3-70b-versatile"),
        markdown=True,
        description=dedent("""\
        You are CodeReview-X, an expert code review agent specializing in evaluating and improving code quality.
        Your expertise includes:
        
        - Analyzing code structure and design
        - Identifying potential errors and inefficiencies
        - Providing actionable improvement suggestions
        - Ensuring adherence to coding best practices
        - Delivering clear, concise feedback for refinement
        """),
        instructions=dedent("""\
        1. Code Analysis 🔍
           - Examine the provided code for logical errors and potential performance issues
           - Assess readability, maintainability, and adherence to best practices
           - Identify opportunities for refactoring or optimization
        2. Feedback Generation 📝
           - Provide specific, actionable feedback if improvements are needed
           - Clearly indicate areas that require changes by using keywords like "change" or "improve"
           - If the code meets quality standards, simply state "The code is good"
        3. Quality Assurance ✅
           - Ensure feedback is constructive and beneficial for further refinement
           - Maintain a professional and supportive tone throughout the review process
        """),
        response_model=Reviewer,
    )

    # Agent that documents the final code.
    code_documenter: Agent = Agent(
        model=Groq("llama-3.3-70b-versatile"),  
        description=dedent("""\
        You are CodeDoc-X, an elite code documentator that produces comprehensive and clear documentation for code.
        Your expertise includes:
        
        - Explaining the purpose and functionality of code segments
        - Creating detailed inline comments and descriptions
        - Providing usage examples and context for functions, classes, and modules
        - Structuring documentation in a logical, accessible format
        - Enhancing code maintainability through clear, accurate documentation
        """),
        instructions=dedent("""\
        1. Documentation Strategy 📚
           - Write clear, concise explanations of the provided code
           - Break down complex logic into understandable segments
           - Include usage examples and sample outputs where applicable
        2. Code Annotation ✍️
           - Generate inline comments that explain key code blocks and their functionality
           - Provide context on design choices and the purpose behind code segments
        3. Structured Output 🗂
           - Format the documentation in a structured format (e.g., Markdown)
           - Include sections such as Overview, Detailed Breakdown, and Usage Examples
        4. Quality Assurance ✅
           - Ensure the documentation is accurate, comprehensive, and accessible to developers of all levels
           - Maintain a consistent tone and style throughout the document
        """),
        expected_output=dedent("""\
        # Code Documentation

        ## Overview
        {A brief description of the code's purpose, overall structure, and functionality.}

        ## Detailed Breakdown
        ### Function/Class 1: {Name}
        - **Purpose:** {Description of the function or class purpose.}
        - **Parameters:** {List and explain the parameters.}
        - **Returns:** {Describe the return values.}
        - **Usage Example:**
          ```python
          {Example code snippet demonstrating usage.}
          ```

        ### Function/Class 2: {Name}
        - **Purpose:** {Description of the function or class purpose.}
        - **Parameters:** {List and explain the parameters.}
        - **Returns:** {Describe the return values.}
        - **Usage Example:**
          ```python
          {Example code snippet demonstrating usage.}
          ```

        ## Additional Notes
        {Any extra details, potential pitfalls, or recommendations for further improvements.}
        """),
        markdown=True,
    )

    def run(self, query: str) -> Iterator[RunResponse]:
        logger.info(f"Running code reviewer workflow for query: {query}")

        # Step 1: Generate Code
        gen_response = self.code_generator.run(query)
        generated_code = gen_response.content
        logger.info("Generated code obtained.")

        # Step 2: Review the Generated Code
        review_prompt = dedent(f"""\
            Please review the following code. Provide feedback if improvements are needed,
            or state "The code is good" if no changes are required.
            
            --- Code Begin ---
            {generated_code}
            --- Code End ---
        """)
        review_response = self.code_reviewer.run(review_prompt)
        review_feedback = review_response.content
        logger.info("Code review completed.")

        # Conditional Refinement: If feedback suggests changes, refine the code.
        if "change" in review_feedback or "improve" in review_feedback:
            refinement_prompt = dedent(f"""\
                The following feedback was received for the code:
                {review_feedback}
                
                Please refine the original code accordingly.
                
                --- Original Code ---
                {generated_code}
            """)
            refined_response = self.code_generator.run(refinement_prompt)
            final_code = refined_response.content
            logger.info("Code refined based on review feedback.")
        else:
            final_code = generated_code
            logger.info("No refinement needed; using original generated code.")

        # Step 3: Document the Final Code
        doc_prompt = dedent(f"""\
            Generate documentation for the following code. Include inline comments,
            detailed explanations, and usage examples.
            
            --- Code Begin ---
            {final_code}
            --- Code End ---
        """)
        doc_response = self.code_documenter.run(doc_prompt)
        documentation = doc_response.content
        logger.info("Documentation generated.")

        # Prepare the final structured output without using JSON
        final_output_str = dedent(f"""\
            Final Code:
            {final_code}

            Documentation:
            {documentation}

            Review Feedback:
            {review_feedback}
        """)
        yield RunResponse(content=final_output_str, event=RunEvent.workflow_completed)


# Example usage:
if __name__ == "__main__":
    from rich.prompt import Prompt

    query = Prompt.ask("Enter your code generation query")
    workflow = CodeReviewer(session_id="code_reviewer_workflow")
    output: Iterator[RunResponse] = workflow.run(query=query)

    pprint_run_response(output, markdown=True)
