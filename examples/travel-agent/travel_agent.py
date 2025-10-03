"""
Travel Planning Agent - Standalone Example
Uses Google Gemini and Tavily search to plan trips
"""

import os
from typing import Optional, List, Dict, Any
import google.generativeai as genai
from tavily import TavilyClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize APIs
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")
if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY not found in environment variables")

genai.configure(api_key=GOOGLE_API_KEY)
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)


class TravelAgent:
    """Travel planning agent with web search capabilities"""
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-pro')
        self.search_client = tavily_client
        
    def search_destination_info(self, destination: str, query_type: str = "general") -> List[Dict]:
        """Search for destination information"""
        search_queries = {
            "general": f"travel guide {destination} attractions activities",
            "accommodation": f"hotels accommodation {destination} recommendations",
            "food": f"best restaurants food {destination}",
            "budget": f"travel costs budget {destination}",
            "culture": f"culture customs traditions {destination}"
        }
        
        query = search_queries.get(query_type, search_queries["general"])
        
        try:
            results = self.search_client.search(
                query=query,
                max_results=5,
                search_depth="advanced"
            )
            return results.get('results', [])
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def plan_trip(
        self,
        destination: str,
        days: int,
        budget: float,
        currency: str = "VND",
        preferences: Optional[List[str]] = None
    ) -> str:
        """Plan a trip based on user requirements"""
        
        # Search for destination information
        print(f"🔍 Searching for information about {destination}...")
        
        general_info = self.search_destination_info(destination, "general")
        accommodation_info = self.search_destination_info(destination, "accommodation")
        food_info = self.search_destination_info(destination, "food")
        
        # Build context from search results
        search_context = self._build_search_context({
            "general": general_info,
            "accommodation": accommodation_info,
            "food": food_info
        })
        
        # Build prompt for Gemini
        prompt = self._build_trip_prompt(
            destination=destination,
            days=days,
            budget=budget,
            currency=currency,
            preferences=preferences or [],
            search_context=search_context
        )
        
        print(f"🤖 Generating travel plan...")
        
        # Generate plan with Gemini
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating plan: {str(e)}"
    
    def _build_search_context(self, search_results: Dict[str, List[Dict]]) -> str:
        """Build context from search results"""
        context_parts = []
        
        for category, results in search_results.items():
            if results:
                context_parts.append(f"\n## {category.title()} Information:")
                for idx, result in enumerate(results[:3], 1):
                    title = result.get('title', 'N/A')
                    content = result.get('content', '')
                    url = result.get('url', '')
                    context_parts.append(
                        f"\n{idx}. {title}\n"
                        f"   {content[:200]}...\n"
                        f"   Source: {url}"
                    )
        
        return "\n".join(context_parts)
    
    def _build_trip_prompt(
        self,
        destination: str,
        days: int,
        budget: float,
        currency: str,
        preferences: List[str],
        search_context: str
    ) -> str:
        """Build prompt for trip planning"""
        
        preferences_str = ", ".join(preferences) if preferences else "general sightseeing"
        
        prompt = f"""You are an expert travel planner. Plan a detailed {days}-day trip to {destination}.

**User Requirements:**
- Destination: {destination}
- Duration: {days} days
- Budget: {budget:,.0f} {currency}
- Preferences: {preferences_str}

**Current Information (from web search):**
{search_context}

**Please provide:**

1. **Trip Overview**
   - Best time to visit
   - Brief destination highlights
   - Budget breakdown estimate

2. **Day-by-Day Itinerary**
   For each day, include:
   - Morning activities
   - Afternoon activities
   - Evening activities
   - Estimated costs
   - Transportation tips

3. **Accommodation Recommendations**
   - 3-4 options at different price points
   - Location advantages
   - Estimated costs per night

4. **Food & Dining**
   - Must-try local dishes
   - Restaurant recommendations
   - Street food options
   - Estimated meal costs

5. **Practical Tips**
   - Transportation options
   - Money-saving tips
   - Cultural etiquette
   - Safety considerations

6. **Estimated Total Budget**
   - Accommodation
   - Food & drinks
   - Activities & attractions
   - Transportation
   - Miscellaneous
   - Total

Format the response in a clear, organized manner with appropriate headings and bullet points.
Keep all cost estimates in {currency}.
"""
        return prompt


def main():
    """Interactive mode"""
    print("=" * 60)
    print("🌍 Travel Planning Agent")
    print("=" * 60)
    
    agent = TravelAgent()
    
    # Get user input
    print("\nLet's plan your trip!")
    destination = input("📍 Destination: ")
    days = int(input("📅 Number of days: "))
    budget_input = input("💰 Budget (e.g., 10000000 VND or 3000 USD): ")
    
    # Parse budget
    parts = budget_input.split()
    budget = float(parts[0].replace(",", ""))
    currency = parts[1] if len(parts) > 1 else "VND"
    
    preferences_input = input("🎯 Preferences (comma-separated, or press Enter to skip): ")
    preferences = [p.strip() for p in preferences_input.split(",")] if preferences_input else []
    
    print("\n" + "=" * 60)
    print("Planning your trip... This may take a moment.\n")
    
    # Plan the trip
    plan = agent.plan_trip(
        destination=destination,
        days=days,
        budget=budget,
        currency=currency,
        preferences=preferences
    )
    
    # Display the plan
    print("\n" + "=" * 60)
    print("📋 YOUR TRAVEL PLAN")
    print("=" * 60)
    print(plan)
    print("\n" + "=" * 60)
    
    # Save to file
    output_file = f"trip_plan_{destination.replace(' ', '_').lower()}.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(plan)
    print(f"\n✅ Plan saved to: {output_file}")


if __name__ == "__main__":
    main()
