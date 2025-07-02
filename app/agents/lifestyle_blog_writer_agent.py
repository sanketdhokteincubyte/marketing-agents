from agno.agent import Agent, RunResponse
from agno.models.anthropic import Claude
from agno.tools.reasoning import ReasoningTools
from agno.tools.googlesearch import GoogleSearchTools
from app.agents.base_agent import BaseAgent
from app.core import settings
from agno.utils.pprint import pprint_run_response
from typing import Iterator, List, Optional
from fastapi import UploadFile


class LifestyleBlogWriterAgent(BaseAgent):
    def __init__(self):
        self.lifestyle_blog_writer = self._create_lifestyle_blog_writer()

    def _create_lifestyle_blog_writer(self):
        return Agent(
            name="Lifestyle Blog Writer",
            role="You are an expert lifestyle blog writer specializing in wellness, personal development, and lifestyle content",
            model=Claude(id="claude-3-7-sonnet-20250219", max_tokens=6144),
            instructions=[
                "Create engaging, relatable lifestyle blog posts that inspire and provide practical value",
                "Use storytelling techniques to connect emotionally with readers",
                "Include personal insights, practical tips, and actionable advice",
                "Write in a conversational, authentic tone that feels like talking to a friend",
                "Focus on topics like wellness, personal growth, relationships, productivity, and life balance",
                "Include relatable examples and real-life scenarios",
                "Use positive, uplifting language that motivates readers",
                "Structure content with engaging introductions, valuable body content, and inspiring conclusions",
                "Include practical takeaways that readers can implement immediately",
                "Use markdown formatting for better readability",
                "Create content that feels authentic and avoids being preachy",
                "Include relevant lifestyle trends and current topics when appropriate",
                "Focus on holistic well-being including mental, physical, and emotional health",
                "Make complex lifestyle concepts accessible and easy to understand",
            ],
            show_tool_calls=True,
            tools=[ReasoningTools(add_instructions=True), GoogleSearchTools()],
            stream=True,
            markdown=True,
        )

    def generate_lifestyle_blog_post(self, topic: str, style: str = "casual", length: str = "medium", focus_area: str = "general") -> str:
        """
        Generate a lifestyle blog post based on the topic, style, and length
        
        Args:
            topic: The lifestyle topic for the blog post
            style: Writing style (casual, formal, inspirational, conversational)
            length: Desired post length (short, medium, long)
            focus_area: Specific lifestyle focus (wellness, productivity, relationships, personal_growth, mindfulness, fitness)
        """
        
        # Define length specifications
        length_specs = {
            "short": "800-1200 words, focused and actionable with key insights",
            "medium": "1500-2200 words, comprehensive coverage with stories and practical tips", 
            "long": "2500-3500 words, in-depth exploration with multiple perspectives and detailed guidance"
        }
        
        # Define style specifications
        style_specs = {
            "casual": "Friendly, conversational tone like talking to a close friend, use personal anecdotes",
            "formal": "Professional yet warm tone, structured approach with clear sections and expert insights",
            "inspirational": "Uplifting, motivational tone that empowers readers to take action and embrace change",
            "conversational": "Natural, flowing dialogue style with questions and direct reader engagement"
        }
        
        # Define focus area specifications
        focus_specs = {
            "wellness": "Holistic health, mental well-being, self-care practices, and healthy lifestyle choices",
            "productivity": "Time management, goal setting, habits, work-life balance, and efficiency tips",
            "relationships": "Communication, boundaries, love, friendship, family dynamics, and social connections",
            "personal_growth": "Self-improvement, mindset, confidence, learning, and personal transformation",
            "mindfulness": "Meditation, presence, stress reduction, gratitude, and mindful living practices",
            "fitness": "Exercise routines, motivation, body positivity, nutrition, and physical wellness",
            "general": "Broad lifestyle topics covering multiple aspects of modern living"
        }

        enhanced_prompt = f"""
        Create a lifestyle blog post about: "{topic}"
        
        Specifications:
        - Style: {style} ({style_specs.get(style, style_specs['casual'])})
        - Length: {length} ({length_specs.get(length, length_specs['medium'])})
        - Focus Area: {focus_area} ({focus_specs.get(focus_area, focus_specs['general'])})
        
        Content Structure Requirements:
        1. **Compelling Title**: Engaging, relatable headline that draws readers in
        2. **Hook Opening**: Start with a relatable scenario, question, or personal story
        3. **Personal Connection**: Share relevant personal insights or experiences
        4. **Main Content**: Valuable lifestyle advice organized in digestible sections
        5. **Practical Tips**: Actionable advice readers can implement today
        6. **Real-life Examples**: Relatable scenarios and case studies
        7. **Common Challenges**: Address obstacles and how to overcome them
        8. **Mindful Reflection**: Encourage self-reflection and awareness
        9. **Inspiring Conclusion**: End with motivation and clear next steps
        10. **Call-to-Action**: Encourage reader engagement and community building
        
        Lifestyle Writing Guidelines:
        - Use inclusive language that speaks to diverse experiences
        - Include personal anecdotes and relatable stories
        - Balance inspiration with practical, actionable advice
        - Address common lifestyle challenges with empathy
        - Use conversational transitions and natural flow
        - Include questions that encourage self-reflection
        - Avoid being preachy or judgmental
        - Focus on progress over perfection
        - Include diverse perspectives on lifestyle choices
        - Use sensory details to make content vivid and engaging
        
        Target Audience Context:
        - Modern professionals seeking work-life balance
        - Individuals interested in personal growth and wellness
        - People looking for practical lifestyle improvements
        - Readers seeking authentic, relatable content
        - Community-minded individuals wanting connection and inspiration
        
        Content Themes to Weave In:
        - Authenticity and self-acceptance
        - Sustainable lifestyle changes
        - Mental health awareness and support
        - Community and connection
        - Mindful living and presence
        - Personal empowerment and growth
        - Practical wellness that fits real life
        
        Please create an engaging lifestyle blog post that provides genuine value, inspiration, and practical guidance for readers seeking to improve their daily lives and overall well-being.
        """

        try:
            print(f"Generating lifestyle blog post for topic: {topic}")
            response_stream: Iterator[RunResponse] = self.lifestyle_blog_writer.run(enhanced_prompt)
            content = ""
            for response in response_stream:
                content += response.content
            pprint_run_response(response, markdown=True)
            print("Lifestyle blog post generated successfully.")
            return content
        except Exception as e:
            print(f"Error generating lifestyle blog post: {e}")
            return f"# Error generating lifestyle blog post: {e}"

    def create_lifestyle_series(self, theme: str, series_length: int = 5, focus_area: str = "wellness") -> str:
        """
        Create a series of related lifestyle blog posts
        """
        
        series_prompt = f"""
        Create a comprehensive lifestyle blog series about: "{theme}"
        
        Series Specifications:
        - Number of posts: {series_length}
        - Focus area: {focus_area}
        - Each post should be 1500-2200 words
        - Progressive depth and practical application
        - Connected theme with standalone value
        
        Please provide:
        1. **Series Overview**: Main theme, target audience, and transformation journey
        2. **Series Outline**: Title and compelling description for each post
        3. **Detailed Content Plan**: For each post include:
           - Specific lifestyle topics to cover
           - Key insights and takeaways
           - Personal stories or examples needed
           - Practical exercises or challenges
           - Reader engagement opportunities
        4. **Community Building Strategy**: How to encourage reader interaction
        5. **Publishing Schedule**: Optimal timing and reader preparation
        6. **Series Conclusion**: How posts build toward a complete lifestyle transformation
        
        Ensure the series:
        - Builds momentum and engagement from post to post
        - Includes practical challenges and exercises
        - Addresses real-life obstacles and solutions
        - Creates a supportive community feeling
        - Offers both quick wins and long-term lifestyle changes
        - Balances inspiration with practical guidance
        
        Target Audience: People seeking authentic lifestyle improvement and personal growth
        Focus: Practical, sustainable changes that enhance daily life and well-being
        """

        try:
            print(f"Creating lifestyle blog series for theme: {theme}")
            response_stream: Iterator[RunResponse] = self.lifestyle_blog_writer.run(series_prompt)
            content = ""
            for response in response_stream:
                content += response.content
            print("Lifestyle blog series created successfully.")
            return content
        except Exception as e:
            print(f"Error creating lifestyle blog series: {e}")
            return f"# Error creating lifestyle series: {e}"

    def create_seasonal_content(self, season: str, lifestyle_focus: str = "wellness") -> str:
        """
        Create seasonal lifestyle content
        """
        
        seasonal_prompt = f"""
        Create seasonal lifestyle content for: "{season}"
        
        Focus Area: {lifestyle_focus}
        
        Seasonal Content Requirements:
        1. **Seasonal Connection**: How this time of year affects lifestyle and well-being
        2. **Timely Challenges**: Common struggles people face during this season
        3. **Seasonal Opportunities**: Unique advantages and possibilities this season offers
        4. **Practical Adaptations**: How to adjust routines and habits seasonally
        5. **Mood and Energy**: Addressing seasonal emotional and physical changes
        6. **Seasonal Activities**: Lifestyle practices that align with the season
        7. **Mindful Transitions**: How to embrace seasonal changes gracefully
        8. **Community and Connection**: Seasonal social dynamics and relationships
        9. **Self-Care Adjustments**: Season-specific wellness and self-care practices
        10. **Goal Setting**: How to align personal goals with seasonal energy
        
        Content should feel:
        - Timely and relevant to current seasonal experiences
        - Practical for implementation during this specific time
        - Sensitive to seasonal mood variations
        - Inclusive of different climate and cultural experiences
        - Focused on sustainable seasonal habits
        
        Target Audience: People seeking to live more intentionally with seasonal rhythms
        """

        try:
            print(f"Creating seasonal lifestyle content for: {season}")
            response_stream: Iterator[RunResponse] = self.lifestyle_blog_writer.run(seasonal_prompt)
            content = ""
            for response in response_stream:
                content += response.content
            print("Seasonal lifestyle content created successfully.")
            return content
        except Exception as e:
            print(f"Error creating seasonal content: {e}")
            return f"# Error creating seasonal content: {e}"

    def create_lifestyle_guide(self, topic: str, target_audience: str = "general") -> str:
        """
        Create a comprehensive lifestyle guide
        """
        
        guide_prompt = f"""
        Create a comprehensive lifestyle guide about: "{topic}"
        
        Target Audience: {target_audience}
        
        Guide Structure:
        1. **Introduction**: Why this lifestyle area matters and what readers will gain
        2. **Assessment**: Help readers understand their current situation
        3. **Foundation Building**: Core principles and mindset shifts needed
        4. **Step-by-Step Process**: Clear, actionable phases of implementation
        5. **Common Obstacles**: Challenges readers will face and how to overcome them
        6. **Tools and Resources**: Practical tools, apps, books, and resources
        7. **Real-Life Application**: How to integrate into busy, real life
        8. **Troubleshooting**: What to do when things don't go as planned
        9. **Community and Support**: Building support systems and accountability
        10. **Long-term Sustainability**: Maintaining changes and continuing growth
        11. **Celebration and Reflection**: Recognizing progress and adjusting course
        
        Guide Requirements:
        - Comprehensive yet accessible
        - Practical steps with clear timelines
        - Address different life situations and constraints
        - Include beginner to advanced strategies
        - Provide motivation and encouragement throughout
        - Offer flexible approaches for different personalities and lifestyles
        - Include reflection questions and self-assessment tools
        
        Target Audience: People ready to make meaningful lifestyle changes with practical guidance
        """

        try:
            print(f"Creating comprehensive lifestyle guide for: {topic}")
            response_stream: Iterator[RunResponse] = self.lifestyle_blog_writer.run(guide_prompt)
            content = ""
            for response in response_stream:
                content += response.content
            print("Lifestyle guide created successfully.")
            return content
        except Exception as e:
            print(f"Error creating lifestyle guide: {e}")
            return f"# Error creating lifestyle guide: {e}"

    def chat_lifestyle_advice(self, message: str, context_history: list = None) -> str:
        """
        Provide conversational lifestyle advice and coaching
        """
        
        if context_history is None:
            context_history = []
        
        # Build conversation context
        conversation_context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in context_history])
        
        chat_prompt = f"""
        You are having a supportive, friendly conversation about lifestyle and personal development.
        
        Previous conversation context:
        {conversation_context}
        
        Current message from user: "{message}"
        
        Respond as a caring lifestyle coach and friend who:
        - Listens empathetically and validates feelings
        - Asks thoughtful follow-up questions when appropriate
        - Provides practical, actionable advice
        - Shares relevant insights without being preachy
        - Encourages self-reflection and personal growth
        - Maintains a warm, supportive tone
        - Offers different perspectives and options
        - Acknowledges that everyone's lifestyle journey is unique
        
        Keep the response conversational, supportive, and practical. Focus on empowerment and positive action.
        """

        try:
            print(f"Providing lifestyle chat response for: {message[:50]}...")
            response_stream: Iterator[RunResponse] = self.lifestyle_blog_writer.run(chat_prompt)
            content = ""
            for response in response_stream:
                content += response.content
            print("Lifestyle chat response generated successfully.")
            return content
        except Exception as e:
            print(f"Error generating lifestyle chat response: {e}")
            return f"I'm sorry, I'm having trouble responding right now. Could you try asking again?"

    def get_response(self, prompt: str, files: Optional[List[UploadFile]] = None) -> str:
        """
        Main interface method that handles different types of lifestyle content requests
        """
        print(f"Processing lifestyle blog content request: {prompt}")
        
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
            return self.create_lifestyle_series(prompt, series_length)
        
        # Detect seasonal content requests
        elif any(season in prompt_lower for season in ["spring", "summer", "fall", "autumn", "winter", "seasonal", "holiday"]):
            # Extract season
            season = "current season"
            seasons = ["spring", "summer", "fall", "autumn", "winter"]
            for s in seasons:
                if s in prompt_lower:
                    season = s
                    break
            return self.create_seasonal_content(season)
        
        # Detect guide requests
        elif "guide" in prompt_lower or "comprehensive" in prompt_lower or "complete guide" in prompt_lower:
            return self.create_lifestyle_guide(prompt)
        
        # Detect chat/conversation requests
        elif "chat" in prompt_lower or "advice" in prompt_lower or "help me" in prompt_lower:
            return self.chat_lifestyle_advice(prompt)
        
        # Default to blog post generation
        else:
            # Detect style
            style = "casual"  # default
            if "formal" in prompt_lower or "professional" in prompt_lower:
                style = "formal"
            elif "inspirational" in prompt_lower or "motivational" in prompt_lower:
                style = "inspirational"
            elif "conversational" in prompt_lower:
                style = "conversational"
            
            # Detect length
            length = "medium"  # default
            if "short" in prompt_lower or "brief" in prompt_lower:
                length = "short"
            elif "long" in prompt_lower or "detailed" in prompt_lower or "comprehensive" in prompt_lower:
                length = "long"
            
            # Detect focus area
            focus_area = "general"  # default
            focus_areas = ["wellness", "productivity", "relationships", "personal_growth", "mindfulness", "fitness"]
            for area in focus_areas:
                if area in prompt_lower or area.replace("_", " ") in prompt_lower:
                    focus_area = area
                    break
            
            return self.generate_lifestyle_blog_post(prompt, style, length, focus_area)
