from agno.agent import Agent, RunResponse
from agno.models.anthropic import Claude
from agno.media import Image
from app.agents.base_agent import BaseAgent
from app.core import settings
from typing import List, Optional
from fastapi import UploadFile
import tempfile
import os


class ImageNERAgent(BaseAgent):
    """
    Named Entity Recognition Agent for Image Processing
    
    This agent analyzes images to identify and extract named entities,
    presenting them as structured key-value pairs.
    """
    
    def __init__(self, model_id='claude-3-5-sonnet-20241022'):
        self.agent = Agent(
            model=Claude(id=model_id, api_key=settings.ANTHROPIC_API_KEY),
            name="Image NER Agent",
            agent_id="image-ner-agent",
            description="An AI agent specialized in extracting named entities from images",
            instructions=[
                "You are a specialized Named Entity Recognition (NER) agent that analyzes images to identify and extract named entities.",
                "Your task is to carefully examine the provided image and identify all visible named entities.",
                "Focus on extracting the following types of entities:",
                "- PERSON: Names of people, characters, or individuals",
                "- ORGANIZATION: Company names, institutions, brands, logos",
                "- LOCATION: Places, addresses, geographical locations, landmarks",
                "- PRODUCT: Product names, models, brands visible on items",
                "- EVENT: Names of events, conferences, meetings",
                "- DATE: Dates, times, years visible in the image",
                "- MONEY: Currency amounts, prices, financial figures",
                "- MISCELLANEOUS: Any other significant named entities not covered above",
                "",
                "IMPORTANT OUTPUT FORMAT:",
                "Present your findings in a well-structured markdown format with the following structure:",
                "",
                "# Named Entity Recognition Results",
                "",
                "## Image Summary",
                "Brief description of what you see in the image.",
                "",
                "## Extracted Entities",
                "",
                "### 👤 People",
                "- Entity 1",
                "- Entity 2",
                "",
                "### 🏢 Organizations",
                "- Entity 1",
                "- Entity 2",
                "",
                "### 📍 Locations",
                "- Entity 1",
                "- Entity 2",
                "",
                "### 📦 Products",
                "- Entity 1",
                "- Entity 2",
                "",
                "### 🎉 Events",
                "- Entity 1",
                "- Entity 2",
                "",
                "### 📅 Dates",
                "- Entity 1",
                "- Entity 2",
                "",
                "### 💰 Money/Prices",
                "- Entity 1",
                "- Entity 2",
                "",
                "### 🔖 Miscellaneous",
                "- Entity 1",
                "- Entity 2",
                "",
                "## Confidence Level",
                "**Confidence:** High/Medium/Low",
                "",
                "Guidelines:",
                "- Only include entity sections that you actually find in the image",
                "- Be precise and accurate in your entity extraction",
                "- If text is unclear or partially visible, indicate uncertainty with (unclear) or (?)",
                "- Use clear, readable markdown formatting",
                "- If no entities are found for a category, omit that section entirely",
                "- Focus on text that is clearly readable and identifiable",
                "- Use emojis to make the output more visually appealing"
            ],
            markdown=True,
            show_tool_calls=False,
            debug_mode=False,
        )

    def get_response(self, prompt: str, files: Optional[List[UploadFile]] = None, user_email: Optional[str] = None) -> str:
        """
        Process the image and extract named entities
        
        Args:
            prompt: User's prompt/question about the image
            files: List of uploaded image files
            user_email: User's email (optional)
            
        Returns:
            Markdown formatted string containing extracted named entities
        """
        
        # Check if files are provided
        if not files:
            return """# ❌ Error: No Image Provided

Please upload an image file for named entity recognition.

**Supported formats:** JPEG, PNG, GIF, WebP"""
        
        # Supported image types
        IMAGE_TYPES = {
            'image/jpeg',
            'image/jpg', 
            'image/png',
            'image/gif',
            'image/webp'
        }
        
        IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        
        agno_images = []
        
        # Process uploaded files
        for uploaded_file in files:
            if uploaded_file.filename:
                file_extension = os.path.splitext(uploaded_file.filename.lower())[1]
                content_type = uploaded_file.content_type or ''
                
                # Check if it's an image
                if file_extension in IMAGE_EXTENSIONS or content_type in IMAGE_TYPES:
                    try:
                        # Read image content
                        content = uploaded_file.file.read()
                        
                        # Create Agno Image object
                        agno_images.append(Image(content=content))
                        
                    except Exception as e:
                        return f"""# ❌ Error: File Processing Failed

Failed to process image file **{uploaded_file.filename}**

**Error:** {str(e)}"""
                else:
                    return f"""# ❌ Error: Unsupported File Type

**File:** {uploaded_file.filename}

This file type is not supported. Please upload an image file.

**Supported formats:** JPEG, PNG, GIF, WebP"""
        
        if not agno_images:
            return """# ❌ Error: No Valid Images Found

No valid image files found. Please upload image files in supported formats.

**Supported formats:** JPEG, PNG, GIF, WebP"""
        
        try:
            # Combine user prompt with NER instructions
            ner_prompt = f"""
            Analyze the provided image(s) for named entity recognition.
            
            User request: {prompt}
            
            Please extract all named entities visible in the image and present them in the specified JSON format.
            """
            
            # Run the agent with the image(s)
            response: RunResponse = self.agent.run(
                ner_prompt,
                images=agno_images,
                markdown=True,
            )

            # Return the markdown response directly
            return response.content

        except Exception as e:
            return f"""# ❌ Error: Processing Failed

Failed to process image for named entity recognition.

**Error:** {str(e)}

Please try again with a different image or contact support if the issue persists."""
