from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path
from typing import Any, Dict, List, TypedDict, Optional

from dotenv import load_dotenv
from langgraph.graph import END, StateGraph

try:  # pragma: no cover - import guard exercised via tests
    import google.generativeai as genai  # type: ignore[import-not-found]
except ImportError as _import_exc_gemini:  # pragma: no cover - allowed fallback
    genai = None  # type: ignore[assignment]
    _GEMINI_IMPORT_ERROR = _import_exc_gemini
else:
    _GEMINI_IMPORT_ERROR = None

try:  # pragma: no cover - import guard exercised via tests
    from tavily import TavilyClient  # type: ignore[import-not-found]
except ImportError as _import_exc:  # pragma: no cover - allowed fallback
    TavilyClient = None  # type: ignore[assignment]
    _TAVILY_IMPORT_ERROR = _import_exc
else:
    _TAVILY_IMPORT_ERROR = None

from onyx.agents.base import AgentDefinition
from onyx.agents.registry import register_agent


class TravelState(TypedDict, total=False):
    query: str
    conversation_history: List[Dict[str, str]]
    user_preferences: Dict[str, Any]
    needs_clarification: bool
    clarification_questions: List[str]
    search_results: List[Dict[str, Any]]
    travel_plans: List[Dict[str, Any]]
    answer: str


_ENV_LOADED = False


def _ensure_env_loaded() -> None:
    global _ENV_LOADED
    if _ENV_LOADED:
        return

    candidate_paths: list[Path] = []

    override_path = os.environ.get("ONYX_ENV_FILE")
    if override_path:
        candidate_paths.append(Path(override_path))

    current_path = Path(__file__).resolve()
    parents = list(current_path.parents)
    # Typical structure: [..., travel, agents, onyx, onyx, backend, onyx, ...]
    for depth in (4, 5, 6):
        if depth < len(parents):
            candidate_paths.append(parents[depth] / ".env")

    candidate_paths.append(Path.cwd() / ".env")

    seen: set[Path] = set()
    for path in candidate_paths:
        try:
            path = path.resolve()
        except FileNotFoundError:
            continue
        if path in seen or not path.exists():
            continue
        load_dotenv(path, override=False)
        seen.add(path)

    # Finally load from environment / defaults in case nothing matched
    load_dotenv(override=False)

    _ENV_LOADED = True


def _validate_required_env() -> None:
    if not os.environ.get("TAVILY_API_KEY") and os.environ.get("TAVILY_APU_KEY"):
        os.environ["TAVILY_API_KEY"] = os.environ["TAVILY_APU_KEY"]

    missing: list[str] = []
    if not os.environ.get("TAVILY_API_KEY"):
        missing.append("TAVILY_API_KEY")
    if not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GEN_AI_API_KEY")):
        missing.append("GEMINI_API_KEY or GEN_AI_API_KEY")
    if missing:
        missing_list = ", ".join(missing)
        raise RuntimeError(
            "Missing environment variables for travel agent: " f"{missing_list}. "
            "Populate them in your Onyx .env file."
        )


def _analyze_user_query(state: TravelState) -> TravelState:
    """Analyze user query and determine if clarification is needed"""
    query = state["query"]
    gemini = _gemini_model()
    
    analysis_prompt = f"""
    You are an expert travel consultant. Analyze the customer's question and extract information.
    
    IMPORTANT: ONLY request clarification if destination is COMPLETELY MISSING or query is extremely vague.
    If you have at least a destination or can suggest general options, set needs_clarification = false.
    
    Query: {query}
    
    Return JSON format:
    {{
        "has_destination": true/false,
        "needs_clarification": true/false,
        "clarification_questions": ["only ask if absolutely necessary"],
        "extracted_preferences": {{
            "destination": "location name or 'general' if unclear",
            "duration": "number of days or 'flexible'",
            "budget": "budget level or 'flexible'",
            "interests": ["activities/preferences"]
        }}
    }}
    
    NOTE: Prioritize providing plans immediately rather than asking more questions. Only ask if you cannot provide any suggestions.
    """
    
    response = gemini.generate_content(analysis_prompt)
    analysis_text = getattr(response, "text", str(response))
    
    # Parse JSON response
    import json
    import re
    json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
    if json_match:
        try:
            analysis = json.loads(json_match.group())
            # Chỉ cho phép clarification nếu THỰC SỰ thiếu destination
            has_destination = analysis.get("has_destination", False)
            state["needs_clarification"] = analysis.get("needs_clarification", False) and not has_destination
            state["clarification_questions"] = analysis.get("clarification_questions", [])[:2]  # Limit to 2 questions max
            state["user_preferences"] = analysis.get("extracted_preferences", {})
        except json.JSONDecodeError:
            # Nếu parse fail, assume có thể proceed
            state["needs_clarification"] = False
            state["user_preferences"] = {
                "destination": "general",
                "duration": "flexible",
                "budget": "flexible",
                "interests": []
            }
    else:
        # Fallback: proceed without clarification
        state["needs_clarification"] = False
        state["user_preferences"] = {
            "destination": query,
            "duration": "flexible",
            "budget": "flexible",
            "interests": []
        }
    
    return state


