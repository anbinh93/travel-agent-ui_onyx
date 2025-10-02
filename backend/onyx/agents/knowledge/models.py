"""Knowledge Base models for AgentHub."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class KnowledgeSourceType(str, Enum):
    """Types of knowledge sources."""
    NOTION = "notion"
    SLACK = "slack"
    GOOGLE_DRIVE = "google_drive"
    CONFLUENCE = "confluence"
    GITHUB = "github"
    WEB_SCRAPER = "web_scraper"
    CUSTOM = "custom"


class KnowledgeStatus(str, Enum):
    """Status of knowledge base."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SYNCING = "syncing"
    ERROR = "error"


class KnowledgeVersion(BaseModel):
    """Represents a version of knowledge base."""
    version: str = Field(..., description="Semantic version (e.g., v1.0.0)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    document_count: int = Field(default=0)
    total_size_bytes: int = Field(default=0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    checksum: Optional[str] = Field(None, description="Content hash for integrity")


class ConnectorConfig(BaseModel):
    """Configuration for a connector feeding into knowledge base."""
    connector_id: UUID = Field(default_factory=uuid4)
    connector_type: KnowledgeSourceType
    name: str
    enabled: bool = True
    
    # Connector-specific settings
    config: dict[str, Any] = Field(default_factory=dict)
    
    # Sync settings
    auto_sync: bool = True
    sync_interval_minutes: int = 60
    last_sync_at: Optional[datetime] = None
    next_sync_at: Optional[datetime] = None
    
    # Monitoring
    total_syncs: int = 0
    failed_syncs: int = 0
    last_error: Optional[str] = None


class KnowledgeBase(BaseModel):
    """Knowledge Base associated with agents."""
    kb_id: UUID = Field(default_factory=uuid4)
    name: str
    description: str = ""
    
    # Status & Enable/Disable
    status: KnowledgeStatus = KnowledgeStatus.ACTIVE
    enabled: bool = True
    
    # Versioning
    current_version: str = "v1.0.0"
    versions: list[KnowledgeVersion] = Field(default_factory=list)
    
    # Connectors feeding this KB
    connectors: list[ConnectorConfig] = Field(default_factory=list)
    
    # Agent associations
    agent_keys: list[str] = Field(default_factory=list, description="Agents using this KB")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    
    # Monitoring
    query_count: int = 0
    last_queried_at: Optional[datetime] = None

    def add_connector(self, connector: ConnectorConfig) -> None:
        """Add a connector to this knowledge base."""
        self.connectors.append(connector)
        self.updated_at = datetime.utcnow()
    
    def remove_connector(self, connector_id: UUID) -> bool:
        """Remove a connector by ID."""
        original_count = len(self.connectors)
        self.connectors = [c for c in self.connectors if c.connector_id != connector_id]
        if len(self.connectors) < original_count:
            self.updated_at = datetime.utcnow()
            return True
        return False
    
    def create_version(self, document_count: int, total_size_bytes: int, metadata: dict[str, Any] | None = None) -> KnowledgeVersion:
        """Create a new version of the knowledge base."""
        import hashlib
        from packaging import version
        
        # Parse current version and increment
        current = version.parse(self.current_version.lstrip('v'))
        new_version_num = f"v{current.major}.{current.minor}.{current.micro + 1}"
        
        # Create checksum
        content_str = f"{document_count}:{total_size_bytes}:{datetime.utcnow().isoformat()}"
        checksum = hashlib.sha256(content_str.encode()).hexdigest()
        
        new_version = KnowledgeVersion(
            version=new_version_num,
            document_count=document_count,
            total_size_bytes=total_size_bytes,
            metadata=metadata or {},
            checksum=checksum
        )
        
        self.versions.append(new_version)
        self.current_version = new_version_num
        self.updated_at = datetime.utcnow()
        
        return new_version
    
    def rollback_version(self, target_version: str) -> bool:
        """Rollback to a specific version."""
        if any(v.version == target_version for v in self.versions):
            self.current_version = target_version
            self.updated_at = datetime.utcnow()
            return True
        return False
    
    def enable(self) -> None:
        """Enable this knowledge base."""
        self.enabled = True
        self.status = KnowledgeStatus.ACTIVE
        self.updated_at = datetime.utcnow()
    
    def disable(self) -> None:
        """Disable this knowledge base."""
        self.enabled = False
        self.status = KnowledgeStatus.INACTIVE
        self.updated_at = datetime.utcnow()
    
    def get_active_connectors(self) -> list[ConnectorConfig]:
        """Get all enabled connectors."""
        return [c for c in self.connectors if c.enabled]
    
    def record_query(self) -> None:
        """Record that this KB was queried."""
        self.query_count += 1
        self.last_queried_at = datetime.utcnow()


class KnowledgeBaseUsageMetrics(BaseModel):
    """Metrics for knowledge base usage and monitoring."""
    kb_id: UUID
    period_start: datetime
    period_end: datetime
    
    # Query metrics
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    avg_query_latency_ms: float = 0.0
    
    # Sync metrics
    total_syncs: int = 0
    successful_syncs: int = 0
    failed_syncs: int = 0
    
    # Data metrics
    documents_added: int = 0
    documents_updated: int = 0
    documents_deleted: int = 0
    bytes_processed: int = 0
    
    # Agent usage
    agents_using: list[str] = Field(default_factory=list)
