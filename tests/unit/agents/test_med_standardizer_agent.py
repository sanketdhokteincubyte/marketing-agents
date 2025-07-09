import pytest
import tempfile
import os
from fastapi import UploadFile
from io import BytesIO
from app.agents.med_standardizer_agent import MedStandardizerAgent


class TestMedStandardizerAgent:
    """Test cases for MedStandardizer Pro agent with demo scenarios"""

    def setup_method(self):
        """Setup test environment"""
        self.agent = MedStandardizerAgent()

    def create_upload_file(self, content: str, filename: str, content_type: str) -> UploadFile:
        """Helper method to create UploadFile objects for testing"""
        file_obj = BytesIO(content.encode('utf-8'))
        return UploadFile(filename=filename, file=file_obj, content_type=content_type)

    def test_scenario_1_lab_results_csv_to_fhir(self):
        """
        Demo Scenario 1: Lab Results CSV → FHIR
        Convert lab results CSV to FHIR Patient + Observation resources
        """
        # Sample lab results CSV data
        csv_content = """PAT_ID,PATIENT_NM,DOB,TEST_CD,TEST_NM,RESULT,UNITS
12345,"Doe, John",03/15/1985,GLU,Glucose,95,mg/dL
12345,"Doe, John",03/15/1985,CHOL,Cholesterol,180,mg/dL
67890,"Smith, Jane",07/22/1990,GLU,Glucose,110,mg/dL"""

        # Create upload file
        upload_file = self.create_upload_file(csv_content, "lab_results.csv", "text/csv")
        
        # Test prompt
        prompt = """
        Transform this lab results CSV data into FHIR format. 
        Create Patient resources for each unique patient and Observation resources for each lab test.
        Include confidence scores and processing metadata.
        """

        # Execute agent
        response = self.agent.get_response(prompt, [upload_file])
        
        # Assertions
        assert response is not None
        assert len(response) > 0
        # Note: In a real test, you would parse the JSON response and validate FHIR structure
        print(f"Scenario 1 Response: {response[:500]}...")

    def test_scenario_2_patient_xml_to_fhir(self):
        """
        Demo Scenario 2: Patient XML → FHIR
        Convert patient XML record to FHIR Patient resource
        """
        # Sample patient XML data
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<PatientRecord>
    <patient_number>98765</patient_number>
    <fname>Sarah</fname>
    <lname>Johnson</lname>
    <birth_dt>1990-07-22</birth_dt>
    <sex>F</sex>
    <address>
        <street>123 Main St</street>
        <city>Springfield</city>
        <state>IL</state>
        <zip>62701</zip>
    </address>
    <phone>555-123-4567</phone>
    <email>sarah.johnson@email.com</email>
</PatientRecord>"""

        # Create upload file
        upload_file = self.create_upload_file(xml_content, "patient_record.xml", "application/xml")
        
        # Test prompt
        prompt = """
        Transform this patient XML record into FHIR Patient resource format.
        Map all available fields to appropriate FHIR elements.
        Provide confidence scores for the transformation.
        """

        # Execute agent
        response = self.agent.get_response(prompt, [upload_file])
        
        # Assertions
        assert response is not None
        assert len(response) > 0
        print(f"Scenario 2 Response: {response[:500]}...")

    def test_scenario_3_clinical_text_to_fhir(self):
        """
        Demo Scenario 3: Clinical Text → FHIR
        Convert clinical text to FHIR Patient + MedicationRequest + Observation resources
        """
        # Sample clinical text data
        text_content = """Patient: Mary Smith (DOB: 05/12/1975, MRN: 54321)
Gender: Female
Address: 456 Oak Avenue, Chicago, IL 60601
Phone: 555-987-6543

Current Medications:
- Metformin 500mg BID (twice daily)
- Lisinopril 10mg daily
- Atorvastatin 20mg daily

