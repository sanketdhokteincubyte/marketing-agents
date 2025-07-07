from app.agents.base_agent import BaseAgent
from app.agents.marketing_agents import MarketingAgent
from app.agents.ai_agent import AIAgent
from app.agents.linkedin_writer_agent import LinkedInWriterAgent
from app.agents.tech_blog_writer_agent import TechBlogWriterAgent
from app.agents.lifestyle_blog_writer_agent import LifestyleBlogWriterAgent
from app.agents.clinical_decision_agents import ClinicalDecisionAgent
from app.agents.med_standardizer_agent import MedStandardizerAgent
from app.agents.image_ner_agent import ImageNERAgent
from app.agents.enum.agent_enum import AgentType


class AgentFactory:
    _agents = {
        AgentType.MARKETING_AGENT: MarketingAgent,
        AgentType.AI_AGENT: AIAgent,
        AgentType.LINKEDIN_WRITER_AGENT: LinkedInWriterAgent,
        AgentType.TECH_BLOG_WRITER_AGENT: TechBlogWriterAgent,
        AgentType.LIFESTYLE_BLOG_WRITER_AGENT: LifestyleBlogWriterAgent,
        AgentType.CLINICAL_DECISION_AGENT: ClinicalDecisionAgent,
        AgentType.MED_STANDARDIZER_AGENT: MedStandardizerAgent,
        AgentType.IMAGE_NER_AGENT: ImageNERAgent,
    }

    @staticmethod
    def get_agent(agent_type: AgentType) -> BaseAgent:
        agent_class = AgentFactory._agents.get(agent_type)
        if not agent_class:
            raise ValueError(f"No agent found for type: {agent_type}")
        return agent_class()
