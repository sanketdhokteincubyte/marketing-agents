from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from fastapi_utils.cbv import cbv

from app.service.agent_service import AgentService
from app.service import PdfService, EmailService
from app.db.models import Agent
from typing import Optional, List


router = APIRouter()


class AgentRequest(BaseModel):
    prompt: str
    user_email: str

@cbv(router)
class AgentRouter:
    """Router for agent-related endpoints"""

    agent_service: AgentService = Depends(AgentService)
    pdf_service: PdfService = Depends(PdfService)
    email_service: EmailService = Depends(EmailService)

    @router.get("/agents")
    def get_agents(self):
        """Get all agents"""
        agents = self.agent_service.get_all_agents()
        if not agents:
            raise HTTPException(status_code=404, detail="No agents found")
        return agents

    @router.get("/agents/count")
    def get_agent_count(self):
        """Get the total count of agents"""
        return self.agent_service.get_agent_count()

    @router.get("/agents/{agent_id}")
    def get_agent(self, agent_id: int):
        """Get a specific agent by ID"""
        print(f"Fetching agent with ID: {agent_id}")
        
        agent = self.agent_service.get_agent_by_id(agent_id)
        prompt = self.agent_service.get_prompt(agent.slug)
        print(f"Found agent: {agent}, Prompt: {prompt}")
        return {"agent": agent, "prompt": prompt}

    @router.post("/create-agent")
    def create_agent(self, agent: Agent):
        """Create a new agent"""
        created_agent = self.agent_service.create_agent(agent)
        return created_agent


    @router.post("/run-agent/{agent_id}")
    def run_agent_by_id(
        self,
        agent_id: int,
        prompt: str = Form(...),
        user_email: str = Form(...),
        files: Optional[List[UploadFile]] = File(None)
    ):
        """
        Run an agent by ID with a given prompt and optional files

        Supported file types for AI Agent (Anthropic Claude):

        Documents:
        - PDF (.pdf)
        - Text (.txt)
        - CSV (.csv)
        - Word Documents (.docx)
        - JSON (.json)

        Images:
        - JPEG (.jpg, .jpeg)
        - PNG (.png)
        - GIF (.gif)
        - WebP (.webp)

        Note: File support varies by agent. AI Agent supports all listed types.
        Other agents may ignore files or have limited support.
        """
        response = self.agent_service.run_agent_by_id(
                agent_id=agent_id,
                prompt=prompt,
                user_email=user_email,
                files=files
            )
        return {"response": response}
       

    @router.put("/agents/{agent_id}")
    def update_agent(self, agent_id: int, updated_data: dict):
        """Update an existing agent"""
        updated_agent = self.agent_service.update_agent(agent_id, updated_data)
        if not updated_agent:
            raise HTTPException(status_code=404, detail=f"Agent with ID {agent_id} not found")
        return updated_agent
        
        

    @router.delete("/agents/{agent_id}")
    def delete_agent(self, agent_id: int):
        """Delete an agent"""
        success = self.agent_service.delete_agent(agent_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Agent with ID {agent_id} not found")
        return {"message": f"Agent with ID {agent_id} deleted successfully"}

    @router.get("/agents/slug/{slug}")
    def get_agent_by_slug(self, slug: str):
        """Get an agent by slug"""
        agent = self.agent_service.get_agent_by_slug(slug)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent with slug '{slug}' not found")
        return agent
        
    @router.get("/agents/exists/{slug}")
    def check_agent_exists(self, slug: str):
        """Check if an agent exists with the given slug"""
        try:
            exists = self.agent_service.agent_exists_by_slug(slug)
            return {"exists": exists}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
