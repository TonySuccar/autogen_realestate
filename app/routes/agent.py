"""
Agent routes - AutoGen only
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from pydantic import BaseModel, Field
from typing import Optional
from app.agents.orchestrator_agent import OrchestratorAgentAutogen
from app.middleware.logging import logger

router = APIRouter(prefix="/agent", tags=["Agent"])

# Store active AutoGen sessions (in production, use Redis or similar)
active_sessions = {}


class AgentRequest(BaseModel):
    message: str = Field(..., description="User's message to the agent")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")


class AgentResponse(BaseModel):
    response: str
    session_id: str


@router.post("/chat", response_model=AgentResponse)
async def chat(req: AgentRequest, db: Session = Depends(get_db)):
    """
    Chat with the AI real estate agent powered by AutoGen. The agent can:
    - Search for properties
    - Schedule viewings
    - Answer real estate questions
    - Provide property details
    
    Provide a session_id to maintain conversation context.
    """
    try:
        # Get or create session
        session_id = req.session_id or f"session_{len(active_sessions)}"
        
        # Get or create AutoGen orchestrator for this session
        if session_id not in active_sessions:
            active_sessions[session_id] = OrchestratorAgentAutogen(db)
            logger.info(f"Created new AutoGen session: {session_id}")
        
        orchestrator = active_sessions[session_id]
        
        # Process message
        response = await orchestrator.chat(req.message)
        
        return {
            "response": response,
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"Error in AutoGen chat: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {str(e)}"
        )


@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """Clear a specific agent session"""
    if session_id in active_sessions:
        active_sessions[session_id].clear_history()
        del active_sessions[session_id]
        return {"message": f"Session {session_id} cleared"}
    return {"message": "Session not found"}
