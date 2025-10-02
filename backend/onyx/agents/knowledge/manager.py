"""Knowledge Base Manager - handles KB lifecycle and connector integration."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from onyx.agents.knowledge.models import (
    KnowledgeBase,
    KnowledgeVersion,
    ConnectorConfig,
    KnowledgeSourceType,
    KnowledgeStatus,
    KnowledgeBaseUsageMetrics,
)


class KnowledgeBaseManager:
    """
    Manages knowledge bases, versioning, and connector integration.
    
    Responsibilities:
    - CRUD operations for knowledge bases
    - Version management and rollback
    - Connector lifecycle (add, remove, sync)
    - Monitoring and metrics
    - Enable/disable knowledge bases
    """
    
    def __init__(self):
        # In-memory storage - replace with database in production
        self._knowledge_bases: dict[UUID, KnowledgeBase] = {}
        self._metrics: dict[UUID, list[KnowledgeBaseUsageMetrics]] = {}
    
    # ==================== CRUD Operations ====================
    
    def create_knowledge_base(
        self,
        name: str,
        description: str = "",
        agent_keys: list[str] | None = None,
        created_by: str | None = None,
    ) -> KnowledgeBase:
        """Create a new knowledge base."""
        kb = KnowledgeBase(
            name=name,
            description=description,
            agent_keys=agent_keys or [],
            created_by=created_by,
        )
        
        # Create initial version
        kb.create_version(
            document_count=0,
            total_size_bytes=0,
            metadata={"initial": True}
        )
        
        self._knowledge_bases[kb.kb_id] = kb
        return kb
    
    def get_knowledge_base(self, kb_id: UUID) -> Optional[KnowledgeBase]:
        """Get a knowledge base by ID."""
        return self._knowledge_bases.get(kb_id)
    
    def list_knowledge_bases(
        self,
        agent_key: str | None = None,
        enabled_only: bool = False,
    ) -> list[KnowledgeBase]:
        """List all knowledge bases, optionally filtered."""
        kbs = list(self._knowledge_bases.values())
        
        if agent_key:
            kbs = [kb for kb in kbs if agent_key in kb.agent_keys]
        
        if enabled_only:
            kbs = [kb for kb in kbs if kb.enabled]
        
        return kbs
    
    def update_knowledge_base(
        self,
        kb_id: UUID,
        name: str | None = None,
        description: str | None = None,
        agent_keys: list[str] | None = None,
    ) -> Optional[KnowledgeBase]:
        """Update knowledge base metadata."""
        kb = self.get_knowledge_base(kb_id)
        if not kb:
            return None
        
        if name is not None:
            kb.name = name
        if description is not None:
            kb.description = description
        if agent_keys is not None:
            kb.agent_keys = agent_keys
        
        kb.updated_at = datetime.utcnow()
        return kb
    
    def delete_knowledge_base(self, kb_id: UUID) -> bool:
        """Delete a knowledge base."""
        if kb_id in self._knowledge_bases:
            del self._knowledge_bases[kb_id]
            if kb_id in self._metrics:
                del self._metrics[kb_id]
            return True
        return False
    
    # ==================== Enable/Disable ====================
    
    def enable_knowledge_base(self, kb_id: UUID) -> bool:
        """Enable a knowledge base."""
        kb = self.get_knowledge_base(kb_id)
        if kb:
            kb.enable()
            return True
        return False
    
    def disable_knowledge_base(self, kb_id: UUID) -> bool:
        """Disable a knowledge base."""
        kb = self.get_knowledge_base(kb_id)
        if kb:
            kb.disable()
            return True
        return False
    
    # ==================== Versioning ====================
    
    def create_version(
        self,
        kb_id: UUID,
        document_count: int,
        total_size_bytes: int,
        metadata: dict | None = None,
    ) -> Optional[KnowledgeVersion]:
        """Create a new version of the knowledge base."""
        kb = self.get_knowledge_base(kb_id)
        if not kb:
            return None
        
        return kb.create_version(document_count, total_size_bytes, metadata)
    
    def rollback_version(self, kb_id: UUID, target_version: str) -> bool:
        """Rollback to a specific version."""
        kb = self.get_knowledge_base(kb_id)
        if not kb:
            return False
        
        return kb.rollback_version(target_version)
    
    def get_versions(self, kb_id: UUID) -> list[KnowledgeVersion]:
        """Get all versions of a knowledge base."""
        kb = self.get_knowledge_base(kb_id)
        return kb.versions if kb else []
    
    # ==================== Connector Management ====================
    
    def add_connector(
        self,
        kb_id: UUID,
        connector_type: KnowledgeSourceType,
        name: str,
        config: dict,
        auto_sync: bool = True,
        sync_interval_minutes: int = 60,
    ) -> Optional[ConnectorConfig]:
        """Add a connector to a knowledge base."""
        kb = self.get_knowledge_base(kb_id)
        if not kb:
            return None
        
        connector = ConnectorConfig(
            connector_type=connector_type,
            name=name,
            config=config,
            auto_sync=auto_sync,
            sync_interval_minutes=sync_interval_minutes,
            next_sync_at=datetime.utcnow() + timedelta(minutes=sync_interval_minutes) if auto_sync else None,
        )
        
        kb.add_connector(connector)
        return connector
    
    def remove_connector(self, kb_id: UUID, connector_id: UUID) -> bool:
        """Remove a connector from a knowledge base."""
        kb = self.get_knowledge_base(kb_id)
        if not kb:
            return False
        
        return kb.remove_connector(connector_id)
    
    def enable_connector(self, kb_id: UUID, connector_id: UUID) -> bool:
        """Enable a connector."""
        kb = self.get_knowledge_base(kb_id)
        if not kb:
            return False
        
        for connector in kb.connectors:
            if connector.connector_id == connector_id:
                connector.enabled = True
                kb.updated_at = datetime.utcnow()
                return True
        return False
    
    def disable_connector(self, kb_id: UUID, connector_id: UUID) -> bool:
        """Disable a connector."""
        kb = self.get_knowledge_base(kb_id)
        if not kb:
            return False
        
        for connector in kb.connectors:
            if connector.connector_id == connector_id:
                connector.enabled = False
                kb.updated_at = datetime.utcnow()
                return True
        return False
    
    def trigger_sync(self, kb_id: UUID, connector_id: UUID | None = None) -> bool:
        """
        Manually trigger a sync for a connector or all connectors.
        
        Args:
            kb_id: Knowledge base ID
            connector_id: Specific connector to sync, or None for all
        
        Returns:
            True if sync was triggered successfully
        """
        kb = self.get_knowledge_base(kb_id)
        if not kb:
            return False
        
        kb.status = KnowledgeStatus.SYNCING
        
        connectors_to_sync = []
        if connector_id:
            connectors_to_sync = [c for c in kb.connectors if c.connector_id == connector_id and c.enabled]
        else:
            connectors_to_sync = kb.get_active_connectors()
        
        if not connectors_to_sync:
            kb.status = KnowledgeStatus.ACTIVE
            return False
        
        # TODO: Implement actual sync logic with connectors
        # For now, just update sync metadata
        for connector in connectors_to_sync:
            connector.last_sync_at = datetime.utcnow()
            connector.total_syncs += 1
            if connector.auto_sync:
                connector.next_sync_at = datetime.utcnow() + timedelta(minutes=connector.sync_interval_minutes)
        
        kb.status = KnowledgeStatus.ACTIVE
        kb.updated_at = datetime.utcnow()
        return True
    
    def get_connectors_due_for_sync(self) -> list[tuple[UUID, UUID]]:
        """Get all connectors that are due for sync."""
        due_syncs = []
        now = datetime.utcnow()
        
        for kb in self._knowledge_bases.values():
            if not kb.enabled:
                continue
            
            for connector in kb.get_active_connectors():
                if connector.auto_sync and connector.next_sync_at and connector.next_sync_at <= now:
                    due_syncs.append((kb.kb_id, connector.connector_id))
        
        return due_syncs
    
    # ==================== Monitoring & Metrics ====================
    
    def record_query(self, kb_id: UUID, success: bool, latency_ms: float) -> None:
        """Record a query to the knowledge base."""
        kb = self.get_knowledge_base(kb_id)
        if not kb:
            return
        
        kb.record_query()
        
        # Update current period metrics
        # TODO: Implement proper time-series metrics storage
    
    def get_metrics(
        self,
        kb_id: UUID,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
    ) -> Optional[KnowledgeBaseUsageMetrics]:
        """Get usage metrics for a knowledge base."""
        if kb_id not in self._metrics or not self._metrics[kb_id]:
            return None
        
        # Filter metrics by time period if specified
        metrics = self._metrics[kb_id]
        if period_start:
            metrics = [m for m in metrics if m.period_start >= period_start]
        if period_end:
            metrics = [m for m in metrics if m.period_end <= period_end]
        
        # Return most recent metrics
        return metrics[-1] if metrics else None
    
    def get_knowledge_bases_for_agent(self, agent_key: str) -> list[KnowledgeBase]:
        """Get all enabled knowledge bases associated with an agent."""
        return [
            kb for kb in self._knowledge_bases.values()
            if agent_key in kb.agent_keys and kb.enabled
        ]


# Global singleton instance
_kb_manager: Optional[KnowledgeBaseManager] = None


def get_knowledge_base_manager() -> KnowledgeBaseManager:
    """Get the global KnowledgeBaseManager instance."""
    global _kb_manager
    if _kb_manager is None:
        _kb_manager = KnowledgeBaseManager()
    return _kb_manager
