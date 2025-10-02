from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Optional
from uuid import UUID


AgentResult = Dict[str, Any]
AgentRunner = Callable[[str, dict[str, Any]], AgentResult]


class AgentType(str, Enum):
    """Types of agents in the hub."""
    CONVERSATIONAL = "conversational"  # Like Travel Agent
    RESEARCH = "research"  # Deep research agents
    TASK_EXECUTOR = "task_executor"  # Execute specific tasks
    WORKFLOW = "workflow"  # Multi-step workflows
    CUSTOM = "custom"


class AgentCapability(str, Enum):
    """Capabilities that agents can have."""
    WEB_SEARCH = "web_search"
    RAG = "rag"  # Retrieval Augmented Generation
    TOOL_CALLING = "tool_calling"
    CODE_EXECUTION = "code_execution"
    FILE_PROCESSING = "file_processing"
    API_INTEGRATION = "api_integration"
    SCHEDULING = "scheduling"
    CONDITIONAL_LOGIC = "conditional_logic"


class TriggerType(str, Enum):
    """Types of triggers for agents."""
    MANUAL = "manual"  # User asks in chat
    SCHEDULED = "scheduled"  # Cron jobs
    WEBHOOK = "webhook"  # External events
    CONNECTOR_EVENT = "connector_event"  # Data sync events


@dataclass
class AgentTriggerConfig:
    """Configuration for agent triggers."""
    trigger_type: TriggerType
    enabled: bool = True
    
    # Scheduled trigger config
    cron_expression: Optional[str] = None
    
    # Webhook trigger config
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    
    # Connector event config
    connector_events: list[str] = None  # e.g., ["on_sync", "on_update"]


@dataclass(frozen=True)
class AgentDefinition:
    """
    Metadata describing a pluggable AgentHub agent.
    
    Agents are like models - they can be selected in the chat interface
    and invoked with queries. Each agent is wrapped as an API endpoint.
    """

    key: str  # Unique identifier (e.g., "travel_agent", "research_agent")
    name: str  # Display name (e.g., "Travel Planning Agent")
    description: str  # What this agent does
    runner: AgentRunner  # The actual agent execution function
    
    # Agent metadata (like model metadata)
    agent_type: AgentType = AgentType.CONVERSATIONAL
    capabilities: list[AgentCapability] = None
    
    # Knowledge base integration
    use_knowledge_base: bool = False
    knowledge_base_ids: list[UUID] = None
    
    # API-like properties
    api_endpoint: Optional[str] = None  # If agent is external API
    requires_api_key: bool = False
    
    # Versioning (like model versions)
    version: str = "1.0.0"
    
    # Triggers
    triggers: list[AgentTriggerConfig] = None
    
    # Resource limits
    max_tokens: Optional[int] = None
    timeout_seconds: int = 300
    
    # UI metadata
    icon: Optional[str] = None  # Emoji or icon identifier
    color: Optional[str] = None  # For UI display
    tags: list[str] = None
    
    # Monitoring
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        # Set defaults for mutable fields
        if self.capabilities is None:
            object.__setattr__(self, 'capabilities', [])
        if self.knowledge_base_ids is None:
            object.__setattr__(self, 'knowledge_base_ids', [])
        if self.triggers is None:
            object.__setattr__(self, 'triggers', [AgentTriggerConfig(trigger_type=TriggerType.MANUAL)])
        if self.tags is None:
            object.__setattr__(self, 'tags', [])
        if self.created_at is None:
            object.__setattr__(self, 'created_at', datetime.utcnow())
        if self.updated_at is None:
            object.__setattr__(self, 'updated_at', datetime.utcnow())

    def to_metadata(self) -> dict[str, Any]:
        """
        Convert to metadata dict for API responses.
        Similar to model metadata in LLM APIs.
        """
        return {
            "key": self.key,
            "name": self.name,
            "description": self.description,
            "type": self.agent_type.value,
            "capabilities": [cap.value for cap in self.capabilities],
            "use_knowledge_base": self.use_knowledge_base,
            "knowledge_base_count": len(self.knowledge_base_ids),
            "version": self.version,
            "api_endpoint": self.api_endpoint,
            "requires_api_key": self.requires_api_key,
            "triggers": [
                {
                    "type": t.trigger_type.value,
                    "enabled": t.enabled,
                    "cron": t.cron_expression,
                }
                for t in self.triggers
            ],
            "max_tokens": self.max_tokens,
            "timeout_seconds": self.timeout_seconds,
            "icon": self.icon,
            "color": self.color,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def to_model_selector_format(self) -> dict[str, Any]:
        """
        Convert to format compatible with model selector UI.
        This allows agents to appear alongside models like GPT-4o, Claude, etc.
        """
        return {
            "id": f"agent:{self.key}",  # Prefix with "agent:" to distinguish from models
            "name": self.name,
            "description": self.description,
            "provider": "AgentHub",
            "type": "agent",
            "capabilities": [cap.value for cap in self.capabilities],
            "icon": self.icon or "🤖",
            "color": self.color or "#6366f1",
            "version": self.version,
            "metadata": {
                "agent_type": self.agent_type.value,
                "use_kb": self.use_knowledge_base,
                "tags": self.tags,
            }
        }
