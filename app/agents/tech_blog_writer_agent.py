from agno.agent import Agent, RunResponse
from agno.models.anthropic import Claude
from agno.tools.reasoning import ReasoningTools
from agno.tools.googlesearch import GoogleSearchTools
from app.agents.base_agent import BaseAgent
from app.core import settings
from agno.utils.pprint import pprint_run_response
from typing import Iterator, List, Optional
from fastapi import UploadFile


class TechBlogWriterAgent(BaseAgent):
    def __init__(self):
        self.tech_blog_writer = self._create_tech_blog_writer()

    def _create_tech_blog_writer(self):
        return Agent(
            name="Technical Blog Writer",
            role="You are an expert technical blog writer specializing in software development, AI, and technology content",
            model=Claude(id="claude-3-7-sonnet-20250219", max_tokens=8096),
            instructions=[
                "Create comprehensive, well-structured technical blog posts that educate and engage developers",
                "Include clear explanations of technical concepts with appropriate depth for the target audience",
                "Provide practical code examples, best practices, and real-world applications",
                "Structure content with proper headings, subheadings, and logical flow",
                "Include common pitfalls, troubleshooting tips, and performance considerations",
                "Use markdown formatting for code blocks, links, and emphasis",
                "Ensure content is accurate, up-to-date, and follows industry standards",
                "Create engaging introductions that hook readers and clear conclusions that summarize key points",
                "Include relevant technical keywords for SEO without keyword stuffing",
                "Provide actionable takeaways that readers can implement immediately",
                "Adapt writing style and complexity based on target audience level",
                "Include references to documentation, tools, and additional resources when helpful",
                "Focus on practical value and real-world problem solving",
                "Ensure code examples are syntactically correct and follow best practices",
            ],
            show_tool_calls=True,
            tools=[ReasoningTools(add_instructions=True), GoogleSearchTools()],
            stream=True,
            markdown=True,
        )

    def generate_tech_blog_post(self, topic: str, complexity: str = "intermediate", length: str = "medium", post_type: str = "tutorial") -> str:
        """
        Generate a technical blog post based on the topic, complexity, and length
        
        Args:
            topic: The technical topic for the blog post
            complexity: Target audience level (beginner, intermediate, advanced)
            length: Desired post length (short, medium, long)
            post_type: Type of post (tutorial, explainer, review, comparison, guide, news)
        """
        
        # Define length specifications
        length_specs = {
            "short": "800-1200 words, focus on key concepts and quick implementation",
            "medium": "1500-2500 words, comprehensive coverage with examples and best practices", 
            "long": "3000-5000 words, in-depth analysis with multiple examples, case studies, and advanced topics"
        }
        
        # Define complexity specifications
        complexity_specs = {
            "beginner": "Assume basic programming knowledge, explain fundamental concepts clearly, include step-by-step instructions",
            "intermediate": "Assume solid programming foundation, focus on practical implementation and best practices",
            "advanced": "Assume expert-level knowledge, dive deep into implementation details, performance optimization, and edge cases"
        }
        
        # Define post type specifications
        post_type_specs = {
            "tutorial": "Step-by-step guide with hands-on examples and code implementations",
            "explainer": "Deep dive into concepts, theories, and how things work under the hood",
            "review": "Analysis and evaluation of tools, libraries, frameworks, or technologies",
            "comparison": "Side-by-side comparison of different approaches, tools, or technologies",
            "guide": "Comprehensive reference covering multiple aspects of a topic",
            "news": "Analysis of recent developments, updates, or trends in technology"
        }

        enhanced_prompt = f"""
        Create a technical blog post about: "{topic}"
        
        Specifications:
        - Complexity Level: {complexity} ({complexity_specs.get(complexity, complexity_specs['intermediate'])})
        - Length: {length} ({length_specs.get(length, length_specs['medium'])})
        - Post Type: {post_type} ({post_type_specs.get(post_type, post_type_specs['tutorial'])})
        
        Content Structure Requirements:
        1. **Engaging Title**: Create a compelling, SEO-friendly title
        2. **Hook Introduction**: Start with a relatable problem or interesting insight
        3. **Clear Outline**: Brief overview of what the post will cover
        4. **Main Content**: Detailed technical content with proper sections
        5. **Code Examples**: Practical, runnable code snippets with explanations
        6. **Best Practices**: Industry-standard recommendations and tips
        7. **Common Pitfalls**: What to avoid and how to troubleshoot issues
        8. **Real-world Applications**: How this applies in actual development scenarios
        9. **Performance Considerations**: Optimization tips and considerations
        10. **Conclusion**: Summary of key takeaways and next steps
        11. **Additional Resources**: Links to documentation, tools, and further reading
        
        Technical Writing Guidelines:
        - Use clear, concise language appropriate for the complexity level
        - Include proper markdown formatting for code blocks with language specification
        - Add comments to code examples explaining key concepts
        - Use bullet points and numbered lists for better readability
        - Include relevant technical diagrams or flowcharts when helpful (describe them)
        - Ensure all code examples are syntactically correct and follow best practices
        - Include error handling and edge cases in code examples
        - Reference official documentation and authoritative sources
        
        Target Audience Context:
        - Software developers and engineers
        - Technical leads and architects
        - DevOps and infrastructure professionals
        - Students and professionals learning new technologies
        
        Company Positioning:
        - High-quality software development focus
        - AI-enhanced development practices
        - Emphasis on craftsmanship and best practices
        - Modern, cutting-edge technology adoption
        
        Please create a comprehensive technical blog post that provides genuine value to developers and establishes thought leadership in the software development community.
        """

        try:
            print(f"Generating technical blog post for topic: {topic}")
            response_stream: Iterator[RunResponse] = self.tech_blog_writer.run(enhanced_prompt)
            content = ""
            for response in response_stream:
                content += response.content
            pprint_run_response(response, markdown=True)
            print("Technical blog post generated successfully.")
            return content
        except Exception as e:
            print(f"Error generating technical blog post: {e}")
            return f"# Error generating technical blog post: {e}"

    def create_blog_series(self, topic: str, series_length: int = 5, complexity: str = "intermediate") -> str:
        """
        Create a series of related technical blog posts
        """
        
        series_prompt = f"""
        Create a comprehensive blog series about: "{topic}"
        
        Series Specifications:
        - Number of posts: {series_length}
        - Complexity level: {complexity}
        - Each post should be 1500-2500 words
        - Progressive difficulty and depth
        
        Please provide:
        1. **Series Overview**: Main theme and learning objectives
        2. **Series Outline**: Title and brief description for each post
        3. **Detailed Content Plan**: For each post include:
           - Specific topics to cover
           - Key concepts to explain
           - Code examples needed
           - Prerequisites and dependencies
        4. **Publishing Schedule**: Recommended timing between posts
        5. **Cross-linking Strategy**: How posts should reference each other
        6. **Call-to-Action**: How to engage readers throughout the series
        
        Ensure the series:
        - Builds knowledge progressively from post to post
        - Can be read independently but benefits from sequential reading
        - Includes practical projects or exercises
        - Covers both theory and practical implementation
        - Appeals to {complexity} level developers
        
        Target Audience: Software developers, technical leads, and engineering teams
        Focus: Practical, actionable content that solves real development challenges
        """

        try:
            print(f"Creating technical blog series for topic: {topic}")
            response_stream: Iterator[RunResponse] = self.tech_blog_writer.run(series_prompt)
            content = ""
            for response in response_stream:
                content += response.content
            print("Technical blog series created successfully.")
            return content
        except Exception as e:
            print(f"Error creating technical blog series: {e}")
            return f"# Error creating blog series: {e}"

    def review_technology(self, technology: str, focus_areas: list = None) -> str:
        """
        Create a comprehensive technology review or analysis
        """
        
        if focus_areas is None:
            focus_areas = ["features", "performance", "ease_of_use", "ecosystem", "community", "pricing"]
        
        review_prompt = f"""
        Create a comprehensive technical review and analysis of: "{technology}"
        
        Review Focus Areas: {', '.join(focus_areas)}
        
        Review Structure:
        1. **Technology Overview**: What it is, what problem it solves, target use cases
        2. **Key Features**: Core capabilities and unique selling points
        3. **Technical Analysis**: Architecture, performance characteristics, scalability
        4. **Pros and Cons**: Honest assessment of strengths and weaknesses
        5. **Use Cases**: When to use it vs when not to use it
        6. **Comparison**: How it compares to alternatives in the market
        7. **Getting Started**: Setup process, learning curve, documentation quality
        8. **Community and Ecosystem**: Support, plugins, third-party tools
        9. **Pricing and Licensing**: Cost considerations for different use cases
        10. **Future Outlook**: Development roadmap, sustainability, market trends
        11. **Recommendation**: Who should consider this technology and why
        
        Requirements:
        - Include specific examples and use cases
        - Provide code snippets demonstrating key features
        - Be objective and balanced in assessment
        - Include performance benchmarks if relevant
        - Consider different perspectives (startup vs enterprise, individual vs team)
        - Include real-world adoption examples
        
        Target Audience: Technical decision makers, developers evaluating technology choices
        """

        try:
            print(f"Creating technology review for: {technology}")
            response_stream: Iterator[RunResponse] = self.tech_blog_writer.run(review_prompt)
            content = ""
            for response in response_stream:
                content += response.content
            print("Technology review created successfully.")
            return content
        except Exception as e:
            print(f"Error creating technology review: {e}")
            return f"# Error creating technology review: {e}"

    def create_technical_comparison(self, technologies: list, comparison_criteria: list = None) -> str:
        """
        Create a detailed comparison between multiple technologies
        """
        
        if comparison_criteria is None:
            comparison_criteria = ["performance", "ease_of_use", "learning_curve", "community", "ecosystem", "cost", "scalability"]
        
        comparison_prompt = f"""
        Create a comprehensive technical comparison between: {', '.join(technologies)}
        
        Comparison Criteria: {', '.join(comparison_criteria)}
        
        Comparison Structure:
        1. **Executive Summary**: Quick overview of recommendations for different use cases
        2. **Technology Overviews**: Brief introduction to each technology
        3. **Feature Comparison Matrix**: Side-by-side feature comparison table
        4. **Detailed Analysis**: In-depth comparison across all criteria
        5. **Performance Benchmarks**: Quantitative comparisons where possible
        6. **Use Case Scenarios**: Which technology works best for specific scenarios
        7. **Migration Considerations**: Switching between these technologies
        8. **Cost Analysis**: Total cost of ownership comparison
        9. **Decision Framework**: How to choose between these options
        10. **Recommendations**: Specific recommendations for different team sizes and use cases
        
        Requirements:
        - Include concrete examples and benchmarks
        - Provide code samples showing key differences
        - Be objective and fair to all technologies
        - Include real-world case studies if possible
        - Consider both technical and business factors
        - Address common decision points and concerns
        
        Target Audience: Technical leads, architects, and decision makers evaluating technology choices
        """

        try:
            print(f"Creating technical comparison for: {', '.join(technologies)}")
            response_stream: Iterator[RunResponse] = self.tech_blog_writer.run(comparison_prompt)
            content = ""
            for response in response_stream:
                content += response.content
            print("Technical comparison created successfully.")
            return content
        except Exception as e:
            print(f"Error creating technical comparison: {e}")
            return f"# Error creating technical comparison: {e}"

    def get_response(self, prompt: str, files: Optional[List[UploadFile]] = None) -> str:
        """
        Main interface method that handles different types of technical blog content requests
        """
        print(f"Processing technical blog content request: {prompt}")
        
        # Parse the prompt to determine the type of content and parameters
        prompt_lower = prompt.lower()
        
        # Detect series requests
        if "series" in prompt_lower or "multiple posts" in prompt_lower:
            # Extract series length if specified
            series_length = 5  # default
            for num in range(3, 11):  # check for numbers 3-10
                if str(num) in prompt:
                    series_length = num
                    break
            return self.create_blog_series(prompt, series_length)
        
        # Detect review requests
        elif "review" in prompt_lower or "analyze" in prompt_lower:
            return self.review_technology(prompt)
        
        # Detect comparison requests
        elif "compare" in prompt_lower or "vs" in prompt_lower or " versus " in prompt_lower:
            # Simple extraction - in a real implementation, you might want more sophisticated parsing
            technologies = []
            if " vs " in prompt_lower:
                parts = prompt.split(" vs ")
                technologies = [part.strip() for part in parts[:2]]
            elif " versus " in prompt_lower:
                parts = prompt.split(" versus ")
                technologies = [part.strip() for part in parts[:2]]
            
            if len(technologies) >= 2:
                return self.create_technical_comparison(technologies)
            else:
                return self.create_technical_comparison([prompt])
        
        # Default to blog post generation
        else:
            # Detect complexity level
            complexity = "intermediate"  # default
            if "beginner" in prompt_lower or "basic" in prompt_lower:
                complexity = "beginner"
            elif "advanced" in prompt_lower or "expert" in prompt_lower:
                complexity = "advanced"
            
            # Detect length
            length = "medium"  # default
            if "short" in prompt_lower or "brief" in prompt_lower:
                length = "short"
            elif "long" in prompt_lower or "detailed" in prompt_lower or "comprehensive" in prompt_lower:
                length = "long"
            
            # Detect post type
            post_type = "tutorial"  # default
            if "tutorial" in prompt_lower or "how to" in prompt_lower:
                post_type = "tutorial"
            elif "explain" in prompt_lower or "what is" in prompt_lower:
                post_type = "explainer"
            elif "guide" in prompt_lower:
                post_type = "guide"
            elif "news" in prompt_lower or "update" in prompt_lower:
                post_type = "news"
            
            return self.generate_tech_blog_post(prompt, complexity, length, post_type)
