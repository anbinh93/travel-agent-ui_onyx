from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query

from onyx.auth.users import current_chat_accessible_user
from onyx.server.models import User
from onyx.agents.registry import get_agent_registry
from onyx.agents.base import AgentType, AgentCapability, TriggerType
from onyx.agents.knowledge.manager import get_knowledge_base_manager
from onyx.agents.knowledge import (
    KnowledgeBase,
    KnowledgeSourceType,
    ConnectorConfig,
)


router = APIRouter(prefix="/agenthub", tags=["AgentHub"])


# ==================== Request/Response Models ====================

class RunAgentRequest(BaseModel):
    agent_key: str
    query: str
    context: Optional[dict[str, Any]] = None


class RunAgentResponse(BaseModel):
    answer: str
    sources: list[dict] = Field(default_factory=list)
    plans: Optional[list[dict]] = None
    needs_clarification: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentMetadata(BaseModel):
    """Agent metadata for listing - like model metadata."""
    key: str
    name: str
    description: str
    type: str
    capabilities: list[str]
    use_knowledge_base: bool
    knowledge_base_count: int
    version: str
    icon: Optional[str]
    color: Optional[str]
    tags: list[str]
    requires_api_key: bool
    max_tokens: Optional[int]
    timeout_seconds: int


class AgentModelSelectorFormat(BaseModel):
    """Format for model selector UI - agents appear alongside GPT-4o, Claude, etc."""
    id: str  # Format: "agent:agent_key"
    name: str
    description: str
    provider: str = "AgentHub"
    type: str = "agent"
    capabilities: list[str]
    icon: str
    color: str
    version: str
    metadata: dict[str, Any]


class CreateKnowledgeBaseRequest(BaseModel):
    name: str
    description: str = ""
    agent_keys: list[str] = Field(default_factory=list)


class AddConnectorRequest(BaseModel):
    kb_id: UUID
    connector_type: str
    name: str
    config: dict[str, Any]
    auto_sync: bool = True
    sync_interval_minutes: int = 60


class KnowledgeBaseResponse(BaseModel):
    kb_id: UUID
    name: str
    description: str
    status: str
    enabled: bool
    current_version: str
    agent_keys: list[str]
    connector_count: int
    created_at: datetime
    updated_at: datetime


# ==================== Agent Endpoints ====================

@router.get("/agents", response_model=list[AgentMetadata])
def get_available_agents(
    agent_type: Optional[str] = Query(None, description="Filter by agent type"),
    capability: Optional[str] = Query(None, description="Filter by capability"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    user: User | None = Depends(current_chat_accessible_user),
) -> list[AgentMetadata]:
    """
    Get all available agents with optional filtering.
    Similar to listing available models.
    """
    registry = get_agent_registry()
    
    # Parse filters
    filter_type = AgentType(agent_type) if agent_type else None
    filter_capability = AgentCapability(capability) if capability else None
    
    agents = registry.list_all(
        agent_type=filter_type,
        capability=filter_capability,
        tag=tag,
    )
    
    return [AgentMetadata(**agent.to_metadata()) for agent in agents]


@router.get("/agents/models", response_model=list[AgentModelSelectorFormat])
def get_agents_for_model_selector(
    user: User | None = Depends(current_chat_accessible_user),
) -> list[AgentModelSelectorFormat]:
    """
    Get agents in format compatible with model selector UI.
    This allows agents to appear in the same dropdown as GPT-4o, Claude, etc.
    
    Usage in frontend:
    - Fetch both /api/models and /api/agenthub/agents/models
    - Merge the lists
    - Agents will have id prefix "agent:" to distinguish from models
    """
    registry = get_agent_registry()
    models = registry.list_for_model_selector()
    return [AgentModelSelectorFormat(**model) for model in models]


@router.get("/agents/{agent_key}", response_model=AgentMetadata)
def get_agent_details(
    agent_key: str,
    user: User | None = Depends(current_chat_accessible_user),
) -> AgentMetadata:
    """Get detailed information about a specific agent."""
    registry = get_agent_registry()
    agent = registry.get(agent_key)
    
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_key}' not found")
    
    return AgentMetadata(**agent.to_metadata())


@router.post("/run", response_model=RunAgentResponse)
def run_agent(
    body: RunAgentRequest,
    user: User | None = Depends(current_chat_accessible_user),
) -> RunAgentResponse:
    """
    Execute an agent with a query.
    Similar to LLM completion endpoint but for agents.
    
    This is called when user selects an agent in the chat interface.
    """
    registry = get_agent_registry()
    
    try:
        # Add user context
        context = body.context or {}
        if user:
            context["user_id"] = user.id
            context["user_email"] = user.email
        
        # Execute agent
        result = registry.execute_agent(
            agent_key=body.agent_key,
            query=body.query,
            context=context,
        )
        
        return RunAgentResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")


