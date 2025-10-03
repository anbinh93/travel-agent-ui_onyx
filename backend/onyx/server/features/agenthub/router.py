"""
External Agent API Router
CRUD operations for managing n8n-wrapped agents
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional

from onyx.auth.users import current_admin_user, current_user
from onyx.db.engine.sql_engine import get_session_with_current_tenant as get_session
from onyx.server.features.agenthub.external_agent import ExternalAgent
from onyx.server.features.agenthub.service import (
    create_external_agent,
    get_all_external_agents,
    get_external_agent_by_id,
    update_external_agent,
    delete_external_agent,
    test_agent_connection,
)


router = APIRouter(prefix="/agent-hub")


# Pydantic models
class ExternalAgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    api_endpoint: str = Field(..., min_length=1)
    api_key: Optional[str] = None
    auth_type: str = Field(default="bearer")  # bearer, api_key, none
    default_model: str = Field(default="gpt-4o")
    default_temperature: float = Field(default=1.0, ge=0.0, le=2.0)
    default_max_tokens: int = Field(default=4096, gt=0)
    supports_streaming: bool = Field(default=True)
    system_prompt: Optional[str] = None
    additional_params: Optional[dict] = None
    icon_color: Optional[str] = None
    icon_emoji: Optional[str] = None


class ExternalAgentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    auth_type: Optional[str] = None
    default_model: Optional[str] = None
    default_temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    default_max_tokens: Optional[int] = Field(None, gt=0)
    supports_streaming: Optional[bool] = None
    system_prompt: Optional[str] = None
    additional_params: Optional[dict] = None
    icon_color: Optional[str] = None
    icon_emoji: Optional[str] = None
    is_active: Optional[bool] = None


class ExternalAgentResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    api_endpoint: str
    auth_type: str
    default_model: str
    default_temperature: float
    default_max_tokens: int
    supports_streaming: bool
    system_prompt: Optional[str]
    icon_color: Optional[str]
    icon_emoji: Optional[str]
    is_active: bool
    last_test_status: Optional[str]
    last_test_error: Optional[str]

    class Config:
        from_attributes = True


class TestConnectionRequest(BaseModel):
    test_message: str = Field(default="Hello, test connection")


class TestConnectionResponse(BaseModel):
    success: bool
    message: str
    response_preview: Optional[str] = None
    error: Optional[str] = None


# Endpoints
@router.post("/agents", response_model=ExternalAgentResponse)
def create_agent(
    agent_data: ExternalAgentCreate,
    db_session: Session = Depends(get_session),
    _: None = Depends(current_user),  # Any authenticated user can create
) -> ExternalAgent:
    """
    Create a new external agent (n8n workflow)
    """
    try:
        agent = create_external_agent(db_session, agent_data)
        return agent
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/agents", response_model=list[ExternalAgentResponse])
def list_agents(
    include_inactive: bool = False,
    db_session: Session = Depends(get_session),
    _: None = Depends(current_user),
) -> list[ExternalAgent]:
    """
    Get all external agents (organization-wide)
    """
    agents = get_all_external_agents(db_session, include_inactive=include_inactive)
    return agents


@router.get("/agents/{agent_id}", response_model=ExternalAgentResponse)
def get_agent(
    agent_id: int,
    db_session: Session = Depends(get_session),
    _: None = Depends(current_user),
) -> ExternalAgent:
    """
    Get a specific external agent by ID
    """
    agent = get_external_agent_by_id(db_session, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.patch("/agents/{agent_id}", response_model=ExternalAgentResponse)
def update_agent(
    agent_id: int,
    agent_data: ExternalAgentUpdate,
    db_session: Session = Depends(get_session),
    _: None = Depends(current_user),
) -> ExternalAgent:
    """
    Update an existing external agent
    """
    agent = update_external_agent(db_session, agent_id, agent_data)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.delete("/agents/{agent_id}")
def delete_agent(
    agent_id: int,
    db_session: Session = Depends(get_session),
    _: None = Depends(current_admin_user),  # Only admin can delete
) -> dict:
    """
    Delete an external agent (admin only)
    """
    success = delete_external_agent(db_session, agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"success": True, "message": "Agent deleted successfully"}


@router.post("/agents/{agent_id}/test", response_model=TestConnectionResponse)
async def test_agent(
    agent_id: int,
    test_data: TestConnectionRequest,
    db_session: Session = Depends(get_session),
    _: None = Depends(current_user),
) -> TestConnectionResponse:
    """
    Test connection to an external agent
    """
    result = await test_agent_connection(db_session, agent_id, test_data.test_message)
    return result
