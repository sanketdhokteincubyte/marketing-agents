"""
Agent Service - Business logic layer for agent operations
This service handles the business logic and coordinates between the route layer and repository layer.
"""
from typing import List, Optional
from app.db.models import Agent, UserAgentRun
from app.db.repository.agent_repository import AgentRepository
from app.service.user_agent_run_service import UserAgentRunService
from app.agents.agent_factory import AgentFactory
import textwrap
from fastapi import HTTPException, UploadFile
from app.agents.agent_prompt_repository import agent_prompt_repository
from app.agents.enum.agent_enum import AgentType




class AgentService:
    """Service layer for managing agents and their operations"""
    
    def __init__(self):
        self.agent_repository = AgentRepository()
        self.user_agent_run_service = UserAgentRunService()

    def get_all_agents(self) -> List[Agent]:
        """Get all agents from the repository"""
        try:
            agents = self.agent_repository.get_all()
            return agents
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve list of agents: {str(e)}")

    def get_agent_by_id(self, agent_id: int) -> Optional[Agent]:
        """Get a specific agent by ID"""
        agent = self.agent_repository.get_by_id(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent with ID {agent_id} not found")
        return agent
     
        
        
    def get_prompt(self, slug: AgentType) -> Optional[str]:
        """Get the prompt for a specific agent by slug"""
        prompt = agent_prompt_repository.get(AgentType(slug))
        if not prompt:
            return "Enter your prompt here"
        return prompt

    def create_agent(self, agent: Agent) -> Agent:
        """Create a new agent"""
            # Add any business logic validation here
        if not agent.name or not agent.slug:
            raise ValueError("Agent name and slug are required")
            
            # Check if agent with same slug already exists
        if self.agent_repository.exists_by_slug(agent.slug):
            raise ValueError(f"Agent with slug '{agent.slug}' already exists")

        created_agent = self.agent_repository.create(agent)
        return created_agent

    def run_agent_by_id(self, agent_id: int, prompt: str, user_email: str, files: Optional[List[UploadFile]] = None) -> str:
        """Run an agent by ID with the given prompt"""
        
            # Validate inputs
        if not prompt:
            raise ValueError("Prompt must not be empty")
        
        if not user_email:
            raise ValueError("User email must not be empty")
            
            # Get agent data from repository
        agent = self.get_agent_by_id(agent_id)
        if not agent:
            raise  HTTPException(status_code=404, detail=f"Agent with ID {agent_id} not found")
        agent = AgentFactory.get_agent(AgentType(agent.slug))

            # Generate response


        user_agent_run = self.save_user_agent_run(user_email, agent_id)
        response = agent.get_response(prompt, files, user_email)
            
            # Clean up response
        clean_response = textwrap.dedent(response).lstrip()
            
        return clean_response
        

    def update_agent(self, agent_id: int, updated_data: dict) -> Optional[Agent]:
        """Update an existing agent"""
        agent = self.get_agent_by_id(agent_id)
        if not agent:
            raise  HTTPException(status_code=404, detail=f"Agent with ID {agent_id} not found")
            
            # Update agent fields
        for key, value in updated_data.items():
            if hasattr(agent, key):
                setattr(agent, key, value)
            
            # Use the repository update method
        return self.agent_repository.update(agent)

    def delete_agent(self, agent_id: int) -> Agent:
        """Delete an agent"""
        agent = self.get_agent_by_id(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent with ID {agent_id} not found")
        return self.agent_repository.delete(agent)

    def get_agent_by_slug(self, slug: str) -> Optional[Agent]:
        """Get an agent by slug"""
        agent = self.agent_repository.get_by_slug(slug)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent with slug {slug} not found")
        return agent

    def agent_exists_by_slug(self, slug: str) -> bool:
        """Check if an agent exists with the given slug"""
        try:
            return self.agent_repository.exists_by_slug(slug)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to check agent existence: {str(e)}")

    def get_agent_count(self) -> dict:
        """Get the total count of agents"""
        try:
            return self.agent_repository.agent_count()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to get agent count: {str(e)}")

    def save_user_agent_run(self, email: str, agent_id: int) -> Optional[UserAgentRun]:
        """Save a user agent run"""
        try:
            return self.user_agent_run_service.create(email, agent_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save user agent run: {str(e)}")