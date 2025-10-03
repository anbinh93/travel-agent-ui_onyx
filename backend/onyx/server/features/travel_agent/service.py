"""
Travel Agent Service - Integrated with Chat
Uses Google Gemini API for chat completion
"""

import os
from typing import Optional, List, Dict, Any, AsyncGenerator
import google.generativeai as genai
from pydantic import BaseModel


class ChatMessage(BaseModel):
    """Chat message format"""
    role: str  # "user" or "assistant"
    content: str


class TravelAgentService:
    """Travel Agent chat service using Google Gemini"""
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro-latest')
        
        # System prompt for travel agent
        self.system_prompt = """You are a professional travel planning assistant. 
You help users plan their trips by providing:
- Destination recommendations
- Itinerary planning
- Budget estimation
- Activity suggestions
- Local tips and advice

Always be helpful, informative, and enthusiastic about travel!"""
    
    async def chat(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """
        Send chat messages to Google Gemini and get response
        
        Args:
            messages: List of chat messages (history + current)
            temperature: Model temperature (0-1)
            max_tokens: Maximum tokens in response
            
        Returns:
            Response text from the model
        """
        try:
            # Convert messages to Gemini format
            # Gemini uses a conversation history format
            chat_history = []
            user_message = None
            
            for msg in messages:
                if msg.role == "user":
                    user_message = msg.content
                elif msg.role == "assistant":
                    chat_history.append({
                        "role": "model",
                        "parts": [msg.content]
                    })
            
            # Start chat with history
            chat = self.model.start_chat(history=chat_history)
            
            # Generate response
            response = chat.send_message(
                user_message or "Hello",
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                )
            )
            
            return response.text
            
        except Exception as e:
            raise Exception(f"Travel Agent error: {str(e)}")
    
    async def chat_stream(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat response from Google Gemini
        
        Args:
            messages: List of chat messages
            temperature: Model temperature
            max_tokens: Maximum tokens
            
        Yields:
            Chunks of response text
        """
        try:
            # Convert messages
            chat_history = []
            user_message = None
            
            for msg in messages:
                if msg.role == "user":
                    user_message = msg.content
                elif msg.role == "assistant":
                    chat_history.append({
                        "role": "model",
                        "parts": [msg.content]
                    })
            
            # Start chat
            chat = self.model.start_chat(history=chat_history)
            
            # Stream response
            response = chat.send_message(
                user_message or "Hello",
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
                stream=True
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            yield f"Error: {str(e)}"


# Global instance
_travel_agent_service: Optional[TravelAgentService] = None


def get_travel_agent_service() -> TravelAgentService:
    """Get or create Travel Agent service instance"""
    global _travel_agent_service
    
    if _travel_agent_service is None:
        _travel_agent_service = TravelAgentService()
    
    return _travel_agent_service
