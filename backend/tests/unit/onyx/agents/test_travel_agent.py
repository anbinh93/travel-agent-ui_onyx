from __future__ import annotations

from types import SimpleNamespace

import pytest

from onyx.agents.registry import get_agent_runner, list_agents
from onyx.agents.travel import travel_agent


@pytest.fixture(autouse=True)
def _env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    travel_agent._ENV_LOADED = False
    travel_agent._compiled_graph.cache_clear()
    travel_agent._gemini_model.cache_clear()


def test_travel_agent_prefers_tavily_answer(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeTavilyClient:
        def search(self, *, query: str, **_: object) -> dict:
            return {
                "answer": "Visit Kyoto in spring for cherry blossoms.",
                "results": [
                    {
                        "title": "Kyoto travel guide",
                        "url": "https://example.com/kyoto",
                    }
                ],
            }

    monkeypatch.setattr(travel_agent, "TavilyClient", FakeTavilyClient)
    
    def fail_gemini_model() -> object:
        raise AssertionError("Gemini model should not be invoked when Tavily provides an answer")

    monkeypatch.setattr(travel_agent, "_gemini_model", fail_gemini_model)

    result = travel_agent.run_travel_agent("Plan a Japan itinerary")

    assert result["answer"] == "Visit Kyoto in spring for cherry blossoms."
    assert result["sources"] == [
        {
            "title": "Kyoto travel guide",
            "url": "https://example.com/kyoto",
        }
    ]


def test_travel_agent_synthesizes_answer(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeTavilyClient:
        def search(self, *, query: str, **_: object) -> dict:
            return {
                "results": [
                    {
                        "title": "Athens highlights",
                        "url": "https://example.com/athens",
                        "content": "Explore Acropolis and local food tours.",
                    }
                ],
            }

    class FakeGeminiModel:
        def generate_content(self, prompt: str) -> SimpleNamespace:
            assert "Athens" in prompt
            return SimpleNamespace(text="Consider a two-day Athens city break.")

    monkeypatch.setattr(travel_agent, "TavilyClient", FakeTavilyClient)
    monkeypatch.setattr(travel_agent, "_gemini_model", lambda: FakeGeminiModel())

    result = travel_agent.run_travel_agent("Weekend in Athens")

    assert result["answer"] == "Consider a two-day Athens city break."
    assert result["sources"][0]["url"] == "https://example.com/athens"


def test_registry_exposes_travel_agent() -> None:
    agents = list_agents()
    assert any(agent["key"] == "travel_tavily" for agent in agents)

    runner = get_agent_runner("travel_tavily")
    assert runner is travel_agent.run_travel_agent
