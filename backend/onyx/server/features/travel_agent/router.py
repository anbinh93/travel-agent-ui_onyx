"""
Travel Agent API Router
Provides chat endpoints for travel planning
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

from onyx.auth.users import current_user
from onyx.db.models import User
from onyx.server.features.travel_agent.service import (
    get_travel_agent_service,
    ChatMessage
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/travel-agent", tags=["travel-agent"])


class ChatRequest(BaseModel):
    """Chat request model"""
    messages: List[ChatMessage] = Field(..., description="Chat message history")
    temperature: float = Field(default=0.7, ge=0, le=1, description="Model temperature")
    max_tokens: int = Field(default=2000, gt=0, le=4000, description="Maximum tokens")
    stream: bool = Field(default=False, description="Stream response")


class ChatResponse(BaseModel):
    """Chat response model"""
    message: str
    status: str = "success"


class StatusResponse(BaseModel):
    """Status response"""
    enabled: bool
    api_configured: bool
    message: str


@router.get("/status", response_model=StatusResponse)
async def get_status(_user: User | None = Depends(current_user)):
    """
    Check if Travel Agent is enabled and configured
    """
    try:
        service = get_travel_agent_service()
        return StatusResponse(
            enabled=True,
            api_configured=bool(service.api_key),
            message="Travel Agent is ready"
        )
    except ValueError as e:
        return StatusResponse(
            enabled=False,
            api_configured=False,
            message=str(e)
        )
    except Exception as e:
        logger.error(f"Status check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    _user: User | None = Depends(current_user)
):
    """
    Send a chat message to Travel Agent (non-streaming)
    
    **Example Request:**
    ```json
    {
        "messages": [
            {"role": "user", "content": "I want to visit Tokyo for 5 days"},
            {"role": "assistant", "content": "Great choice! Let me help..."},
            {"role": "user", "content": "What's the best time to visit?"}
        ],
        "temperature": 0.7,
        "max_tokens": 2000
    }
    ```
    """
    try:
        service = get_travel_agent_service()
        
        response_text = await service.chat(
            messages=request.messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return ChatResponse(
            message=response_text,
            status="success"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    _user: User | None = Depends(current_user)
):
    """
    Send a chat message to Travel Agent (streaming)
    
    Returns Server-Sent Events (SSE) stream
    """
    try:
        service = get_travel_agent_service()
        
        async def generate():
            try:
                async for chunk in service.chat_stream(
                    messages=request.messages,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens
                ):
                    yield f"data: {chunk}\n\n"
                
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                logger.error(f"Stream error: {e}")
                yield f"data: Error: {str(e)}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Stream setup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
