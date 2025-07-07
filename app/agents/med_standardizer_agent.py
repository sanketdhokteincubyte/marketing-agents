from typing import Iterator, List, Optional
from agno.agent import Agent, RunResponse
from agno.models.anthropic import Claude
from agno.storage.sqlite import SqliteStorage
from agno.media import File
from agno.tools.file import FileTools
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


@tool(name="save_fhir_json", description="Save FHIR resources to a JSON file")
def save_fhir_json_file(fhir_content: str, filename: str = None) -> str:
    """
    Save FHIR resources to a JSON file for use by subsequent agents.

    Args:
        fhir_content: The FHIR JSON content to save
        filename: Optional filename (will auto-generate if not provided)

    Returns:
        str: Success message with filename
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


class MedStandardizerAgent(BaseAgent):
    def __init__(self):
        self.AGENT_STORAGE = settings.AGENT_STORAGE
        print(self.AGENT_STORAGE)
        self.med_standardizer_team = self._create_med_standardizer_team()

    # Factory methods for creating individual agents
    def create_data_format_detection_agent(self):
        return Agent(
            name="Data Format Detection Agent",
            role="You are an expert at analyzing medical data files and identifying their format, structure, and content type",
            model=Claude(id="claude-3-7-sonnet-20250219", max_tokens=8096),
            instructions=[
                "Analyze uploaded medical data files to determine format (CSV, XML, JSON, plain text)",
                "Identify the structure and schema of the medical data",
                "Detect medical data types: patient demographics, lab results, medications, vital signs, clinical notes",
                "Identify field names, data types, and relationships in the input data",
                "Recognize common medical data patterns and naming conventions",
                "Assess data quality and completeness for transformation readiness",
                "Provide detailed analysis of data structure for downstream processing",
                "Handle various medical data formats from different EHR/PM systems",
                "Identify potential data mapping challenges and transformation requirements",
                "Format output as structured JSON with detected format, fields, and recommendations"
            ],
            show_tool_calls=True,
            stream=True,
            markdown=True,
            debug_mode=True,
        )

    def create_medical_field_mapping_agent(self):
        return Agent(
            name="Medical Field Mapping Agent",
            role="You are an expert at mapping various medical field names and formats to standardized FHIR field mappings",
            model=Claude(id="claude-3-7-sonnet-20250219", max_tokens=8096),
            instructions=[
                "Map medical field names from various formats to FHIR R4 standard field names",
                "Handle common variations: patient_name, PatientName, PATIENT_NM, fname/lname combinations",
                "Convert date formats to FHIR standard (YYYY-MM-DD)",
                "Map gender codes: M/F, Male/Female, 1/2 to FHIR gender values (male, female, other, unknown)",
                "Standardize medical codes: ICD-10, SNOMED, LOINC, CPT mappings where possible",
                "Handle unit conversions for lab values and vital signs",
                "Map medication formats to FHIR MedicationRequest structure",
                "Create field mapping dictionary for FHIR resource generation",
                "Identify unmappable fields and suggest manual review",
                "Provide confidence scores for each field mapping (0-1 scale)",
                "Handle nested data structures and complex medical records",
                "Support batch processing of multiple records with consistent mapping"
            ],
            show_tool_calls=True,
            stream=True,
            markdown=True,
            debug_mode=True,
        )

    def create_fhir_resource_generation_agent(self):
        return Agent(
            name="FHIR Resource Generation Agent",
            role="You are an expert at generating valid FHIR R4 Patient, Observation, and MedicationRequest resources from mapped medical data",
            model=Claude(id="claude-3-7-sonnet-20250219", max_tokens=8096),
            tools=[save_fhir_json_file],
            instructions=[
                "Generate valid FHIR R4 compliant JSON resources from mapped medical data",
                "Create Patient resources with demographics, identifiers, and contact information",
                "Generate Observation resources for lab results, vital signs, and clinical measurements",
                "Create MedicationRequest resources for prescribed medications with dosage and frequency",
                "Ensure all required FHIR fields are populated with appropriate values",
                "Generate unique resource IDs and maintain referential integrity between resources",
                "Include proper FHIR meta information, resource types, and status fields",
                "Handle missing data gracefully with appropriate FHIR null/unknown values",
                "Validate resource structure against FHIR R4 specification",
                "Support multiple resource types in a single transformation",
                "Include proper coding systems (LOINC, SNOMED, ICD-10) where applicable",
                "Generate Bundle resources when multiple related resources are created",
                "Ensure FHIR compliance for interoperability with healthcare systems",
                "IMPORTANT: After generating FHIR resources, ALWAYS save them to a file using the save_fhir_json tool",
                "Use the save_fhir_json tool to save the complete FHIR JSON output for subsequent agents to review",
                "The saved file will be used by the Data Quality Assessment Agent to avoid output truncation issues"
            ],
            show_tool_calls=True,
            stream=True,
            markdown=True,
            debug_mode=True,
        )

    def create_data_quality_assessment_agent(self):
        return Agent(
            name="Data Quality Assessment Agent",
            role="You are an expert at validating FHIR output, calculating confidence scores, and identifying data quality issues",
            model=Claude(id="claude-3-7-sonnet-20250219", max_tokens=8096),
            tools=[FileTools(Path(FHIR_OUTPUT_DIR))],
            instructions=[
                "Validate generated FHIR resources against FHIR R4 specification",
                "Calculate confidence scores (0-1) for data transformation quality",
                "Assess completeness of required vs optional FHIR fields",
                "Identify potential data quality issues: missing values, format inconsistencies, invalid codes",
                "Validate medical codes against standard terminologies (LOINC, SNOMED, ICD-10)",
                "Check for logical consistency in medical data (e.g., age vs birth date)",
                "Assess data accuracy and clinical plausibility",
                "Flag potential privacy/security concerns in the data",
                "Generate quality metrics: completeness %, accuracy %, compliance %",
                "Provide recommendations for data quality improvement",
                "Create detailed quality assessment report with specific issues identified",
                "Score individual fields and overall transformation confidence",
                "Identify fields requiring manual review or validation",
                "IMPORTANT: Look for and read the FHIR JSON file saved by the previous agent",
                "Use the read_file tool to access the complete FHIR resources for thorough analysis",
                "The FHIR file will be in the tmp/fhir_output directory with a timestamp in the filename"
            ],
            show_tool_calls=True,
            stream=True,
            markdown=True,
            debug_mode=True,
        )

    def create_output_formatting_agent(self):
        return Agent(
            name="Output Formatting Agent",
            role="You are an expert at creating concise summary reports since the detailed FHIR JSON is saved as a file attachment",
            model=Claude(id="claude-3-7-sonnet-20250219", max_tokens=4096),
            tools=[FileTools(Path(FHIR_OUTPUT_DIR))],
            instructions=[
                "Create a CONCISE summary report since the full FHIR JSON is saved as a file",
                "DO NOT include the full FHIR resources in your output - they are in the saved file",
                "Provide a brief executive summary with key metrics:",
                "- Overall transformation confidence score (0-1)",
                "- Number of records processed",
                "- Number of FHIR resources generated (Patients, Observations, MedicationRequests)",
                "- Key data quality indicators (completeness %, accuracy %)",
                "- Critical issues or warnings (if any)",
                "- File location of the complete FHIR JSON output",
                "Keep the summary under 500 words - focus on actionable insights",
                "Format as a clean, readable markdown report",
                "Reference the saved FHIR file location for detailed review"
            ],
            show_tool_calls=True,
            stream=True,
            markdown=True,
            debug_mode=True,
        )

    def _create_med_standardizer_team(self):
        return Agent(
            name="MedStandardizer Pro Team",
            team=[
                self.create_data_format_detection_agent(),
                self.create_medical_field_mapping_agent(),
                self.create_fhir_resource_generation_agent(),
                self.create_data_quality_assessment_agent(),
                self.create_output_formatting_agent()
            ],
            model=Claude(id="claude-3-7-sonnet-20250219", max_tokens=12000),
            instructions=[
                "You are MedStandardizer Pro, an AI-powered medical data transformation system",
                "Transform heterogeneous medical data formats into standardized FHIR R4 resources",
                "Process the workflow in this order:",
                "1. Data Format Detection: Analyze input files and identify structure",
                "2. Medical Field Mapping: Map fields to FHIR standards with confidence scores",
                "3. FHIR Resource Generation: Create valid FHIR R4 resources",
                "4. Data Quality Assessment: Validate output and calculate confidence scores",
                "5. Output Formatting: Format final JSON response with metadata",
                "Handle CSV, XML, JSON, and clinical text input formats",
                "Support Patient, Observation, and MedicationRequest FHIR resources",
                "Provide confidence scores (0-1) for transformation quality",
                "Include processing metadata and quality assessment in output",
                "Ensure FHIR R4 compliance for healthcare interoperability",
            ],
            show_tool_calls=True,
            stream=True,
            markdown=True,
            debug_mode=True,
            storage=SqliteStorage(table_name="medical_data_standardizer_team", db_file=self.AGENT_STORAGE),
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

                    # Create Agno File object
                    agno_files.append(File(filepath=temp_file_path))
                else:
                    print(f"Skipping unsupported file: {uploaded_file.filename} (type: {content_type})")
                    continue
            
        try:
            print(f"🚀 Starting MedStandardizer team with {len(agno_files)} files")
            
            response_stream: Iterator[RunResponse] = self.med_standardizer_team.run(
                prompt,
                files=agno_files if agno_files else None,
                markdown=True,
                stream=True,
            )
            
            content = ""
            
            for response in response_stream:
                content += response.content if hasattr(response, 'content') else ""
                        
            pprint_run_response(response, markdown=True)
            print("✅ Medical Data Standardizer team analysis completed successfully.")

            # Send email with results if user_email is provided
            if user_email:
                try:
                    self._send_results_email(user_email, content)
                except Exception as email_error:
                    print(f"⚠️ Warning: Failed to send email to {user_email}: {email_error}")
                    # Don't fail the main process if email fails

            return content
            
        except Exception as e:
            print(f"Error running medical data standardizer team: {e}")
            return f"# Medical Data Standardizer Error: {e}"
    
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
        print(f"📧 Sending results email to {user_email}")

        # Initialize email service
        email_service = EmailService()

        try:
            # Connect to email service
            email_service.connect()

            # Find the most recent FHIR JSON file
            fhir_file_path = self._find_latest_fhir_file()

            # Create email subject
            subject = "Medical Data Standardization Results - FHIR Conversion Complete"

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
            Path to the latest FHIR file or None if no files found
        """
        fhir_pattern = os.path.join(FHIR_OUTPUT_DIR, "*.json")
        fhir_files = glob.glob(fhir_pattern)

        if not fhir_files:
            print("⚠️ No FHIR JSON files found in output directory")
            return None

        # Get the most recent file by modification time
        latest_file = max(fhir_files, key=os.path.getmtime)
        print(f"📄 Found latest FHIR file: {latest_file}")
        return latest_file

    def _create_email_body(self, content: str) -> str:
        """
        Create HTML email body by converting markdown content to HTML

        Args:
            content: The markdown content from the agent

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

                <hr style="margin: 30px 0; border: none; border-top: 1px solid #dee2e6;">
                <p style="font-size: 12px; color: #6c757d; text-align: center;">
                    <em>This email was generated automatically by MedStandardizer Pro.</em><br>
                    For questions about this transformation, please contact your system administrator.
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
                <p><em>This email was generated automatically by MedStandardizer Pro.</em></p>
            </div>
            """
