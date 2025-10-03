"""
Travel Planning Agent - REST API
FastAPI server for the travel agent
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
import uvicorn
from travel_agent import TravelAgent

app = FastAPI(
    title="Travel Planning Agent API",
    description="AI-powered travel planning with web search",
    version="1.0.0"
)

# Initialize agent
agent = TravelAgent()


class TripRequest(BaseModel):
    """Trip planning request"""
    destination: str = Field(..., description="Destination city or country")
    days: int = Field(..., gt=0, description="Number of days")
    budget: float = Field(..., gt=0, description="Budget amount")
    currency: str = Field(default="VND", description="Currency code (VND, USD, EUR, etc.)")
    preferences: Optional[List[str]] = Field(default=None, description="Travel preferences")


class TripResponse(BaseModel):
    """Trip planning response"""
    status: str
    destination: str
    days: int
    budget: float
    currency: str
    plan: str


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Travel Planning Agent API",
        "version": "1.0.0",
        "endpoints": {
            "plan_trip": "POST /api/plan-trip",
            "health": "GET /health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/api/plan-trip", response_model=TripResponse)
async def plan_trip(request: TripRequest):
    """
    Plan a trip based on user requirements
    
    **Example Request:**
    ```json
    {
        "destination": "Tokyo",
        "days": 5,
        "budget": 50000000,
        "currency": "VND",
        "preferences": ["culture", "food", "shopping"]
    }
    ```
    """
    try:
        plan = agent.plan_trip(
            destination=request.destination,
            days=request.days,
            budget=request.budget,
            currency=request.currency,
            preferences=request.preferences
        )
        
        return TripResponse(
            status="success",
            destination=request.destination,
            days=request.days,
            budget=request.budget,
            currency=request.currency,
            plan=plan
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    print("Starting Travel Planning Agent API...")
    print("API documentation: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