# ==================== Knowledge Base Endpoints ====================

@router.post("/knowledge-bases", response_model=KnowledgeBaseResponse)
def create_knowledge_base(
    body: CreateKnowledgeBaseRequest,
    user: User | None = Depends(current_chat_accessible_user),
) -> KnowledgeBaseResponse:
    """Create a new knowledge base for agents."""
    kb_manager = get_knowledge_base_manager()
    
    kb = kb_manager.create_knowledge_base(
        name=body.name,
        description=body.description,
        agent_keys=body.agent_keys,
        created_by=user.email if user else None,
    )
    
    return KnowledgeBaseResponse(
        kb_id=kb.kb_id,
        name=kb.name,
        description=kb.description,
        status=kb.status.value,
        enabled=kb.enabled,
        current_version=kb.current_version,
        agent_keys=kb.agent_keys,
        connector_count=len(kb.connectors),
        created_at=kb.created_at,
        updated_at=kb.updated_at,
    )


@router.get("/knowledge-bases", response_model=list[KnowledgeBaseResponse])
def list_knowledge_bases(
    agent_key: Optional[str] = Query(None, description="Filter by agent"),
    enabled_only: bool = Query(False, description="Only show enabled KBs"),
    user: User | None = Depends(current_chat_accessible_user),
) -> list[KnowledgeBaseResponse]:
    """List all knowledge bases."""
    kb_manager = get_knowledge_base_manager()
    kbs = kb_manager.list_knowledge_bases(agent_key=agent_key, enabled_only=enabled_only)
    
    return [
        KnowledgeBaseResponse(
            kb_id=kb.kb_id,
            name=kb.name,
            description=kb.description,
            status=kb.status.value,
            enabled=kb.enabled,
            current_version=kb.current_version,
            agent_keys=kb.agent_keys,
            connector_count=len(kb.connectors),
            created_at=kb.created_at,
            updated_at=kb.updated_at,
        )
        for kb in kbs
    ]


@router.post("/knowledge-bases/{kb_id}/enable")
def enable_knowledge_base(
    kb_id: UUID,
    user: User | None = Depends(current_chat_accessible_user),
) -> dict:
    """Enable a knowledge base."""
    kb_manager = get_knowledge_base_manager()
    
    if not kb_manager.enable_knowledge_base(kb_id):
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    return {"message": "Knowledge base enabled", "kb_id": str(kb_id)}


@router.post("/knowledge-bases/{kb_id}/disable")
def disable_knowledge_base(
    kb_id: UUID,
    user: User | None = Depends(current_chat_accessible_user),
) -> dict:
    """Disable a knowledge base."""
    kb_manager = get_knowledge_base_manager()
    
    if not kb_manager.disable_knowledge_base(kb_id):
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    return {"message": "Knowledge base disabled", "kb_id": str(kb_id)}


@router.post("/knowledge-bases/connectors", response_model=dict)
def add_connector_to_kb(
    body: AddConnectorRequest,
    user: User | None = Depends(current_chat_accessible_user),
) -> dict:
    """Add a connector to feed data into a knowledge base."""
    kb_manager = get_knowledge_base_manager()
    
    try:
        connector_type = KnowledgeSourceType(body.connector_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid connector type: {body.connector_type}")
    
    connector = kb_manager.add_connector(
        kb_id=body.kb_id,
        connector_type=connector_type,
        name=body.name,
        config=body.config,
        auto_sync=body.auto_sync,
        sync_interval_minutes=body.sync_interval_minutes,
    )
    
    if not connector:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    return {
        "message": "Connector added successfully",
        "connector_id": str(connector.connector_id),
        "kb_id": str(body.kb_id),
    }


@router.post("/knowledge-bases/{kb_id}/sync")
def trigger_sync(
    kb_id: UUID,
    connector_id: Optional[UUID] = Query(None, description="Specific connector to sync, or all if omitted"),
    user: User | None = Depends(current_chat_accessible_user),
) -> dict:
    """Manually trigger a sync for a knowledge base."""
    kb_manager = get_knowledge_base_manager()
    
    if not kb_manager.trigger_sync(kb_id, connector_id):
        raise HTTPException(status_code=404, detail="Knowledge base or connector not found")
    
    return {
        "message": "Sync triggered successfully",
        "kb_id": str(kb_id),
        "connector_id": str(connector_id) if connector_id else "all",
    }