def _deep_web_search(state: TravelState) -> TravelState:
    """Search for detailed information about the destination"""
    preferences = state.get("user_preferences", {})
    destination = preferences.get("destination", "")
    interests = preferences.get("interests", [])
    
    # Build comprehensive search query
    search_query = state["query"]
    if destination:
        search_query = f"{destination} travel guide 2025"
        if interests:
            search_query += f" {' '.join(interests)}"
    
    if TavilyClient is None:
        raise RuntimeError("tavily package is required to run the travel agent") from _TAVILY_IMPORT_ERROR
    
    client = TavilyClient()
    
    # Search for multiple aspects
    search_queries = [
        f"{destination} best attractions places to visit 2025",
        f"{destination} hotels accommodation recommendations",
        f"{destination} local food restaurants must try",
        f"{destination} travel tips transportation guide"
    ]
    
    all_results = []
    for query in search_queries[:2]:  # Limit to avoid too many API calls
        try:
            results = client.search(
                query=query,
                search_depth="advanced",
                include_answer=True,
                max_results=4,
            )
            all_results.extend(results.get("results", []))
        except Exception:
            continue
    
    state["search_results"] = all_results
    return state


@lru_cache(maxsize=1)
def _gemini_model() -> Any:
    if genai is None:
        raise RuntimeError(
            "google-generativeai package is required to run the travel agent"
        ) from _GEMINI_IMPORT_ERROR

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEN_AI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing environment variables for travel agent: GEMINI_API_KEY or GEN_AI_API_KEY."
        )

    genai.configure(api_key=api_key)
    model_name = (
        os.environ.get("GEN_AI_MODEL_VERSION")
        or os.environ.get("GEMINI_MODEL_NAME")
        or "gemini-2.0-flash"
    )
    return genai.GenerativeModel(model_name)


