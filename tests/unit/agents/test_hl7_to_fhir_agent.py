import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import UploadFile
import tempfile
import os
from io import BytesIO

from app.agents.hl7_to_fhir_agent import HL7ToFHIRAgent


class TestHL7ToFHIRAgent:
    def setup_method(self):
        """Setup method run before each test"""
        with patch('app.agents.hl7_to_fhir_agent.settings') as mock_settings:
            mock_settings.AGENT_STORAGE = "test_storage.db"
            self.agent = HL7ToFHIRAgent()

    def test_init(self):
        """Test that HL7ToFHIRAgent initializes correctly"""
        assert self.agent is not None
        assert hasattr(self.agent, 'hl7_to_fhir_agent')
        assert hasattr(self.agent, 'AGENT_STORAGE')

    def test_create_hl7_to_fhir_agent(self):
        """Test creation of single HL7 to FHIR agent"""
        agent = self.agent._create_hl7_to_fhir_agent()
        assert agent is not None
        assert agent.name == "HL7 to FHIR Transformation Agent"
        assert "complete HL7 to FHIR transformation" in agent.role

    @patch('app.agents.hl7_to_fhir_agent.EmailService')
    @patch('app.agents.hl7_to_fhir_agent.os.unlink')
    @patch('app.agents.hl7_to_fhir_agent.pprint_run_response')
    def test_get_response_with_hl7_file(self, mock_pprint, mock_unlink, mock_email_service):
        """Test get_response with HL7 file"""
        # Create mock HL7 file content
        hl7_content = """MSH|^~\\&|LAB|HOSPITAL|EMR|CLINIC|20240115143000||ORU^R01|MSG001|P|2.5
PID|1||12345^^^HOSPITAL^MR||SMITH^JOHN^MICHAEL||19850315|M|||123 MAIN ST^^CHICAGO^IL^60601^USA||(555)123-4567|EN|M|CHR|123456789|||||||||||20240115
OBR|1|ORD001|LAB001|CBC^COMPLETE BLOOD COUNT^L|||20240115140000|||||||||DOC001^JOHNSON^MARY^MD||||||||F
OBX|1|NM|WBC^WHITE BLOOD CELL COUNT^L|1|7.5|10*3/uL|4.0-11.0|N|||F"""

        # Create mock UploadFile
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.hl7"
        mock_file.content_type = "text/plain"
        mock_file.file = BytesIO(hl7_content.encode())

        # Mock the team run method to return an iterator
        def mock_run_generator():
            mock_response = Mock()
            mock_response.content = "# HL7 to FHIR Transformation Complete\n\nSuccessfully transformed HL7 message to FHIR format."
            yield mock_response

        with patch.object(self.agent.hl7_to_fhir_agent, 'run') as mock_run:
            mock_run.return_value = mock_run_generator()

            # Test the response
            result = self.agent.get_response(
                prompt="Transform this HL7 message to FHIR format",
                files=[mock_file],
                user_email="test@example.com"
            )

            assert "HL7 to FHIR Transformation Complete" in result
            mock_run.assert_called_once()

    @patch('app.agents.hl7_to_fhir_agent.pprint_run_response')
    def test_get_response_unsupported_file_type(self, mock_pprint):
        """Test get_response with unsupported file type"""
        # Create mock file with unsupported type
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.file = BytesIO(b"fake pdf content")

        # Mock the team run method to return an iterator
        mock_response = Mock()
        mock_response.content = "No files to process"

        with patch.object(self.agent.hl7_to_fhir_agent, 'run') as mock_run:
            # Return a generator that yields the mock response
            mock_run.return_value = (r for r in [mock_response])

            # Test the response
            result = self.agent.get_response(
                prompt="Transform this file",
                files=[mock_file]
            )

            # Should process with no files since PDF is not supported
            assert "No files to process" in result
            mock_run.assert_called_once()

    @patch('app.agents.hl7_to_fhir_agent.pprint_run_response')
    def test_get_response_no_files(self, mock_pprint):
        """Test get_response with no files"""
        # Mock the team run method to return an iterator
        mock_response = Mock()
        mock_response.content = "Please provide an HL7 file to transform"

        with patch.object(self.agent.hl7_to_fhir_agent, 'run') as mock_run:
            # Return a generator that yields the mock response
            mock_run.return_value = (r for r in [mock_response])

            # Test the response
            result = self.agent.get_response(
                prompt="Transform HL7 to FHIR",
                files=None
            )

            assert "Please provide an HL7 file" in result
            mock_run.assert_called_once()

    @patch('app.agents.hl7_to_fhir_agent.glob.glob')
    def test_find_latest_fhir_file(self, mock_glob):
        """Test finding the latest FHIR file"""
        # Mock glob to return some files
        mock_files = [
            "tmp/fhir_output/file1.json",
            "tmp/fhir_output/file2.json"
        ]
        mock_glob.return_value = mock_files
        
        with patch('app.agents.hl7_to_fhir_agent.os.path.getmtime') as mock_getmtime:
            # Make file2 newer
            mock_getmtime.side_effect = lambda x: 2 if "file2" in x else 1
            
            result = self.agent._find_latest_fhir_file()
            assert result == "tmp/fhir_output/file2.json"

    @patch('app.agents.hl7_to_fhir_agent.glob.glob')
    def test_find_latest_fhir_file_no_files(self, mock_glob):
        """Test finding latest FHIR file when none exist"""
        mock_glob.return_value = []
        
        result = self.agent._find_latest_fhir_file()
        assert result is None

    @patch('app.agents.hl7_to_fhir_agent.markdown.markdown')
    def test_create_email_body(self, mock_markdown):
        """Test creating email body from markdown content"""
        mock_markdown.return_value = "<h1>Test Content</h1>"
        
        content = "# Test Content"
        result = self.agent._create_email_body(content)
        
        assert "HL7 to FHIR Transformation Results" in result
        assert "<h1>Test Content</h1>" in result
        assert "FHIR JSON File" in result

    def test_create_email_body_markdown_error(self):
        """Test creating email body when markdown conversion fails"""
        with patch('app.agents.hl7_to_fhir_agent.markdown.markdown') as mock_markdown:
            mock_markdown.side_effect = Exception("Markdown error")
            
            content = "Test content with\nnewlines"
            result = self.agent._create_email_body(content)
            
            # Should fall back to simple HTML
            assert "HL7 to FHIR Transformation Results" in result
            assert "Test content with<br>newlines" in result
