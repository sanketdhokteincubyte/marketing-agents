from typing import Iterator, List, Optional
from agno.agent import Agent, RunResponse
from agno.models.anthropic import Claude
from agno.storage.sqlite import SqliteStorage
from agno.media import File

from agno.tools import tool
from app.agents.base_agent import BaseAgent
from app.core import settings
from agno.utils.pprint import pprint_run_response
from fastapi import UploadFile
import tempfile
import os
import json
import glob
from pathlib import Path
from datetime import datetime
from app.service.email_service import EmailService
import markdown

# Constants
FHIR_OUTPUT_DIR = "tmp/fhir_output"

@tool
def save_fhir_json_file(fhir_content: str, filename: str = None) -> str:
    """
    Save FHIR resources as a JSON file in the output directory.
    
    Args:
        fhir_content: The FHIR JSON content as a string
        filename: Optional filename. If not provided, generates timestamp-based name
    
    Returns:
        Success message with file path
    """
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"hl7_to_fhir_conversion_{timestamp}.json"
    
    # Ensure the output directory exists
    output_dir = Path(FHIR_OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = output_dir / filename
    
    try:
        # Try to parse and validate JSON
        parsed_json = json.loads(fhir_content)
        
        # Save the formatted JSON
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(parsed_json, f, indent=2, ensure_ascii=False)
        
        return f"✅ FHIR resources successfully saved to: {file_path}"
    
    except json.JSONDecodeError:
        # If not valid JSON, save as text with .json extension for review
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fhir_content)
        
        return f"⚠️ Content saved to {file_path} (not valid JSON - please review)"
    
    except Exception as e:
        return f"❌ Error saving FHIR file: {e}"


