# Travel Planning Agent Example

A standalone travel planning agent that uses Google Gemini API and Tavily search to help plan trips.

## Features

- Trip planning for any destination
- Budget-conscious recommendations
- Multi-day itinerary generation
- Real-time web search for current information
- Accommodation and activity suggestions

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your API keys:
# - GOOGLE_API_KEY (for Gemini)
# - TAVILY_API_KEY (for web search)
```

3. Run the agent:
```bash
python travel_agent.py
```

## Usage

### Interactive Mode
```bash
python travel_agent.py
```

### API Mode
```bash
python travel_agent_api.py
```

Then send requests:
```bash
curl -X POST http://localhost:8000/plan \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "Da Nang, Vietnam",
    "days": 3,
    "budget": 10000000,
    "preferences": ["beach", "food", "culture"]
  }'
```

## Configuration

Edit `config.yaml` to customize:
- Default model settings
- Search preferences
- Budget ranges
- Activity categories

## Example Queries

- "I want to visit Da Nang Vietnam for 3 days, budget 10 million VND"
- "Plan a week-long trip to Tokyo for two people, budget $3000"
- "Suggest a romantic weekend getaway in Paris under €1000"
