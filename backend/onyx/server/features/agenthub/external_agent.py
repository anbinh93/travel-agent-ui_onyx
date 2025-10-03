"""
External Agent Models
Stores n8n-wrapped agents with OpenAI-compatible API format
"""
from sqlalchemy import Boolean, String, Text, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column

from onyx.db.models import Base


class ExternalAgent(Base):
    """
    External agents (e.g., n8n workflows) that follow OpenAI API format
    Organization-wide, accessible to all users
    """
    
    __tablename__ = "external_agent"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Agent identification
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # API configuration
    api_endpoint: Mapped[str] = mapped_column(String, nullable=False)
    api_key: Mapped[str | None] = mapped_column(String, nullable=True)  # Encrypted
    auth_type: Mapped[str] = mapped_column(String, default="bearer")  # bearer, api_key, none
    
    # OpenAI-compatible settings (defaults)
    default_model: Mapped[str] = mapped_column(String, default="gpt-4o")
    default_temperature: Mapped[float] = mapped_column(default=1.0)
    default_max_tokens: Mapped[int] = mapped_column(Integer, default=4096)
    supports_streaming: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # System prompt
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Additional OpenAI parameters as JSON
    additional_params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    # UI customization
    icon_color: Mapped[str | None] = mapped_column(String, nullable=True)  # Hex color
    icon_emoji: Mapped[str | None] = mapped_column(String, nullable=True)  # Emoji
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Test connection result
    last_test_status: Mapped[str | None] = mapped_column(String, nullable=True)  # success, failed
    last_test_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    def __repr__(self) -> str:
        return f"<ExternalAgent(id={self.id}, name='{self.name}', endpoint='{self.api_endpoint}')>"
