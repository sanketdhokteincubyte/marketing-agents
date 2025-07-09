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
        filename = f"fhir_output_{timestamp}.json"
    
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


class MedStandardizerSingleAgent(BaseAgent):
    def __init__(self):
        self.AGENT_STORAGE = settings.AGENT_STORAGE
        print(f"MedStandardizer Single Agent Storage: {self.AGENT_STORAGE}")
        self.med_standardizer_agent = self._create_med_standardizer_agent()

    def _create_med_standardizer_agent(self):
        return Agent(
            name="Medical Data Standardizer Agent",
            role="You are an expert at transforming medical data from various formats into standardized FHIR R4 resources with quality assessment",
            model=Claude(id="claude-3-7-sonnet-20250219", max_tokens=20000),
            tools=[save_fhir_json_file],
            instructions=[
                "Transform uploaded medical data files into standardized FHIR R4 format",
                "Work with the uploaded files directly - they contain the medical data to process",
                
                "Process medical data transformation in these steps:",
                "1. Analyze the uploaded file format (CSV, XML, JSON, plain text)",
                "2. Map medical fields to FHIR R4 standard elements",
                "3. Generate valid FHIR resources (Patient, Observation, MedicationRequest)",
                "4. Assess data quality and calculate confidence scores",
                "5. Save FHIR JSON and create summary report",
                
                "Key capabilities:",
                "- Handle various medical data formats from different EHR/PM systems",
                "- Map field variations: patient_name, PatientName, PATIENT_NM, fname/lname",
                "- Convert date formats to FHIR standard (YYYY-MM-DD)",
                "- Map gender codes: M/F, Male/Female, 1/2 to FHIR values (male, female, other, unknown)",
                "- Standardize medical codes: ICD-10, SNOMED, LOINC, CPT where possible",
                "- Handle unit conversions for lab values and vital signs",
                "- Create Patient resources with demographics and identifiers",
                "- Generate Observation resources for lab results and vital signs",
                "- Create MedicationRequest resources for prescribed medications",
                "- Ensure FHIR R4 compliance with proper resource structure",
                "- Generate unique resource IDs and maintain referential integrity",
                "- Include proper coding systems and meta information",
                "- Save complete FHIR JSON using save_fhir_json_file tool",
                
                "Quality assessment requirements:",
                "- Calculate confidence scores (0-1) for transformation quality",
                "- Assess data completeness and accuracy",
                "- Identify missing values and format inconsistencies",
                "- Validate medical codes against standard terminologies",
                "- Check logical consistency in medical data",
                "- Generate quality metrics: completeness %, accuracy %, compliance %",
                
                "Output requirements:",
                "- Create concise summary under 200 words",
                "- Include transformation confidence score",
                "- List number of records processed and FHIR resources generated",
                "- Highlight any data quality issues or warnings",
                "- Reference the saved FHIR file location",
                "- Format as clean markdown for email delivery",
                "- Focus on actionable insights and recommendations"
            ],
            show_tool_calls=True,
            stream=True,
            markdown=True,
            debug_mode=True,
            storage=SqliteStorage(table_name="med_standardizer_single", db_file=self.AGENT_STORAGE),
        )

    def get_response(self, prompt: str, files: Optional[List[UploadFile]] = None, user_email: Optional[str] = None) -> str:
        # Define supported medical file types
        SUPPORTED_TYPES = {
            'text/csv',
            'application/json',
            'text/xml',
            'application/xml',
            'text/plain'
        }
        
        SUPPORTED_EXTENSIONS = {'.csv', '.json', '.xml', '.txt'}
        
        agno_files = []
        temp_files = []

        if files:
            for uploaded_file in files:
                file_extension = os.path.splitext(uploaded_file.filename or '')[1].lower()
                content_type = uploaded_file.content_type or ''

                if (file_extension in SUPPORTED_EXTENSIONS or content_type in SUPPORTED_TYPES):
                    # Save uploaded file to temporary location
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
            print(f"🚀 Starting Medical Data Standardizer agent with {len(agno_files)} files")
            
            # Simple, clear prompt
            enhanced_prompt = f"""
{prompt}

Transform the uploaded medical data file to FHIR R4 format and provide a quality assessment summary.
"""
            
            response_stream: Iterator[RunResponse] = self.med_standardizer_agent.run(
                enhanced_prompt,
                files=agno_files if agno_files else None,
                markdown=True,
                stream=True,
            )
            
            content = ""
            
            for response in response_stream:
                content += response.content if hasattr(response, 'content') else ""
                        
            pprint_run_response(response, markdown=True)
            print("✅ Medical data standardization completed successfully.")

            # Send email with results if user_email is provided
            if user_email:
                try:
                    self._send_results_email(user_email, content)
                except Exception as email_error:
                    print(f"⚠️ Warning: Failed to send email to {user_email}: {email_error}")
                    # Don't fail the main process if email fails

            return content
            
        except Exception as e:
            print(f"Error running medical data standardizer: {e}")
            return f"# Medical Data Standardization Error: {e}"
    
        finally:
            # Clean up temporary files
            for temp_file_path in temp_files:
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass

    def _send_results_email(self, user_email: str, content: str) -> None:
        """
        Send email with medical data standardization results and FHIR JSON attachment

        Args:
            user_email: Email address to send results to
            content: The generated content/summary from the agent
        """
        print(f"📧 Sending medical data standardization results email to {user_email}")

        # Initialize email service
        email_service = EmailService()

        try:
            # Connect to email service
            email_service.connect()

            # Find the most recent FHIR JSON file
            fhir_file_path = self._find_latest_fhir_file()

            # Create email subject
            subject = "Medical Data Standardization Results - FHIR Transformation Complete"

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
                <h2 style="color: #2c5aa0;">🏥 Medical Data Standardization Results</h2>
                <p>Your medical data has been successfully transformed to FHIR R4 standard format.</p>

                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #2c5aa0;">
                    {html_content}
                </div>

                <h3 style="color: #2c5aa0;">📎 Attachments:</h3>
                <ul>
                    <li><strong>FHIR JSON File:</strong> Contains the complete standardized medical data in FHIR R4 format</li>
                </ul>

                <p style="color: #666; font-size: 12px; margin-top: 30px;">
                    <em>This email was generated automatically by the Medical Data Standardizer Agent.</em>
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
                <h2>🏥 Medical Data Standardization Results</h2>
                <p>Your medical data has been successfully transformed to FHIR R4 standard format.</p>
                <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 10px 0;">
                    {simple_content}
                </div>
                <p><strong>📎 FHIR JSON File attached</strong></p>
                <p><em>This email was generated automatically by the Medical Data Standardizer Agent.</em></p>
            </div>
            """
