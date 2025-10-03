"""
External Agent Service Layer
Business logic for agent management
"""
import httpx
import json
from sqlalchemy.orm import Session
from typing import Optional

from onyx.server.features.agenthub.external_agent import ExternalAgent
from onyx.utils.logger import setup_logger


logger = setup_logger()


def create_external_agent(
    db_session: Session,
    agent_data: any,  # ExternalAgentCreate from router
) -> ExternalAgent:
    """
    Create a new external agent
    """
    # Check if agent with same name exists
    existing = db_session.query(ExternalAgent).filter(
        ExternalAgent.name == agent_data.name
    ).first()
    
    if existing:
        raise ValueError(f"Agent with name '{agent_data.name}' already exists")
    
    agent = ExternalAgent(
        name=agent_data.name,
        description=agent_data.description,
        api_endpoint=agent_data.api_endpoint,
        api_key=agent_data.api_key,  # TODO: Encrypt this
        auth_type=agent_data.auth_type,
        default_model=agent_data.default_model,
        default_temperature=agent_data.default_temperature,
        default_max_tokens=agent_data.default_max_tokens,
        supports_streaming=agent_data.supports_streaming,
        system_prompt=agent_data.system_prompt,
        additional_params=agent_data.additional_params,
        icon_color=agent_data.icon_color,
        icon_emoji=agent_data.icon_emoji,
    )
    
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)
    
    logger.info(f"Created external agent: {agent.name} (ID: {agent.id})")
    return agent


def get_all_external_agents(
    db_session: Session,
    include_inactive: bool = False,
) -> list[ExternalAgent]:
    """
    Get all external agents
    """
    query = db_session.query(ExternalAgent)
    
    if not include_inactive:
        query = query.filter(ExternalAgent.is_active == True)
    
    return query.order_by(ExternalAgent.name).all()


def get_external_agent_by_id(
    db_session: Session,
    agent_id: int,
) -> Optional[ExternalAgent]:
    """
    Get an agent by ID
    """
    return db_session.query(ExternalAgent).filter(
        ExternalAgent.id == agent_id
    ).first()


def update_external_agent(
    db_session: Session,
    agent_id: int,
    agent_data: any,  # ExternalAgentUpdate from router
) -> Optional[ExternalAgent]:
    """
    Update an existing agent
    """
    agent = get_external_agent_by_id(db_session, agent_id)
    
    if not agent:
        return None
    
    # Update fields if provided
    update_data = agent_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent, field, value)
    
    db_session.commit()
    db_session.refresh(agent)
    
    logger.info(f"Updated external agent: {agent.name} (ID: {agent.id})")
    return agent


def delete_external_agent(
    db_session: Session,
    agent_id: int,
) -> bool:
    """
    Delete an agent (soft delete by setting is_active=False)
    """
    agent = get_external_agent_by_id(db_session, agent_id)
    
    if not agent:
        return False
    
    # Soft delete
    agent.is_active = False
    db_session.commit()
    
    logger.info(f"Deleted external agent: {agent.name} (ID: {agent.id})")
    return True


async def test_agent_connection(
    db_session: Session,
    agent_id: int,
    test_message: str = "Hello, test connection",
) -> dict:
    """
    Test connection to an external agent by sending a test message
    """
    agent = get_external_agent_by_id(db_session, agent_id)
    
    if not agent:
        return {
            "success": False,
            "message": "Agent not found",
            "error": "Agent ID does not exist"
        }
    
    # Prepare request in OpenAI format
    headers = {
        "Content-Type": "application/json",
    }
    
    # Add authentication
    if agent.auth_type == "bearer" and agent.api_key:
        headers["Authorization"] = f"Bearer {agent.api_key}"
    elif agent.auth_type == "api_key" and agent.api_key:
        headers["X-API-Key"] = agent.api_key
    
    # Build request body in OpenAI format
    messages = []
    if agent.system_prompt:
        messages.append({"role": "system", "content": agent.system_prompt})
    messages.append({"role": "user", "content": test_message})
    
    request_body = {
        "model": agent.default_model,
        "messages": messages,
        "temperature": agent.default_temperature,
        "max_tokens": agent.default_max_tokens,
        "stream": False,  # No streaming for test
    }
    
    # Merge additional params
    if agent.additional_params:
        request_body.update(agent.additional_params)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                agent.api_endpoint,
                headers=headers,
                json=request_body,
            )
            
            response.raise_for_status()
            
            response_data = response.json()
            
            # Extract response preview (OpenAI format)
            response_preview = None
            if "choices" in response_data and len(response_data["choices"]) > 0:
                choice = response_data["choices"][0]
                if "message" in choice:
                    response_preview = choice["message"].get("content", "")
            
            # Update test status
            agent.last_test_status = "success"
            agent.last_test_error = None
            db_session.commit()
            
            logger.info(f"Test connection successful for agent: {agent.name}")
            
            return {
                "success": True,
                "message": "Connection successful",
                "response_preview": response_preview[:200] if response_preview else None,
            }
            
    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
        agent.last_test_status = "failed"
        agent.last_test_error = error_msg
        db_session.commit()
        
        logger.error(f"Test connection failed for agent {agent.name}: {error_msg}")
        
        return {
            "success": False,
            "message": "Connection failed",
            "error": error_msg,
        }
    
    except Exception as e:
        error_msg = str(e)
        agent.last_test_status = "failed"
        agent.last_test_error = error_msg
        db_session.commit()
        
        logger.error(f"Test connection error for agent {agent.name}: {error_msg}")
        
        return {
            "success": False,
            "message": "Connection error",
            "error": error_msg,
        }