def _create_travel_plans(state: TravelState) -> TravelState:
    """Create personalized travel plans based on preferences and search results"""
    preferences = state.get("user_preferences", {})
    documents = state.get("search_results", [])
    
    gemini = _gemini_model()
    
    # Prepare context from search results
    sources_summary = []
    for item in documents:
        title = item.get("title") or ""
        url = item.get("url") or ""
        content = item.get("content") or item.get("snippet") or ""
        sources_summary.append(f"- {title}\n  URL: {url}\n  Info: {content[:300]}")
    
    destination = preferences.get("destination", "destination")
    duration = preferences.get("duration", "flexible")
    budget = preferences.get("budget", "flexible")
    interests = preferences.get("interests", [])
    
    planning_prompt = f"""
    You are a professional travel consultant. Create 3 detailed and personalized travel plans.
    
    CLIENT INFORMATION:
    - Destination: {destination}
    - Duration: {duration}
    - Budget: {budget}
    - Interests: {', '.join(interests) if interests else 'not specified'}
    
    RESEARCH INFORMATION:
    {chr(10).join(sources_summary[:10])}
    
    REQUIREMENTS:
    Create 3 DISTINCT PLANS (Budget-Friendly, Balanced, Premium) with this EXACT HTML-enhanced markdown structure:
    
    <div style="border: 2px solid #4F46E5; border-radius: 12px; padding: 20px; margin: 20px 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
    
    # 🌟 Plan 1: Budget-Friendly Explorer
    
    **Perfect for:** Travelers who want authentic experiences without breaking the bank
    
    </div>
    
    ## 📋 Overview
    
    > *[2-3 sentences describing this plan's unique approach, highlighting the value and experiences it offers]*
    
    ---
    
    ## 📅 Day-by-Day Itinerary
    
    <details open>
    <summary><strong>🌅 Day 1: [Theme Name]</strong></summary>
    
    | Time | Activity | Details | Cost |
    |------|----------|---------|------|
    | **9:00 AM** | 🏛️ **[Activity Name]** | [Specific location/venue]<br>*[Brief description]* | $XX |
    | **12:30 PM** | 🍜 **Lunch** | **[Restaurant Name]**<br>[Signature dish] | $XX |
    | **2:00 PM** | 🎨 **[Activity Name]** | [Specific location]<br>*[What to see/do]* | $XX |
    | **6:00 PM** | 🌆 **Evening** | **[Venue/Restaurant]**<br>[Activity/dish details] | $XX |
    
    💡 **Day 1 Pro Tip:** [Specific actionable tip for this day]
    
    </details>
    
    [Repeat this structure for each day]
    
    ---
    
    ## 🏨 Where to Stay
    
    <div style="background: #F3F4F6; padding: 15px; border-radius: 8px; border-left: 4px solid #4F46E5;">
    
    ### **[Hotel/Hostel Name]** ⭐⭐⭐
    
    - 📍 **Location:** [Specific neighborhood/area]
    - 💰 **Price:** $XX per night
    - ✨ **Why Choose This:** 
      - [Feature 1]
      - [Feature 2]
      - [Feature 3]
    - 🔗 **Book:** [URL if available]
    
    </div>
    
    ---
    
    ## 💰 Budget Breakdown
    
    | Category | Daily | Total ({duration}) |
    |----------|-------|----------|
    | 🏨 Accommodation | $XX | **$XXX** |
    | 🍽️ Meals | $XX | **$XXX** |
    | 🚇 Transportation | $XX | **$XXX** |
    | 🎭 Activities & Entertainment | $XX | **$XXX** |
    | 🎁 Shopping & Extras | $XX | **$XXX** |
    | **💵 TOTAL** | **$XX** | **💰 $XXX** |
    
    ---
    
    ## 💡 Insider Tips & Hacks
    
    1. 🎫 **[Tip category]:** [Specific actionable advice with details]
    
    2. 🕐 **[Tip category]:** [Practical tip that saves money/time]
    
    3. 📱 **[Tip category]:** [Local insight or app recommendation]
    
    4. 🍴 **[Tip category]:** [Food/dining hack]
    
    5. 🚫 **[Tip category]:** [What to avoid]
    
    ---
    
    ## 🔗 Essential Resources
    
    - 🗺️ **Transportation:** [Specific link/card info]
    - 📱 **Must-Have Apps:** [App names with brief description]
    - 🎟️ **Advance Bookings:** [What to book ahead + links]
    - 🌐 **Official Tourism:** [URL]
    
    ---
    
    [Repeat entire structure for Plan 2: Balanced Adventurer and Plan 3: Premium Experience]
    
    IMPORTANT FORMATTING RULES:
    - Use HTML divs for colored boxes and highlights
    - Use tables for itineraries (more scannable)
    - Use <details> tags for collapsible days
    - Use emojis consistently for visual hierarchy
    - Be SPECIFIC: real names, exact prices, actual locations
    - Keep tone professional but friendly
    - Include actual URLs from research
    - Make it PRINT-READY and SHAREABLE
    """
    
    response = gemini.generate_content(planning_prompt)
    plans_text = getattr(response, "text", str(response))
    
    state["travel_plans"] = [{
        "content": plans_text,
        "type": "comprehensive_plans"
    }]
    
    return state


