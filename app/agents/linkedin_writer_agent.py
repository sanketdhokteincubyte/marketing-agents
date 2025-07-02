from agno.agent import Agent, RunResponse
from agno.models.anthropic import Claude
from agno.tools.reasoning import ReasoningTools
from app.agents.base_agent import BaseAgent
from app.core import settings
from agno.utils.pprint import pprint_run_response
from typing import Iterator, List, Optional
from fastapi import UploadFile


class LinkedInWriterAgent(BaseAgent):
    def __init__(self):
        self.linkedin_writer = self._create_linkedin_writer()

    def _create_linkedin_writer(self):
        return Agent(
            name="LinkedIn Content Writer",
            role="You are an expert LinkedIn content creator specializing in professional, engaging, and viral-worthy posts",
            model=Claude(id="claude-3-7-sonnet-20250219", max_tokens=4096),
            instructions=[
                "Create compelling LinkedIn posts that drive engagement and professional value",
                "Use proven LinkedIn content frameworks and best practices",
                "Incorporate storytelling, insights, and actionable takeaways",
                "Optimize for LinkedIn algorithm preferences (engagement, comments, shares)",
                "Include appropriate hashtags and call-to-action elements",
                "Match the tone to professional yet approachable style",
                "Create content that positions the author as a thought leader",
                "Use formatting that works well on LinkedIn (line breaks, emojis when appropriate)",
                "Ensure content is valuable, authentic, and shareable",
                "Format all output in markdown for easy copying",
                "Always include 3-5 relevant hashtags at the end",
                "Create content that encourages meaningful professional discussions",
            ],
            show_tool_calls=True,
            tools=[ReasoningTools(add_instructions=True)],
            stream=True,
            markdown=True,
        )

    def generate_linkedin_post(self, prompt: str, post_type: str = "general") -> str:
        """
        Generate LinkedIn content based on the prompt and post type
        
        Args:
            prompt: The topic or idea for the LinkedIn post
            post_type: Type of post (story, tip, insight, announcement, question, list)
        """
        
        enhanced_prompt = f"""
        Create a LinkedIn post based on this prompt: "{prompt}"
        
        Post type: {post_type}
        
        LinkedIn Content Guidelines:
        1. Hook: Start with an attention-grabbing first line
        2. Value: Provide genuine insights or useful information
        3. Story: Use storytelling when appropriate to make it relatable
        4. Engagement: End with a question or call-to-action to encourage comments
        5. Format: Use line breaks, bullet points, and emojis strategically
        6. Length: Optimal for LinkedIn (typically 150-300 words)
        
        Post Type Specific Instructions:
        - Story: Share a personal or professional experience with lessons learned
        - Tip: Provide actionable advice or best practices
        - Insight: Share industry observations or thought leadership
        - Announcement: Professional updates, achievements, or news
        - Question: Pose thought-provoking questions to drive discussion
        - List: Create valuable lists (tools, resources, tips, etc.)
        
        Additional Context:
        - Target audience: Software development professionals, startup founders, tech leaders
        - Company focus: High-quality software development, AI-enhanced solutions, craftsmanship
        - Tone: Professional but approachable, confident but not arrogant
        - Goal: Build thought leadership and attract potential clients
        
        Please create an engaging LinkedIn post that follows these guidelines and generates meaningful professional engagement.
        """

        try:
            print(f"Generating LinkedIn post for prompt: {prompt}")
            response_stream: Iterator[RunResponse] = self.linkedin_writer.run(enhanced_prompt)
            content = ""
            for response in response_stream:
                content += response.content
            pprint_run_response(response, markdown=True)
            print("LinkedIn post generated successfully.")
            return content
        except Exception as e:
            print(f"Error generating LinkedIn post: {e}")
            return f"# Error generating LinkedIn post: {e}"

    def create_content_series(self, topic: str, series_length: int = 5) -> str:
        """
        Create a series of LinkedIn posts around a specific topic
        """
        
        series_prompt = f"""
        Create a series of {series_length} LinkedIn posts around the topic: "{topic}"
        
        Each post should:
        1. Stand alone as valuable content
        2. Connect to the overall theme
        3. Build anticipation for the next post
        4. Include series numbering (1/{series_length}, 2/{series_length}, etc.)
        5. Use different content formats (story, tip, insight, question, list)
        
        Please provide:
        - A brief series overview
        - {series_length} complete LinkedIn posts
        - Suggested posting schedule
        - Engagement strategy for the series
        
        Target audience: Software development professionals, startup founders, tech leaders
        Company positioning: Premium software development with AI enhancement and craftsmanship focus
        """

        try:
            print(f"Creating LinkedIn content series for topic: {topic}")
            response_stream: Iterator[RunResponse] = self.linkedin_writer.run(series_prompt)
            content = ""
            for response in response_stream:
                content += response.content
            print("LinkedIn content series created successfully.")
            return content
        except Exception as e:
            print(f"Error creating LinkedIn content series: {e}")
            return f"# Error creating content series: {e}"

    def optimize_existing_post(self, existing_post: str) -> str:
        """
        Optimize an existing LinkedIn post for better engagement
        """
        
        optimization_prompt = f"""
        Please analyze and optimize this existing LinkedIn post for better engagement:
        
        Original Post:
        {existing_post}
        
        Optimization Guidelines:
        1. Improve the hook (first line) to grab attention
        2. Enhance storytelling and emotional connection
        3. Add more value and actionable insights
        4. Improve formatting for better readability
        5. Strengthen the call-to-action
        6. Optimize hashtags for better reach
        7. Ensure alignment with LinkedIn algorithm preferences
        
        Please provide:
        - Analysis of the current post's strengths and weaknesses
        - An optimized version of the post
        - Explanation of changes made and why
        - Engagement prediction and tips
        
        Target audience: Software development professionals, startup founders, tech leaders
        """

        try:
            print("Optimizing existing LinkedIn post...")
            response_stream: Iterator[RunResponse] = self.linkedin_writer.run(optimization_prompt)
            content = ""
            for response in response_stream:
                content += response.content
            print("LinkedIn post optimization completed successfully.")
            return content
        except Exception as e:
            print(f"Error optimizing LinkedIn post: {e}")
            return f"# Error optimizing post: {e}"

    def get_response(self, prompt: str, files: Optional[List[UploadFile]] = None) -> str:
        """
        Main interface method that handles different types of LinkedIn content requests
        """
        print(f"Processing LinkedIn content request: {prompt}")
        
        # Determine the type of request based on keywords in the prompt
        prompt_lower = prompt.lower()
        
        if "series" in prompt_lower or "multiple posts" in prompt_lower:
            return self.create_content_series(prompt)
        elif "optimize" in prompt_lower or "improve" in prompt_lower:
            # Extract the post content for optimization (this is a simplified approach)
            return self.optimize_existing_post(prompt)
        else:
            # Determine post type based on keywords
            post_type = "general"
            if "story" in prompt_lower or "experience" in prompt_lower:
                post_type = "story"
            elif "tip" in prompt_lower or "advice" in prompt_lower:
                post_type = "tip"
            elif "insight" in prompt_lower or "thought" in prompt_lower:
                post_type = "insight"
            elif "announce" in prompt_lower or "launch" in prompt_lower:
                post_type = "announcement"
            elif "question" in prompt_lower or "ask" in prompt_lower:
                post_type = "question"
            elif "list" in prompt_lower or "tools" in prompt_lower or "resources" in prompt_lower:
                post_type = "list"
            
            return self.generate_linkedin_post(prompt, post_type)