Vital Signs (Today's Visit):
- Blood Pressure: 145/92 mmHg
- Heart Rate: 88 bpm
- Temperature: 98.6°F
- Weight: 165 lbs
- Height: 5'6"

Lab Results:
- HbA1c: 7.2%
- Total Cholesterol: 220 mg/dL
- LDL: 140 mg/dL
- HDL: 45 mg/dL

Assessment: Type 2 Diabetes Mellitus, Hypertension, Hyperlipidemia"""

        # Create upload file
        upload_file = self.create_upload_file(text_content, "clinical_note.txt", "text/plain")
        
        # Test prompt
        prompt = """
        Transform this clinical text into FHIR resources.
        Create:
        1. Patient resource with demographics
        2. MedicationRequest resources for each medication
        3. Observation resources for vital signs and lab results
        
        Include confidence scores and processing metadata.
        """

        # Execute agent
        response = self.agent.get_response(prompt, [upload_file])
        
        # Assertions
        assert response is not None
        assert len(response) > 0
        print(f"Scenario 3 Response: {response[:500]}...")

    def test_multiple_format_processing(self):
        """
        Test processing multiple file formats simultaneously
        """
        # Create multiple files
        csv_content = "PAT_ID,NAME,DOB\n11111,Test Patient,01/01/1980"
        json_content = '{"patient_id": "22222", "name": "JSON Patient", "birthDate": "1985-05-15"}'
        
        csv_file = self.create_upload_file(csv_content, "patients.csv", "text/csv")
        json_file = self.create_upload_file(json_content, "patient.json", "application/json")
        
        prompt = """
        Process these multiple medical data files and transform them into FHIR format.
        Combine all patient data into a unified FHIR Bundle.
        """

        # Execute agent
        response = self.agent.get_response(prompt, [csv_file, json_file])
        
        # Assertions
        assert response is not None
        assert len(response) > 0
        print(f"Multiple Format Response: {response[:500]}...")

    def test_empty_prompt_with_files(self):
        """
        Test agent behavior with files but minimal prompt
        """
        csv_content = "ID,Name,Age\n1,Test,30"
        upload_file = self.create_upload_file(csv_content, "test.csv", "text/csv")
        
        prompt = "Transform to FHIR"

        # Execute agent
        response = self.agent.get_response(prompt, [upload_file])
        
        # Assertions
        assert response is not None
        assert len(response) > 0

    def test_no_files_provided(self):
        """
        Test agent behavior with prompt but no files
        """
        prompt = """
        I need help transforming medical data to FHIR format. 
        Can you explain the process and provide an example?
        """

        # Execute agent
        response = self.agent.get_response(prompt, None)
        
        # Assertions
        assert response is not None
        assert len(response) > 0
        print(f"No Files Response: {response[:200]}...")

    def test_unsupported_file_type(self):
        """
        Test agent behavior with unsupported file types
        """
        # Create a fake image file
        fake_image = self.create_upload_file("fake image data", "test.png", "image/png")
        
        prompt = "Transform this medical data to FHIR"

        # Execute agent (should skip unsupported file)
        response = self.agent.get_response(prompt, [fake_image])
        
        # Assertions
        assert response is not None
        assert len(response) > 0

    @pytest.mark.integration
    def test_full_workflow_integration(self):
        """
        Integration test for complete workflow with realistic medical data
        """
        # Comprehensive medical data
        comprehensive_data = """Patient Demographics:
Name: Robert Johnson
DOB: 03/15/1965
Gender: Male
MRN: 789012
SSN: 123-45-6789
Address: 789 Pine Street, Boston, MA 02101
Phone: 617-555-0123
Email: robert.johnson@email.com

Insurance: Blue Cross Blue Shield
Policy Number: BC123456789

Current Medications:
1. Lisinopril 10mg PO daily for hypertension
2. Metformin 1000mg PO BID for diabetes
3. Atorvastatin 40mg PO daily for hyperlipidemia
4. Aspirin 81mg PO daily for cardioprotection

Allergies:
- Penicillin (rash)
- Sulfa drugs (hives)

Vital Signs (Current Visit - 2024-01-15):
- BP: 138/85 mmHg
- HR: 72 bpm
- Temp: 98.4°F
- Resp: 16/min
- O2 Sat: 98% on room air
- Weight: 185 lbs
- Height: 5'10"
- BMI: 26.5

Recent Lab Results (2024-01-10):
- HbA1c: 6.8%
- Fasting Glucose: 125 mg/dL
- Total Cholesterol: 195 mg/dL
- LDL: 115 mg/dL
- HDL: 42 mg/dL
- Triglycerides: 190 mg/dL
- Creatinine: 1.1 mg/dL
- eGFR: 75 mL/min/1.73m²

Medical History:
- Type 2 Diabetes Mellitus (diagnosed 2018)
- Essential Hypertension (diagnosed 2015)
- Hyperlipidemia (diagnosed 2016)
- Coronary Artery Disease (diagnosed 2020)

Assessment and Plan:
1. Diabetes: Well controlled, continue current regimen
2. Hypertension: Slightly elevated, consider dose adjustment
3. Hyperlipidemia: At goal, continue statin therapy
4. CAD: Stable, continue aspirin and statin"""

        upload_file = self.create_upload_file(comprehensive_data, "comprehensive_record.txt", "text/plain")
        
        prompt = """
        This is a comprehensive medical record. Please transform it into a complete FHIR Bundle containing:
        
        1. Patient resource with full demographics
        2. MedicationRequest resources for all current medications
        3. Observation resources for all vital signs and lab results
        4. AllergyIntolerance resources for documented allergies
        5. Condition resources for medical history items
        
        Ensure all resources are properly linked and include:
        - Confidence scores for each transformation
        - Data quality assessment
        - Processing metadata
        - FHIR compliance validation
        
        Format the output as valid JSON with clear structure.
        """

        # Execute agent
        response = self.agent.get_response(prompt, [upload_file])
        
        # Assertions
        assert response is not None
        assert len(response) > 0
        
        # In a real implementation, you would:
        # 1. Parse the JSON response
        # 2. Validate FHIR structure
        # 3. Check confidence scores
        # 4. Verify all expected resources are present
        # 5. Validate resource relationships
        
        print(f"Integration Test Response Length: {len(response)} characters")
        print(f"First 1000 characters: {response[:1000]}...")


if __name__ == "__main__":
    # Run specific test scenarios for demo
    test_agent = TestMedStandardizerAgent()
    test_agent.setup_method()
    
    print("=== MedStandardizer Pro Demo Test Scenarios ===\n")
    
    print("1. Testing Lab Results CSV → FHIR...")
    test_agent.test_scenario_1_lab_results_csv_to_fhir()
    
    print("\n2. Testing Patient XML → FHIR...")
    test_agent.test_scenario_2_patient_xml_to_fhir()
    
    print("\n3. Testing Clinical Text → FHIR...")
    test_agent.test_scenario_3_clinical_text_to_fhir()
    
    print("\n=== Demo Tests Completed ===")
