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
    """Phân tích câu hỏi của người dùng và xác định xem có cần làm rõ thêm không"""
    query = state["query"]
    gemini = _gemini_model()
    
    analysis_prompt = f"""
    Bạn là một chuyên gia tư vấn du lịch. Phân tích câu hỏi của khách hàng và xác định:
    1. Các thông tin đã có (điểm đến, thời gian, ngân sách, sở thích...)
    2. Các thông tin còn thiếu cần hỏi thêm
    
    Câu hỏi: {query}
    
    Trả về JSON format:
    {{
        "has_destination": true/false,
        "has_duration": true/false,
        "has_budget": true/false,
        "has_interests": true/false,
        "needs_clarification": true/false,
        "clarification_questions": ["câu hỏi 1", "câu hỏi 2", ...],
        "extracted_preferences": {{
            "destination": "...",
            "duration": "...",
            "budget": "...",
            "interests": ["..."]
        }}
    }}
    """
    
    response = gemini.generate_content(analysis_prompt)
    analysis_text = getattr(response, "text", str(response))
    
    # Parse JSON response (simplified - should use proper JSON parsing)
    import json
    import re
    json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
    if json_match:
        try:
            analysis = json.loads(json_match.group())
            state["needs_clarification"] = analysis.get("needs_clarification", False)
            state["clarification_questions"] = analysis.get("clarification_questions", [])
            state["user_preferences"] = analysis.get("extracted_preferences", {})
        except json.JSONDecodeError:
            state["needs_clarification"] = False
    
    return state


def _deep_web_search(state: TravelState) -> TravelState:
    """Tìm kiếm thông tin chi tiết về điểm đến"""
    preferences = state.get("user_preferences", {})
    destination = preferences.get("destination", "")
    interests = preferences.get("interests", [])
    
    # Build comprehensive search query
    search_query = state["query"]
    if destination:
        search_query = f"{destination} travel guide"
        if interests:
            search_query += f" {' '.join(interests)}"
    
    if TavilyClient is None:
        raise RuntimeError("tavily package is required to run the travel agent") from _TAVILY_IMPORT_ERROR
    
    client = TavilyClient()
    
    # Search for multiple aspects
    search_queries = [
        f"{destination} best attractions and places to visit",
        f"{destination} accommodation recommendations",
        f"{destination} local food and restaurants",
        f"{destination} travel tips and transportation"
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
    """Tạo các kế hoạch du lịch cá nhân hóa dựa trên preferences và search results"""
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
    
    destination = preferences.get("destination", "điểm đến")
    duration = preferences.get("duration", "vài ngày")
    budget = preferences.get("budget", "linh hoạt")
    interests = preferences.get("interests", [])
    
    planning_prompt = f"""
    Bạn là một chuyên gia tư vấn du lịch chuyên nghiệp. Hãy tạo 3 kế hoạch du lịch chi tiết và cá nhân hóa.
    
    THÔNG TIN KHÁCH HÀNG:
    - Điểm đến: {destination}
    - Thời gian: {duration}
    - Ngân sách: {budget}
    - Sở thích: {', '.join(interests) if interests else 'chưa xác định'}
    
    THÔNG TIN TÌM ĐƯỢC:
    {chr(10).join(sources_summary[:10])}
    
    YÊU CẦU:
    Tạo 3 PLAN khác nhau (Budget-Friendly, Balanced, Premium) với:
    
    1. **Tên kế hoạch** và phong cách
    2. **Tổng quan**: Mô tả ngắn gọn về kế hoạch
    3. **Lịch trình chi tiết theo ngày**:
       - Sáng: Hoạt động + địa điểm cụ thể
       - Trưa: Ăn trưa đâu + món gì
       - Chiều: Hoạt động + địa điểm
       - Tối: Ăn tối + giải trí
    4. **Khách sạn đề xuất**: Tên + vị trí + giá tham khảo
    5. **Chi phí ước tính**: Chia nhỏ (ăn, ở, di chuyển, vui chơi)
    6. **Tips quan trọng**: 3-5 lời khuyên hữu ích
    7. **Links tham khảo**: Trích dẫn các URL có sẵn
    
    Format markdown rõ ràng, dễ đọc. Đưa ra các gợi ý CỤ THỂ, thực tế, có thể thực hiện được.
    """
    
    response = gemini.generate_content(planning_prompt)
    plans_text = getattr(response, "text", str(response))
    
    state["travel_plans"] = [{
        "content": plans_text,
        "type": "comprehensive_plans"
    }]
    
    return state


def _synthesize_answer(state: TravelState) -> TravelState:
    """Tổng hợp câu trả lời cuối cùng"""
    if state.get("answer"):
        return state
    
    # Nếu cần clarification, trả về câu hỏi
    if state.get("needs_clarification"):
        questions = state.get("clarification_questions", [])
        if questions:
            clarification_text = "Để tư vấn chính xác hơn, cho mình hỏi thêm:\n\n"
            for i, q in enumerate(questions, 1):
                clarification_text += f"{i}. {q}\n"
            clarification_text += "\nBạn có thể chia sẻ thêm để mình đưa ra kế hoạch phù hợp nhất nhé! 😊"
            state["answer"] = clarification_text
            return state
    
    # Nếu có travel plans, format output
    travel_plans = state.get("travel_plans", [])
    if travel_plans:
        state["answer"] = travel_plans[0].get("content", "")
    else:
        # Fallback to simple answer
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
        Dựa trên thông tin tìm được, hãy trả lời câu hỏi của khách hàng một cách chi tiết và hữu ích.
        
        Câu hỏi: {query}
        
        Thông tin:
        {chr(10).join(sources_summary[:5])}
        
        Hãy đưa ra câu trả lời thân thiện, chuyên nghiệp với các gợi ý cụ thể và links tham khảo.
        """
        
        response = gemini.generate_content(prompt)
        state["answer"] = getattr(response, "text", str(response))
    
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
            "Trợ lý du lịch thông minh với khả năng:\n"
            "• Đặt câu hỏi để hiểu rõ nhu cầu khách hàng\n"
            "• Tìm kiếm thông tin chi tiết về điểm đến\n"
            "• Lập kế hoạch du lịch cá nhân hóa với 3 lựa chọn (Budget/Balanced/Premium)\n"
            "• Đề xuất lịch trình chi tiết theo ngày, khách sạn, ăn uống, chi phí\n"
            "• Cung cấp tips và links hữu ích"
        ),
        runner=run_travel_agent,
    )
)