class HL7ToFHIRAgent(BaseAgent):
    def __init__(self):
        self.AGENT_STORAGE = settings.AGENT_STORAGE
        print(f"HL7ToFHIR Agent Storage: {self.AGENT_STORAGE}")
        self.hl7_to_fhir_agent = self._create_hl7_to_fhir_agent()

    # Single agent approach for better file handling and performance
    def _create_hl7_to_fhir_agent(self):
        return Agent(
            name="HL7 to FHIR Transformation Agent",
            role="You are an expert at complete HL7 to FHIR transformation, handling parsing, mapping, FHIR resource generation, quality assessment, and summary reporting",
            model=Claude(id="claude-3-7-sonnet-20250219", max_tokens=20000),
            tools=[save_fhir_json_file],
            instructions=[
                "Process the uploaded HL7 files to transform them to FHIR R4 format",
                "The HL7 content is provided in the uploaded files - work with them directly",

                "Transform HL7 messages to FHIR R4 format following these steps:",
                "1. Parse the HL7 message segments (MSH, PID, OBX, ORC, OBR, etc.)",
                "2. Map HL7 data to FHIR resources (Patient, Observation, ServiceRequest, MessageHeader)",
                "3. Generate valid FHIR R4 JSON with proper structure and references",
                "4. Save the FHIR JSON using the save_fhir_json_file tool",
                "5. Create a brief summary report with transformation results",

                "Key requirements:",
                "- Use HL7 field separators (|) and component separators (^) correctly",
                "- Create FHIR Bundle containing all resources",
                "- Include confidence scores and quality assessment",
                "- Keep summary under 200 words",
                "- Format output as markdown for email delivery"
            ],
            show_tool_calls=True,
            stream=True,
            markdown=True,
            debug_mode=True,
            storage=SqliteStorage(table_name="hl7_to_fhir_agent", db_file=self.AGENT_STORAGE),
        )

    def get_response(self, prompt: str, files: Optional[List[UploadFile]] = None, user_email: Optional[str] = None) -> str:
        # Define supported HL7 file types
        SUPPORTED_TYPES = {
            'text/plain',
            'application/octet-stream',  # Sometimes HL7 files are detected as this
        }

        # Supported file extensions for HL7
        HL7_EXTENSIONS = {'.hl7', '.txt', '.dat', '.msg'}

        agno_files = []
        temp_files = []

        if files:
            for uploaded_file in files:
                content_type = uploaded_file.content_type
                file_extension = os.path.splitext(uploaded_file.filename)[1].lower()

                print(f"Processing file: {uploaded_file.filename} (type: {content_type}, ext: {file_extension})")

                # Check if it's a supported HL7 file type
                if content_type in SUPPORTED_TYPES or file_extension in HL7_EXTENSIONS:
                    # Create temporary file (match MedStandardizerAgent pattern)
                    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                        content = uploaded_file.file.read()
                        temp_file.write(content)
                        temp_file_path = temp_file.name
                        temp_files.append(temp_file_path)

                    print(f"✅ Created temp file: {temp_file_path} (size: {len(content)} bytes)")

                    # Create Agno File object
                    agno_files.append(File(filepath=temp_file_path))
                else:
                    print(f"Skipping unsupported file: {uploaded_file.filename} (type: {content_type})")

        try:
            print(f"🚀 Starting HL7 to FHIR transformation agent with {len(agno_files)} files")

            # Simple, clear prompt
            enhanced_prompt = f"""
{prompt}

Transform the uploaded HL7 file to FHIR R4 format and provide a summary.
"""

            response_stream: Iterator[RunResponse] = self.hl7_to_fhir_agent.run(
                enhanced_prompt,
                files=agno_files if agno_files else None,
                markdown=True,
                stream=True,
            )

            content = ""

            for response in response_stream:
                content += response.content if hasattr(response, 'content') else ""

            pprint_run_response(response, markdown=True)
            print("✅ HL7 to FHIR transformation team analysis completed successfully.")

            # Send email with results if user_email is provided
            if user_email:
                try:
                    self._send_results_email(user_email, content)
                except Exception as email_error:
                    print(f"⚠️ Warning: Failed to send email to {user_email}: {email_error}")
                    # Don't fail the main process if email fails

            return content

        except Exception as e:
            print(f"Error running HL7 to FHIR transformation team: {e}")
            return f"# HL7 to FHIR Transformation Error: {e}"

        finally:
            # Clean up temporary files
            for temp_file_path in temp_files:
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass

    def _send_results_email(self, user_email: str, content: str) -> None:
        """
        Send email with HL7 to FHIR transformation results and FHIR JSON attachment

        Args:
            user_email: Email address to send results to
            content: The generated content/summary from the agent
        """
        print(f"📧 Sending HL7 to FHIR results email to {user_email}")

        # Initialize email service
        email_service = EmailService()

        try:
            # Connect to email service
            email_service.connect()

            # Find the most recent FHIR JSON file
            fhir_file_path = self._find_latest_fhir_file()

            # Create email subject
            subject = "HL7 to FHIR Transformation Results - Conversion Complete"

            # Create email body with summary
            email_body = self._create_email_body(content)

            # Send email with FHIR file attachment
            email_service.send_email(
                to_email=user_email,
                subject=subject,
                body=email_body,
                pdf_path=fhir_file_path  # EmailService can handle JSON files as attachments
            )

            print(f"✅ Email sent successfully to {user_email}")

        finally:
            # Always disconnect from email service
            email_service.disconnect()

    def _find_latest_fhir_file(self) -> Optional[str]:
        """
        Find the most recently created FHIR JSON file in the output directory

        Returns:
            Path to the latest FHIR file, or None if no files found
        """
        try:
            # Look for JSON files in the FHIR output directory
            pattern = os.path.join(FHIR_OUTPUT_DIR, "*.json")
            fhir_files = glob.glob(pattern)

            if not fhir_files:
                print("⚠️ No FHIR JSON files found in output directory")
                return None

            # Get the most recently modified file
            latest_file = max(fhir_files, key=os.path.getmtime)
            print(f"📄 Found latest FHIR file: {latest_file}")
            return latest_file

        except Exception as e:
            print(f"⚠️ Error finding FHIR file: {e}")
            return None

    def _create_email_body(self, content: str) -> str:
        """
        Create HTML email body from markdown content

        Args:
            content: Markdown content from the agent

        Returns:
            HTML formatted email body
        """
        try:
            # Convert markdown content to HTML
            html_content = markdown.markdown(
                content,
                extensions=['tables', 'fenced_code', 'nl2br']
            )

            # Wrap in a nice email template
            email_body = f"""
            <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
                <h2 style="color: #2c5aa0;">🔄 HL7 to FHIR Transformation Results</h2>
                <p>Your HL7 message has been successfully transformed to FHIR R4 standard format.</p>

                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #2c5aa0;">
                    {html_content}
                </div>

                <h3 style="color: #2c5aa0;">📎 Attachments:</h3>
                <ul>
                    <li><strong>FHIR JSON File:</strong> Contains the complete transformed medical data in FHIR R4 format</li>
                </ul>

                <p style="color: #666; font-size: 12px; margin-top: 30px;">
                    <em>This email was generated automatically by the HL7 to FHIR Transformation Agent.</em>
                </p>
            </div>
            """

            return email_body

        except Exception as e:
            # Fallback to simple HTML if markdown conversion fails
            print(f"⚠️ Warning: Markdown conversion failed: {e}")

            # Simple HTML fallback
            simple_content = content.replace('\n', '<br>')
            return f"""
            <div style="font-family: Arial, sans-serif;">
                <h2>🔄 HL7 to FHIR Transformation Results</h2>
                <p>Your HL7 message has been successfully transformed to FHIR R4 standard format.</p>
                <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 10px 0;">
                    {simple_content}
                </div>
                <p><strong>📎 FHIR JSON File attached</strong></p>
                <p><em>This email was generated automatically by the HL7 to FHIR Transformation Agent.</em></p>
            </div>
            """
