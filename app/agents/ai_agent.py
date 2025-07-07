from agno.agent import Agent, RunResponse
from agno.models.anthropic import Claude
from agno.tools.reasoning import ReasoningTools
from agno.tools.yfinance import YFinanceTools
from agno.media import File, Image
from app.agents.base_agent import BaseAgent
from app.core import settings
from typing import List, Optional
from fastapi import UploadFile
import tempfile
import os


tools=[
        ReasoningTools(add_instructions=True),
        YFinanceTools(
            stock_price=True,
            analyst_recommendations=True,
            company_info=True,
            company_news=True,
        ),
    ]
instructions=[
    "Only output the report, no other text",
]

class AIAgent(BaseAgent):
    def __init__(self, model_id='claude-3-7-sonnet-latest', tools=tools, instructions=instructions, markdown=True):
        self.agent = Agent(
            model=Claude(id=model_id, api_key=settings.ANTHROPIC_API_KEY,),
            tools=tools,
            instructions=instructions,
            markdown=markdown,
        )

    def get_response(self, prompt: str, files: Optional[List[UploadFile]] = None, user_email: Optional[str] = None):
        # Define supported file types for Anthropic Claude
        DOCUMENT_TYPES = {
            'application/pdf',
            'text/plain',
            'text/csv',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
            'application/json'
        }

        IMAGE_TYPES = {
            'image/jpeg',
            'image/jpg',
            'image/png',
            'image/gif',
            'image/webp'
        }

        DOCUMENT_EXTENSIONS = {'.pdf', '.txt', '.csv', '.docx', '.json'}
        IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}

        # Separate files into documents and images
        agno_files = []
        agno_images = []
        temp_files = []  # Track temp files for cleanup

        if files:
            for uploaded_file in files:
                # Check file type
                file_extension = os.path.splitext(uploaded_file.filename or '')[1].lower()
                content_type = uploaded_file.content_type or ''

                # Check if it's a document
                if (file_extension in DOCUMENT_EXTENSIONS or content_type in DOCUMENT_TYPES):
                    # Save uploaded file to temporary location
                    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                        content = uploaded_file.file.read()
                        temp_file.write(content)
                        temp_file_path = temp_file.name
                        temp_files.append(temp_file_path)

                    # Create Agno File object
                    agno_files.append(File(filepath=temp_file_path))

                # Check if it's an image
                elif (file_extension in IMAGE_EXTENSIONS or content_type in IMAGE_TYPES):
                    # Read image content
                    content = uploaded_file.file.read()

                    # Create Agno Image object
                    agno_images.append(Image(content=content))

                else:
                    print(f"Skipping unsupported file: {uploaded_file.filename} (type: {content_type})")
                    continue

        try:
            # Run the agent with prompt, files, and images
            response: RunResponse = self.agent.run(
                prompt,
                files=agno_files if agno_files else None,
                images=agno_images if agno_images else None,
                markdown=self.agent.markdown,
            )

            return response.content

        finally:
            # Clean up temporary files
            for temp_file_path in temp_files:
                try:
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
                except Exception as e:
                    print(f"Warning: Could not delete temp file {temp_file_path}: {e}")


