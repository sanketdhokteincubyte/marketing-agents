from typing import Iterator, List, Optional
from agno.agent import Agent, RunResponse
from agno.models.anthropic import Claude
from agno.storage.sqlite import SqliteStorage
from agno.tools.googlesearch import GoogleSearchTools
from agno.tools.crawl4ai import Crawl4aiTools
from app.agents.base_agent import BaseAgent
from app.core import settings
from agno.utils.pprint import pprint_run_response
from fastapi import UploadFile
import json

class ClinicalDecisionAgent(BaseAgent):
    def __init__(self):
        self.AGENT_STORAGE = settings.AGENT_STORAGE
        print(self.AGENT_STORAGE)
        self.clinical_decision_team = self._create_clinical_decision_team()

    # Factory methods for creating individual agents
    def create_patient_assessment_agent(self):
        return Agent(
            name="Patient Assessment Agent",
            role="You are an expert at analyzing comprehensive patient data for clinical decision-making",
            model=Claude(id="claude-3-7-sonnet-20250219", max_tokens=8096),
            instructions=[
                "Analyze patient demographics, medical history, current medications, and laboratory values",
                "Identify contraindications, drug allergies, and potential drug interactions",
                "Assess comorbidities and their impact on treatment selection",
                "Evaluate organ function status (kidney, liver, cardiac) for medication dosing",
                "Review previous treatment failures, intolerances, and patient-specific factors",
                "Assess social and lifestyle factors affecting treatment adherence and outcomes",
                "Identify high-priority risk factors that must be considered in treatment selection",
                "Generate patient-specific risk stratification (high/moderate/low risk alerts)",
                "Create comprehensive patient profile summary for clinical decision-making",
                "Format all output in structured markdown with clear risk categorization",
                "Use clinical severity scoring systems when applicable (PHQ-9, CHA2DS2-VASc, etc.)",
                "Flag any missing critical information needed for optimal decision-making",
            ],
            show_tool_calls=True,
            tools=[GoogleSearchTools(fixed_max_results=3), Crawl4aiTools(max_length=15000)],
            stream=True,
            markdown=True,
        )

    def create_treatment_comparison_agent(self):
        return Agent(
            name="Treatment Comparison Agent",
            role="You are an expert at comparing therapeutic alternatives using evidence-based medicine",
            model=Claude(id="claude-3-7-sonnet-20250219", max_tokens=8096),
            instructions=[
                "Compare multiple therapeutic alternatives for efficacy, safety, and tolerability",
                "Analyze clinical trial data, meta-analyses, and real-world evidence",
                "Create detailed comparison matrices showing efficacy rates, side effect profiles",
                "Evaluate drug-specific benefits for comorbid conditions (dual benefits)",
                "Assess medication-specific risks and monitoring requirements",
                "Consider patient-specific factors in treatment ranking (age, comorbidities, preferences)",
                "Apply current clinical practice guidelines and evidence-based recommendations",
                "Synthesize evidence quality and strength of recommendations",
                "Generate ranked treatment options with detailed rationale for each choice",
                "Include cost-effectiveness considerations when relevant",
                "Format output in clear comparison tables and evidence summaries",
                "Provide specific dosing guidelines and administration recommendations",
            ],
            show_tool_calls=True,
            tools=[GoogleSearchTools(fixed_max_results=3), Crawl4aiTools(max_length=15000)],
            stream=True,
            markdown=True,
        )

    def create_safety_monitoring_agent(self):
        return Agent(
            name="Safety Monitoring Agent",
            role="You are an expert at developing comprehensive safety monitoring protocols for clinical treatments",
            model=Claude(id="claude-3-7-sonnet-20250219", max_tokens=8096),
            instructions=[
                "Screen for medication-specific contraindications and precautions",
                "Identify required pre-treatment assessments and baseline measurements",
                "Create personalized monitoring schedules based on medication and patient factors",
                "Establish laboratory monitoring requirements and frequency",
                "Define warning signs and emergency protocols for adverse events",
                "Develop dose adjustment protocols based on response and tolerability",
                "Create patient education materials for safety monitoring",
                "Establish criteria for treatment discontinuation or modification",
                "Generate follow-up schedules with specific assessment timelines",
                "Create safety checklists for healthcare providers",
                "Format output as structured monitoring dashboards and protocols",
                "Include specific instructions for handling adverse events",
            ],
            show_tool_calls=True,
            tools=[GoogleSearchTools(fixed_max_results=3), Crawl4aiTools(max_length=15000)],
            stream=True,
            markdown=True,
        )

    def create_clinical_documentation_agent(self):
        return Agent(
            name="Clinical Documentation Agent",
            role="You are an expert at creating comprehensive clinical documentation and decision support materials",
            model=Claude(id="claude-3-7-sonnet-20250219", max_tokens=8096),
            instructions=[
                "Generate primary treatment recommendations with detailed clinical rationale",
                "Create comprehensive medical record documentation ready for clinical use",
                "Develop prior authorization materials with evidence-based justifications",
                "Generate patient counseling scripts and education materials",
                "Create follow-up decision trees with specific response criteria",
                "Document alternative treatment options with ranking rationale",
                "Produce clinical pathway summaries for care team coordination",
                "Generate audit trails showing decision-making process and evidence sources",
                "Create patient-friendly educational materials about treatment choices",
                "Develop shared decision-making conversation guides",
                "Format all documentation in clinical-ready formats",
                "Include appropriate diagnostic codes and billing considerations",
                "Create templates for ongoing monitoring and follow-up documentation",
            ],
            show_tool_calls=True,
            tools=[GoogleSearchTools(fixed_max_results=3), Crawl4aiTools(max_length=15000)],
            stream=True,
            markdown=True,
        )

    def _create_clinical_decision_team(self):
        return Agent(
            name="Clinical Decision Support Team",
            team=[
                self.create_patient_assessment_agent(),
                self.create_treatment_comparison_agent(),
                self.create_safety_monitoring_agent(),
                self.create_clinical_documentation_agent()
            ],
            model=Claude(id="claude-3-7-sonnet-20250219", max_tokens=12000),
            instructions=[
                "You are a team of clinical experts who work together to provide comprehensive clinical decision support.",
                "Given patient information and clinical questions, conduct a thorough analysis to recommend optimal treatment choices.",
                "Each team member has specific expertise in clinical decision-making:",
                "1. Patient Assessment Agent: Analyzes patient data and identifies risk factors",
                "2. Treatment Comparison Agent: Compares therapeutic alternatives using evidence-based medicine",
                "3. Safety Monitoring Agent: Develops comprehensive safety and monitoring protocols",
                "4. Clinical Documentation Agent: Creates clinical documentation and decision support materials",
                "Work systematically through the clinical decision process:",
                "- First assess the patient comprehensively including all risk factors",
                "- Then compare available treatment options with evidence-based analysis",
                "- Develop appropriate safety monitoring protocols",
                "- Finally create comprehensive documentation and recommendations",
                "Provide evidence-based, patient-centered recommendations that prioritize safety and efficacy",
                "Include specific dosing, monitoring, and follow-up protocols",
                "Format all output in structured clinical reports with clear sections",
                "Use standard medical terminology and clinical decision-making frameworks",
                "Ensure all recommendations are actionable and implementable in clinical practice",
                "Include appropriate risk-benefit analysis for all treatment decisions",
            ],
            show_tool_calls=True,
            markdown=True,
            storage=SqliteStorage(table_name="clinical_decision_team", db_file=self.AGENT_STORAGE),
            stream=True,
        )

    def analyze_clinical_case(self, patient_data):
        print(f"Starting clinical decision analysis for patient case")
        
        # Parse patient data if it's a string
        if isinstance(patient_data, str):
            try:
                patient_info = json.loads(patient_data)
            except json.JSONDecodeError:
                patient_info = {"clinical_question": patient_data}
        else:
            patient_info = patient_data

        prompt = f"""
        Please conduct a comprehensive clinical decision analysis for the following patient case:

        PATIENT INFORMATION:
        {json.dumps(patient_info, indent=2)}

        Follow this systematic clinical decision process:

        1. PATIENT ASSESSMENT:
        - Analyze all patient demographics, medical history, current medications
        - Identify contraindications, allergies, and drug interactions
        - Assess comorbidities and organ function
        - Evaluate social and lifestyle factors
        - Generate risk stratification

        2. TREATMENT COMPARISON:
        - Identify all appropriate therapeutic alternatives
        - Compare efficacy, safety, and tolerability profiles
        - Analyze clinical trial and real-world evidence
        - Rank treatment options based on patient-specific factors
        - Apply current clinical guidelines

        3. SAFETY MONITORING:
        - Develop comprehensive monitoring protocols
        - Identify required pre-treatment assessments
        - Create personalized monitoring schedules
        - Define warning signs and emergency protocols
        - Establish follow-up criteria

        4. CLINICAL DOCUMENTATION:
        - Generate primary treatment recommendation with rationale
        - Create medical record documentation
        - Develop patient counseling materials
        - Produce follow-up decision trees
        - Generate alternative treatment options

        Provide a comprehensive clinical decision report with:
        - Treatment Comparison Matrix
        - Patient-Specific Risk Assessment
        - Evidence Summary Report
        - Primary Recommendation with detailed rationale
        - Safety Monitoring Dashboard
        - Alternative Options (ranked)
        - Patient Counseling Points
        - Follow-up Action Plan
        - Clinical Documentation

        Ensure all recommendations are evidence-based, patient-centered, and clinically actionable.
        """

        try:
            response_stream: Iterator[RunResponse] = self.clinical_decision_team.run(prompt)
            content = ""
            for response in response_stream:
                content += response.content
            pprint_run_response(response, markdown=True)
            print("Clinical decision team analysis completed successfully.")
            return content
        except Exception as e:
            print(f"Error running clinical decision team: {e}")
            return f"# Clinical Decision Analysis Error: {e}"

    def run_clinical_decision_agent(self, patient_data) -> str:
        return self.analyze_clinical_case(patient_data)
    
    def get_response(self, patient_data: str, files: Optional[List[UploadFile]] = None) -> str:
        response = self.run_clinical_decision_agent(patient_data)
        return response
