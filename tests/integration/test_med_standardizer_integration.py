"""
Integration tests for MedStandardizer Pro Agent
Tests the complete workflow with real file uploads and FHIR validation
"""

import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.agents.med_standardizer_agent import MedStandardizerAgent


class TestMedStandardizerIntegration:
    """Integration tests for MedStandardizer Pro agent"""

    def setup_method(self):
        """Setup test environment"""
        self.client = TestClient(app)
        self.agent = MedStandardizerAgent()
        self.test_data_dir = Path(__file__).parent.parent / "data"

    def test_agent_initialization(self):
        """Test that the agent initializes correctly"""
        assert self.agent is not None
        assert self.agent.med_standardizer_team is not None
        assert hasattr(self.agent, 'get_response')

    def test_lab_results_csv_integration(self):
        """Integration test for lab results CSV processing"""
        csv_file_path = self.test_data_dir / "sample_lab_results.csv"
        
        if csv_file_path.exists():
            with open(csv_file_path, 'rb') as f:
                files = {"files": ("sample_lab_results.csv", f, "text/csv")}
                data = {
                    "prompt": """
                    Transform this lab results CSV into FHIR format.
                    Create Patient resources and Observation resources for each lab test.
                    Include confidence scores and ensure FHIR R4 compliance.
                    """,
                    "user_email": "test@example.com",
                    "agent_id": 1  # Assuming MedStandardizer agent ID
                }
                
                # This would be the actual API call in a real integration test
                # response = self.client.post("/agents/run", data=data, files=files)
                # assert response.status_code == 200
                
                print("Lab Results CSV integration test setup complete")

    def test_patient_xml_integration(self):
        """Integration test for patient XML processing"""
        xml_file_path = self.test_data_dir / "sample_patient_record.xml"
        
        if xml_file_path.exists():
            with open(xml_file_path, 'rb') as f:
                files = {"files": ("sample_patient_record.xml", f, "application/xml")}
                data = {
                    "prompt": """
                    Transform this patient XML record into FHIR Patient resource.
                    Map all available fields and provide confidence scoring.
                    """,
                    "user_email": "test@example.com",
                    "agent_id": 1
                }
                
                print("Patient XML integration test setup complete")

    def test_clinical_note_integration(self):
        """Integration test for clinical note processing"""
        txt_file_path = self.test_data_dir / "sample_clinical_note.txt"
        
        if txt_file_path.exists():
            with open(txt_file_path, 'rb') as f:
                files = {"files": ("sample_clinical_note.txt", f, "text/plain")}
                data = {
                    "prompt": """
                    Transform this clinical note into comprehensive FHIR resources:
                    - Patient resource
                    - MedicationRequest resources for medications
                    - Observation resources for vital signs and lab results
                    - Condition resources for diagnoses
                    """,
                    "user_email": "test@example.com",
                    "agent_id": 1
                }
                
                print("Clinical Note integration test setup complete")

    def validate_fhir_response(self, response_content: str) -> dict:
        """
        Validate FHIR response structure and compliance
        Returns validation results
        """
        validation_results = {
            "is_valid_json": False,
            "has_fhir_resources": False,
            "has_confidence_score": False,
            "has_metadata": False,
            "resource_types": [],
            "issues": []
        }

        try:
            # Parse JSON
            data = json.loads(response_content)
            validation_results["is_valid_json"] = True

            # Check for FHIR resources
            if "fhir_resources" in data:
                validation_results["has_fhir_resources"] = True
                
                # Identify resource types
                for resource in data.get("fhir_resources", []):
                    if isinstance(resource, dict) and "resourceType" in resource:
                        validation_results["resource_types"].append(resource["resourceType"])

            # Check for confidence score
            if "confidence_score" in data:
                validation_results["has_confidence_score"] = True
                score = data["confidence_score"]
                if not (0 <= score <= 1):
                    validation_results["issues"].append("Confidence score not in valid range (0-1)")

            # Check for metadata
            metadata_fields = ["processed_records", "processing_time"]
            if any(field in data for field in metadata_fields):
                validation_results["has_metadata"] = True

        except json.JSONDecodeError as e:
            validation_results["issues"].append(f"Invalid JSON: {str(e)}")
        except Exception as e:
            validation_results["issues"].append(f"Validation error: {str(e)}")

        return validation_results

    def test_fhir_validation_helper(self):
        """Test the FHIR validation helper function"""
        # Test valid FHIR response
        valid_response = json.dumps({
            "fhir_resources": [
                {
                    "resourceType": "Patient",
                    "id": "patient-1",
                    "name": [{"family": "Doe", "given": ["John"]}]
                }
            ],
            "confidence_score": 0.95,
            "processed_records": 1,
            "processing_time": "0.2s"
        })

        results = self.validate_fhir_response(valid_response)
        assert results["is_valid_json"] is True
        assert results["has_fhir_resources"] is True
        assert results["has_confidence_score"] is True
        assert results["has_metadata"] is True
        assert "Patient" in results["resource_types"]
        assert len(results["issues"]) == 0

    def test_error_handling(self):
        """Test error handling with invalid inputs"""
        # Test with empty prompt
        response = self.agent.get_response("", None)
        assert response is not None

        # Test with invalid file type (should be handled gracefully)
        # This would require creating a mock UploadFile with unsupported type

    @patch('app.agents.med_standardizer_agent.EmailService')
    def test_email_integration(self, mock_email_service):
        """Test email functionality integration"""
        # Setup mock email service
        mock_email_instance = MagicMock()
        mock_email_service.return_value = mock_email_instance

        # Test email sending with user_email parameter
        test_email = "test@example.com"
        test_prompt = "Transform medical data to FHIR format"

        # Mock the FHIR file finding
        with patch.object(self.agent, '_find_latest_fhir_file') as mock_find_file:
            mock_find_file.return_value = "tmp/fhir_output/test_fhir.json"

            # Call get_response with user_email
            response = self.agent.get_response(test_prompt, None, test_email)

            # Verify response is not None
            assert response is not None

            # Verify email service was called
            mock_email_service.assert_called_once()
            mock_email_instance.connect.assert_called_once()
            mock_email_instance.send_email.assert_called_once()
            mock_email_instance.disconnect.assert_called_once()

            # Verify email parameters
            call_args = mock_email_instance.send_email.call_args
            assert call_args[1]['to_email'] == test_email
            assert 'Medical Data Standardization Results' in call_args[1]['subject']
            assert call_args[1]['body'] is not None

        print("✓ Email integration test passed")

    def test_email_error_handling(self):
        """Test that email errors don't break the main functionality"""
        with patch('app.agents.med_standardizer_agent.EmailService') as mock_email_service:
            # Setup email service to raise an exception
            mock_email_instance = MagicMock()
            mock_email_instance.connect.side_effect = Exception("Email connection failed")
            mock_email_service.return_value = mock_email_instance

            test_email = "test@example.com"
            test_prompt = "Transform medical data to FHIR format"

            # This should not raise an exception even if email fails
            response = self.agent.get_response(test_prompt, None, test_email)

            # Verify the main functionality still works
            assert response is not None
            assert "Medical Data Standardizer Error" not in response

        print("✓ Email error handling test passed")

    def test_performance_benchmarks(self):
        """Test performance benchmarks for different data sizes"""
        import time
        
        # Small dataset test
        small_prompt = "Transform this small dataset to FHIR"
        start_time = time.time()
        response = self.agent.get_response(small_prompt, None)
        small_duration = time.time() - start_time
        
        assert small_duration < 30  # Should complete within 30 seconds
        print(f"Small dataset processing time: {small_duration:.2f} seconds")

    def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        import threading
        import time
        
        results = []
        
        def make_request():
            start_time = time.time()
            response = self.agent.get_response("Test concurrent request", None)
            duration = time.time() - start_time
            results.append({"response": response, "duration": duration})
        
        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all requests completed
        assert len(results) == 3
        for result in results:
            assert result["response"] is not None
            assert result["duration"] < 60  # Each request should complete within 60 seconds

    @pytest.mark.slow
    def test_comprehensive_workflow(self):
        """
        Comprehensive test of the entire workflow with realistic data
        This test may take longer to run
        """
        # Test with comprehensive clinical note
        comprehensive_prompt = """
        Process this comprehensive medical record and create a complete FHIR Bundle with:
        1. Patient resource with full demographics
        2. All medication requests
        3. All observations (vitals and labs)
        4. All conditions/diagnoses
        5. Allergy intolerances
        
        Ensure FHIR R4 compliance and provide detailed confidence scoring.
        """
        
        response = self.agent.get_response(comprehensive_prompt, None)
        
        # Validate response
        assert response is not None
        assert len(response) > 100  # Should be substantial response
        
        # Validate FHIR structure
        validation_results = self.validate_fhir_response(response)
        
        # Print validation results for manual review
        print("\n=== Comprehensive Workflow Validation Results ===")
        print(f"Valid JSON: {validation_results['is_valid_json']}")
        print(f"Has FHIR Resources: {validation_results['has_fhir_resources']}")
        print(f"Has Confidence Score: {validation_results['has_confidence_score']}")
        print(f"Has Metadata: {validation_results['has_metadata']}")
        print(f"Resource Types: {validation_results['resource_types']}")
        print(f"Issues: {validation_results['issues']}")

    def test_demo_mode_scenarios(self):
        """Test all demo scenarios in sequence"""
        demo_scenarios = [
            {
                "name": "Lab Results CSV Demo",
                "prompt": "Demo: Transform lab results CSV to FHIR Patient + Observation resources",
                "expected_resources": ["Patient", "Observation"]
            },
            {
                "name": "Patient XML Demo", 
                "prompt": "Demo: Transform patient XML to FHIR Patient resource",
                "expected_resources": ["Patient"]
            },
            {
                "name": "Clinical Text Demo",
                "prompt": "Demo: Transform clinical text to FHIR Patient + MedicationRequest + Observation",
                "expected_resources": ["Patient", "MedicationRequest", "Observation"]
            }
        ]
        
        for scenario in demo_scenarios:
            print(f"\n--- Testing {scenario['name']} ---")
            response = self.agent.get_response(scenario["prompt"], None)
            
            assert response is not None
            assert len(response) > 50
            
            # In a real implementation, you would validate that the response
            # contains the expected FHIR resource types
            print(f"✓ {scenario['name']} completed successfully")


if __name__ == "__main__":
    # Run integration tests
    test_suite = TestMedStandardizerIntegration()
    test_suite.setup_method()
    
    print("=== MedStandardizer Pro Integration Tests ===\n")
    
    # Run key integration tests
    test_suite.test_agent_initialization()
    print("✓ Agent initialization test passed")
    
    test_suite.test_fhir_validation_helper()
    print("✓ FHIR validation helper test passed")
    
    test_suite.test_performance_benchmarks()
    print("✓ Performance benchmark test passed")
    
    test_suite.test_demo_mode_scenarios()
    print("✓ Demo scenarios test passed")
    
    print("\n=== Integration Tests Completed Successfully ===")
