from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from onyx.agents.base import (
    AgentDefinition,
    AgentRunner,
    AgentType,
    AgentCapability,
    TriggerType,
)
from onyx.agents.knowledge.manager import get_knowledge_base_manager


_AGENT_REGISTRY: dict[str, AgentDefinition] = {}


class AgentRegistry:
    """
    Agent Registry - like a Model Registry for LLMs.
    
    Manages agents that can be selected in the chat UI alongside models.
    Each agent is wrapped as an API and can be invoked with queries.
    """
    
    def __init__(self):
        self._registry = _AGENT_REGISTRY
        self._kb_manager = get_knowledge_base_manager()
    
    def register(self, agent: AgentDefinition) -> None:
        """
        Register an agent in the hub.
        Like registering a model in model registry.
        """
        if agent.key in self._registry:
            raise ValueError(f"Agent with key '{agent.key}' is already registered")
        
        # Validate knowledge base IDs if specified
        if agent.use_knowledge_base and agent.knowledge_base_ids:
            for kb_id in agent.knowledge_base_ids:
                kb = self._kb_manager.get_knowledge_base(kb_id)
                if not kb:
                    raise ValueError(f"Knowledge base {kb_id} not found")
                if not kb.enabled:
                    raise ValueError(f"Knowledge base {kb_id} is disabled")
        
        self._registry[agent.key] = agent
    
    def unregister(self, agent_key: str) -> bool:
        """Unregister an agent."""
        if agent_key in self._registry:
            del self._registry[agent_key]
            return True
        return False
    
    def get(self, agent_key: str) -> Optional[AgentDefinition]:
        """Get an agent definition by key."""
        return self._registry.get(agent_key)
    
    def get_runner(self, agent_key: str) -> AgentRunner:
        """
        Get the runner function for an agent.
        This is called when executing the agent.
        """
        try:
            return self._registry[agent_key].runner
        except KeyError as exc:
            raise ValueError(f"Unknown agent: {agent_key}") from exc
    
    def list_all(
        self,
        agent_type: AgentType | None = None,
        capability: AgentCapability | None = None,
        tag: str | None = None,
    ) -> list[AgentDefinition]:
        """List all agents with optional filtering."""
        agents = list(self._registry.values())
        
        if agent_type:
            agents = [a for a in agents if a.agent_type == agent_type]
        
        if capability:
            agents = [a for a in agents if capability in a.capabilities]
        
        if tag:
            agents = [a for a in agents if tag in a.tags]
        
        return agents
    
    def list_for_model_selector(self) -> list[dict[str, Any]]:
        """
        List agents in format compatible with model selector UI.
        This allows agents to appear alongside GPT-4o, Claude, etc.
        """
        return [agent.to_model_selector_format() for agent in self._registry.values()]
    
    def list_metadata(self) -> list[dict[str, Any]]:
        """List all agent metadata."""
        return [agent.to_metadata() for agent in self._registry.values()]
    
    def get_agents_with_trigger(self, trigger_type: TriggerType) -> list[AgentDefinition]:
        """Get all agents that have a specific trigger type enabled."""
        agents = []
        for agent in self._registry.values():
            for trigger in agent.triggers:
                if trigger.trigger_type == trigger_type and trigger.enabled:
                    agents.append(agent)
                    break
        return agents
    
    def get_agents_for_knowledge_base(self, kb_id: UUID) -> list[AgentDefinition]:
        """Get all agents using a specific knowledge base."""
        return [
            agent for agent in self._registry.values()
            if agent.use_knowledge_base and kb_id in agent.knowledge_base_ids
        ]
    
    def execute_agent(
        self,
        agent_key: str,
        query: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Execute an agent with a query.
        
        Args:
            agent_key: The agent to execute
            query: The user query
            context: Additional context (user info, chat history, etc.)
        
        Returns:
            Agent result with answer, sources, metadata
        """
        agent = self.get(agent_key)
        if not agent:
            raise ValueError(f"Unknown agent: {agent_key}")
        
        # Prepare context
        exec_context = context or {}
        
        # Add knowledge base context if enabled
        if agent.use_knowledge_base and agent.knowledge_base_ids:
            exec_context["knowledge_bases"] = [
                self._kb_manager.get_knowledge_base(kb_id)
                for kb_id in agent.knowledge_base_ids
            ]
        
        # Execute the agent
        start_time = datetime.utcnow()
        try:
            result = agent.runner(query, exec_context)
            
            # Add execution metadata
            result["metadata"] = result.get("metadata", {})
            result["metadata"]["agent_key"] = agent_key
            result["metadata"]["agent_name"] = agent.name
            result["metadata"]["version"] = agent.version
            result["metadata"]["execution_time_ms"] = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Record KB queries if used
            if agent.use_knowledge_base and agent.knowledge_base_ids:
                for kb_id in agent.knowledge_base_ids:
                    latency = (datetime.utcnow() - start_time).total_seconds() * 1000
                    self._kb_manager.record_query(kb_id, success=True, latency_ms=latency)
            
            return result
            
        except Exception as e:
            # Record failures
            if agent.use_knowledge_base and agent.knowledge_base_ids:
                for kb_id in agent.knowledge_base_ids:
                    latency = (datetime.utcnow() - start_time).total_seconds() * 1000
                    self._kb_manager.record_query(kb_id, success=False, latency_ms=latency)
            
            raise


# Global singleton
_agent_registry: Optional[AgentRegistry] = None


def get_agent_registry() -> AgentRegistry:
    """Get the global AgentRegistry instance."""
    global _agent_registry
    if _agent_registry is None:
        _agent_registry = AgentRegistry()
    return _agent_registry


# Backward compatibility functions
def register_agent(agent: AgentDefinition) -> None:
    """Register an agent for use within AgentHub."""
    get_agent_registry().register(agent)


def get_agent_runner(agent_key: str) -> AgentRunner:
    return get_agent_registry().get_runner(agent_key)


def list_agents() -> list[dict[str, Any]]:
    return get_agent_registry().list_metadata()


# Import built-in agents for side-effect registration
from onyx.agents.travel import travel_agent as _travel_agent_module  # noqa: E402,F401