def _synthesize_answer(state: TravelState) -> TravelState:
    """Synthesize final answer"""
    if state.get("answer"):
        return state
    
    # If clarification needed, return questions (ONLY if absolutely necessary)
    if state.get("needs_clarification"):
        questions = state.get("clarification_questions", [])
        if questions:
            clarification_text = "# 🤔 Quick Questions\n\n"
            clarification_text += "To create the perfect itinerary for you, I need a bit more information:\n\n"
            for i, q in enumerate(questions, 1):
                clarification_text += f"{i}. {q}\n"
            clarification_text += "\n💡 **Tip:** Include destination, duration, and budget for the best recommendations!"
            state["answer"] = clarification_text
            return state
    
    # If travel plans exist, format output
    travel_plans = state.get("travel_plans", [])
    if travel_plans:
        answer = travel_plans[0].get("content", "")
        
        # Add professional intro with enhanced styling
        preferences = state.get("user_preferences", {})
        destination = preferences.get("destination", "")
        duration = preferences.get("duration", "")
        budget = preferences.get("budget", "")
        interests = preferences.get("interests", [])
        
        # Build styled header
        intro = '<div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 12px; margin-bottom: 30px;">\n\n'
        
        if destination and destination != "general":
            intro += f'# ✈️ Your {destination} Adventure Awaits!\n\n'
            if duration and duration != "flexible":
                intro += f'### 🎯 {duration} of unforgettable experiences\n\n'
            if budget and budget != "flexible":
                intro += f'💰 Budget: {budget}\n\n'
            if interests:
                intro += f'🎨 Focus: {", ".join(interests)}\n\n'
        else:
            intro += '# ✈️ Your Perfect Journey Starts Here!\n\n'
            intro += '### 🌍 Personalized travel plans just for you\n\n'
        
        intro += '</div>\n\n'
        intro += '<div style="background: #FEF3C7; padding: 15px; border-radius: 8px; border-left: 4px solid #F59E0B; margin: 20px 0;">\n\n'
        intro += '**📖 How to use these plans:**\n\n'
        intro += '1. 🔍 Review all 3 plans to find your perfect match\n'
        intro += '2. 📋 Each plan includes detailed daily itineraries, accommodation, and costs\n'
        intro += '3. 💡 Check insider tips to maximize your experience\n'
        intro += '4. 🔗 Use the resource links for bookings and more information\n\n'
        intro += '</div>\n\n'
        intro += '---\n\n'
        
        # Add table of contents
        intro += '## 📑 Quick Navigation\n\n'
        intro += '- [🌟 Plan 1: Budget-Friendly Explorer](#plan-1-budget-friendly-explorer)\n'
        intro += '- [⚖️ Plan 2: Balanced Adventurer](#plan-2-balanced-adventurer)\n'
        intro += '- [💎 Plan 3: Premium Experience](#plan-3-premium-experience)\n\n'
        intro += '---\n\n'
        
        state["answer"] = intro + answer
    else:
        # Fallback to simple answer (shouldn't happen often)
        query = state["query"]
        documents = state.get("search_results", [])
        gemini = _gemini_model()
        
        sources_summary = []
        for item in documents:
            title = item.get("title") or ""
            url = item.get("url") or ""
            content = item.get("content") or item.get("snippet") or ""
            sources_summary.append(f"- {title}\n  {url}\n  {content[:200]}")
        
        prompt = f"""
        Based on the research findings, provide a detailed and friendly answer to the customer's travel question.
        
        Question: {query}
        
        Research Information:
        {chr(10).join(sources_summary[:5])}
        
        Provide SPECIFIC, practical suggestions with:
        - Must-visit attractions
        - Hotel/accommodation recommendations
        - Local food and restaurants to try
        - Important tips
        - Reference links
        
        Format in clean, scannable markdown with appropriate emojis.
        Use this structure:
        
        # ✈️ [Topic Title]
        
        ## 🎯 Top Recommendations
        [Specific suggestions]
        
        ## 🏨 Where to Stay
        [Hotel recommendations]
        
        ## 🍜 What to Eat
        [Food recommendations]
        
        ## 💡 Insider Tips
        [Practical tips]
        
        ## 🔗 Useful Resources
        [Links]
        """
        
        response = gemini.generate_content(prompt)
        answer = getattr(response, "text", str(response))
        state["answer"] = f"# ✈️ Travel Guide\n\n{answer}"
    
    return state


def _should_search(state: TravelState) -> str:
    """Quyết định có cần search hay chỉ cần clarification"""
    if state.get("needs_clarification"):
        return "synthesize"
    return "web_search"


def build_travel_agent_graph() -> Any:
    """Xây dựng workflow graph cho travel agent"""
    graph = StateGraph(TravelState)
    
    # Add nodes
    graph.add_node("analyze", _analyze_user_query)
    graph.add_node("web_search", _deep_web_search)
    graph.add_node("create_plans", _create_travel_plans)
    graph.add_node("synthesize", _synthesize_answer)
    
    # Define flow
    graph.set_entry_point("analyze")
    
    # Conditional routing: nếu cần clarification thì skip search
    graph.add_conditional_edges(
        "analyze",
        _should_search,
        {
            "web_search": "web_search",
            "synthesize": "synthesize"
        }
    )
    
    graph.add_edge("web_search", "create_plans")
    graph.add_edge("create_plans", "synthesize")
    graph.add_edge("synthesize", END)
    
    return graph.compile()


@lru_cache(maxsize=1)
def _compiled_graph() -> Any:
    return build_travel_agent_graph()


def run_travel_agent(query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Travel agent runner compatible with AgentRegistry.
    
    Args:
        query: User's travel query
        context: Additional context (knowledge bases, user info, etc.) - currently unused
    
    Returns:
        Dict with answer, sources, and plans
    """
    normalized_query = query.strip()
    if not normalized_query:
        raise ValueError("Query must be a non-empty string")

    _ensure_env_loaded()
    _validate_required_env()

    compiled = _compiled_graph()
    initial: TravelState = {"query": normalized_query}
    final_state: TravelState = compiled.invoke(initial)
    return {
        "answer": final_state.get("answer", ""),
        "sources": [
            {"title": r.get("title"), "url": r.get("url")}
            for r in final_state.get("search_results", [])
        ],
    }


register_agent(
    AgentDefinition(
        key="travel_planning_agent",
        name="AI Travel Planning Assistant",
        description=(
            "✈️ Professional Travel Consultant - Instant Itineraries:\n"
            "📋 3 detailed plans (Budget/Balanced/Premium) with beautiful formatting\n"
            "📅 Day-by-day schedules with specific venues, prices & tips\n"
            "🏨 Hotel recommendations with cost breakdowns\n"
            "💡 Insider tips & essential resources\n"
            "🎨 Rich markdown format with tables, emojis & styled sections"
        ),
        runner=run_travel_agent,
    )
)


