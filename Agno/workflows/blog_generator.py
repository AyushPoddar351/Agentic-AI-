from textwrap import dedent
from typing import Iterator

from agno.agent import Agent
from agno.models.groq import Groq
from agno.utils.log import logger
from agno.workflow import RunEvent, RunResponse, Workflow
from agno.utils.pprint import pprint_run_response


class BlogGenerator(Workflow):
    """An intelligent blog generator that creates a cohesive blog post from a YouTube video link.
    
    The workflow:
      1. Extracts the transcript from the YouTube video.
      2. Generates a list of blog topics with descriptions based on the transcript.
      3. Assigns agents to write detailed blog sections for each topic.
      4. Compiles the individual sections into a final blog post.
    """

    description: str = dedent("""\
        An intelligent blog generator that transforms a YouTube video into a well-structured blog post.
        The workflow extracts the video's transcript, creates blog topics with descriptions,
        delegates the writing of individual sections to specialized agents, and compiles the final output.
    """)

    # Agent to extract transcript from a YouTube video.
    transcript_extractor: Agent = Agent(
        model=Groq("llama-3.3-70b-versatile"),
        description=dedent("""\
            You are Transcripto-X, a transcript extraction agent. Given a YouTube video link,
            extract the video's transcript as plain text.
        """),
        instructions=dedent("""\
            1. Extract the video ID from the provided YouTube link.
            2. Fetch and combine the transcript text.
            3. Return the complete transcript as plain text.
        """),
    )

    # Agent to generate blog topics from the transcript.
    topic_generator: Agent = Agent(
        model=Groq("llama-3.3-70b-versatile"),
        description=dedent("""\
            You are TopicGen-X, an expert in creating engaging blog topics.
            Given a transcript, generate a list of blog topics with brief descriptions.
        """),
        instructions=dedent("""\
            1. Analyze the transcript to identify key themes and ideas.
            2. Generate a list of 3-5 blog topics, each with a short description.
            3. Format each topic as: 'Topic Title: Brief Description'.
        """),
    )

    # Agent to write detailed blog sections for each topic.
    section_writer: Agent = Agent(
        model=Groq("llama-3.3-70b-versatile"),
        description=dedent("""\
            You are SectionWriter-X, a skilled content creator.
            Given a blog topic and context from the transcript, write a detailed blog section.
        """),
        instructions=dedent("""\
            1. Use the provided topic and transcript context to craft a detailed blog section.
            2. Ensure the section is engaging, informative, and well-structured.
            3. Include examples, explanations, and any relevant insights.
        """),
    )

    # Agent to compile individual sections into a cohesive blog post.
    compiler: Agent = Agent(
        model=Groq("llama-3.3-70b-versatile"),
        description=dedent("""\
            You are BlogCompiler-X, an expert in organizing content.
            Given multiple blog sections, compile them into a single, cohesive blog post.
        """),
        instructions=dedent("""\
            1. Organize the provided sections logically.
            2. Ensure smooth transitions between sections.
            3. Output the final blog post as plain text with a title and conclusion.
        """),
    )

    def run(self, video_url: str) -> Iterator[RunResponse]:
        logger.info(f"Generating blog post from video: {video_url}")

        # Step 1: Extract Transcript
        transcript_response = self.transcript_extractor.run(video_url)
        transcript = transcript_response.content
        logger.info("Transcript extracted.")

        # Step 2: Generate Blog Topics with Descriptions
        topics_prompt = dedent(f"""\
            Given the following transcript, generate a list of blog topics with brief descriptions.
            Transcript:
            {transcript}
        """)
        topics_response = self.topic_generator.run(topics_prompt)
        topics_text = topics_response.content.strip()
        logger.info("Blog topics generated.")

        # Assume each line of the output is in the format "Topic Title: Description"
        topics = topics_text.splitlines()
        sections = []

        # Step 3: Write Blog Sections for Each Topic
        for topic in topics:
            section_prompt = dedent(f"""\
                Write a detailed blog section on the following topic using the transcript for context.
                Topic: {topic}
                Transcript:
                {transcript}
            """)
            section_response = self.section_writer.run(section_prompt)
            section_content = section_response.content.strip()
            sections.append(f"{topic}\n{section_content}")
            logger.info(f"Section written for topic: {topic.split(':')[0]}")

        # Step 4: Compile Final Blog Post
        compiled_prompt = dedent(f"""\
            Compile the following blog sections into a cohesive blog post. Ensure a strong title, smooth transitions, and a compelling conclusion.
            Sections:
            {'\n\n'.join(sections)}
        """)
        compile_response = self.compiler.run(compiled_prompt)
        final_blog = compile_response.content.strip()
        logger.info("Blog post compiled.")

        # Prepare final output as a plain text string
        final_output_str = dedent(f"""\
            Final Blog Post:
            {final_blog}
        """)
        yield RunResponse(content=final_output_str, event=RunEvent.workflow_completed)


# Example usage:
if __name__ == "__main__":
    from rich.prompt import Prompt

    video_url = Prompt.ask("Enter a YouTube video URL")
    workflow = BlogGenerator(session_id="blog_generator_workflow")
    output: Iterator[RunResponse] = workflow.run(video_url=video_url)

    pprint_run_response(output, markdown=True)
