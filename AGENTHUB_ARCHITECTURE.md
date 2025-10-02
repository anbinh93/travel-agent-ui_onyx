# AgentHub Architecture & Flow

## 📋 Overview

AgentHub là một **Agent Registry** tương tự như Model Registry cho LLMs. Các agents được wrap thành APIs và có thể được chọn trong chat UI giống như việc chọn models (GPT-4o, Claude, etc.).

## 🏗️ Core Concepts

### 1. Agent as Model
- Agents xuất hiện trong **model selector** cùng với GPT-4o, Claude, v.v.
- Mỗi agent có:
  - **Key**: Unique identifier (e.g., `travel_agent`)
  - **Name**: Display name
  - **Capabilities**: Web search, RAG, code execution, etc.
  - **Version**: Semantic versioning (v1.0.0)
  - **Icon & Color**: For UI display

### 2. Knowledge Base System
- **Centralized KB**: Shared knowledge bases cho nhiều agents
- **Versioning**: Track changes, rollback capability
- **Enable/Disable**: Bật/tắt KB per agent
- **Monitoring**: Query count, usage metrics

### 3. Connector Integration
- **Feed Data**: Connectors (Notion, Slack, Google Drive) feed vào KB
- **Auto-sync**: Scheduled syncs (cron-like)
- **Manual Trigger**: On-demand sync
- **Event-based**: Trigger on connector events

## 🔄 Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND - Chat UI                        │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Model Selector Dropdown                                   │  │
│  │  [v] GPT-4o                                              │  │
│  │  [ ] Claude 3.5 Sonnet                                   │  │
│  │  [v] Travel Agent ✈️ (AgentHub)                          │  │
│  │  [ ] Research Agent 🔬 (AgentHub)                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  User: "Plan a 7-day trip to Tokyo"                             │
│                                                                  │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         │ POST /api/agenthub/run
                         │ { agent_key: "travel_agent", query: "..." }
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND - AgentHub API                        │
│                                                                  │
│  📍 Endpoint: /api/agenthub/run                                 │
│                                                                  │
│  1. Validate agent exists                                        │
│  2. Get agent definition from registry                           │
│  3. Check if KB is enabled for this agent                        │
│  4. Prepare execution context                                    │
│  5. Execute agent.runner(query, context)                         │
│                                                                  │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Agent Registry                               │
│                                                                  │
│  registry.execute_agent(agent_key, query, context)              │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ 1. Load Agent Definition                               │   │
│  │    - Travel Agent (travel_agent.py)                    │   │
│  │    - Capabilities: WEB_SEARCH, RAG, CONDITIONAL_LOGIC │   │
│  │    - use_knowledge_base: True                          │   │
│  │    - knowledge_base_ids: [uuid1, uuid2]                │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ 2. Load Knowledge Bases (if enabled)                   │   │
│  │    FOR EACH kb_id IN agent.knowledge_base_ids:         │   │
│  │      kb = kb_manager.get_knowledge_base(kb_id)         │   │
│  │      IF kb.enabled:                                     │   │
│  │        context['knowledge_bases'].append(kb)           │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ 3. Execute Agent Runner                                 │   │
│  │    result = agent.runner(query, context)                │   │
│  │    ▼                                                     │   │
│  │    Travel Agent Logic (travel_agent.py):                │   │
│  │    a) Analyze query                                     │   │
│  │    b) Check missing info → Ask clarifying questions     │   │
│  │    c) Deep web search (using tools)                     │   │
│  │    d) Query knowledge bases (if available)              │   │
│  │    e) Create 3 plans (Budget/Balanced/Premium)          │   │
│  │    f) Return structured result                          │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ 4. Post-Execution                                       │   │
│  │    - Record KB queries                                  │   │
│  │    - Update metrics                                     │   │
│  │    - Add execution metadata                             │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                  │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Knowledge Base Manager                          │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Knowledge Base: "Travel KB"                              │ │
│  │  - Status: ACTIVE                                        │ │
│  │  - Enabled: ✓                                           │ │
│  │  - Version: v1.2.3                                       │ │
│  │  - Agents: [travel_agent, research_agent]               │ │
│  │                                                          │ │
│  │  Connectors:                                             │ │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐          │ │
│  │  │ Notion     │ │ Google     │ │ Web        │          │ │
│  │  │ Enabled: ✓ │ │ Drive      │ │ Scraper    │          │ │
│  │  │ Auto-sync  │ │ Enabled: ✓ │ │ Enabled: ✓ │          │ │
│  │  │ Every 1hr  │ │ Every 30m  │ │ Manual     │          │ │
│  │  └────────────┘ └────────────┘ └────────────┘          │ │
│  │                                                          │ │
│  │  Versions:                                               │ │
│  │  - v1.2.3 (current) - 1,234 docs - 45MB                 │ │
│  │  - v1.2.2 - 1,200 docs - 44MB                           │ │
│  │  - v1.2.1 - 1,150 docs - 43MB                           │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 Trigger Mechanisms

### 1. **Manual Trigger** (User asks in chat)
```
User selects "Travel Agent" → Types query → Agent executes
```

### 2. **Scheduled Trigger** (Cron jobs)
```python
# Agent definition with scheduled trigger
AgentDefinition(
    key="daily_report_agent",
    triggers=[
        AgentTriggerConfig(
            trigger_type=TriggerType.SCHEDULED,
            cron_expression="0 9 * * *",  # Every day at 9 AM
        )
    ]
)
```

### 3. **Webhook Trigger** (External events)
```
External system → POST /api/agenthub/webhook/agent_key
                → Agent executes with webhook payload
```

### 4. **Connector Event Trigger** (Data sync events)
```
Connector syncs new data → KB updated → Event fired
                                      → Agents listening to KB trigger
```

## 📊 Conditional Branching (if-else logic)

Agents có thể implement conditional logic trong runner function:

```python
def run_agent(query: str, context: dict) -> dict:
    # Step 1: Analyze
    analysis = analyze_query(query)
    
    # Conditional branching
    if analysis["missing_info"]:
        # Branch A: Ask clarifying questions
        return {
            "answer": generate_questions(analysis["missing_info"]),
            "needs_clarification": True,
        }
    elif analysis["confidence"] < 0.5:
        # Branch B: Use deep search
        search_results = deep_search(query)
        return create_answer(search_results)
    else:
        # Branch C: Direct answer from KB
        kb_results = query_knowledge_base(query, context["knowledge_bases"])
        return create_answer(kb_results)
```

## 🎯 Key API Endpoints

### Agent Management
- `GET /api/agenthub/agents` - List all agents (like listing models)
- `GET /api/agenthub/agents/models` - Get agents for model selector UI
- `GET /api/agenthub/agents/{agent_key}` - Get agent details
- `POST /api/agenthub/run` - Execute agent (like LLM completion)

### Knowledge Base Management
- `POST /api/agenthub/knowledge-bases` - Create new KB
- `GET /api/agenthub/knowledge-bases` - List KBs
- `POST /api/agenthub/knowledge-bases/{kb_id}/enable` - Enable KB
- `POST /api/agenthub/knowledge-bases/{kb_id}/disable` - Disable KB
- `POST /api/agenthub/knowledge-bases/connectors` - Add connector
- `POST /api/agenthub/knowledge-bases/{kb_id}/sync` - Manual sync

## 💡 Usage Examples

### 1. Frontend: Select Agent in Chat UI
```typescript
// Fetch available models AND agents
const models = await fetch('/api/models');
const agents = await fetch('/api/agenthub/agents/models');

// Merge them
const allOptions = [...models, ...agents];

// Display in dropdown
<select>
  <option value="gpt-4o">GPT-4o</option>
  <option value="claude-3-5-sonnet">Claude 3.5 Sonnet</option>
  <option value="agent:travel_agent">✈️ Travel Agent</option>
  <option value="agent:research_agent">🔬 Research Agent</option>
</select>
```

### 2. Backend: Register New Agent
```python
from onyx.agents.base import AgentDefinition, AgentType, AgentCapability
from onyx.agents.registry import register_agent

def my_custom_agent(query: str, context: dict) -> dict:
    # Your agent logic here
    return {
        "answer": "...",
        "sources": [...],
    }

# Register
register_agent(AgentDefinition(
    key="my_agent",
    name="My Custom Agent",
    description="Does amazing things",
    runner=my_custom_agent,
    agent_type=AgentType.TASK_EXECUTOR,
    capabilities=[AgentCapability.WEB_SEARCH, AgentCapability.RAG],
    use_knowledge_base=True,
    knowledge_base_ids=[kb_uuid],
    version="1.0.0",
    icon="🚀",
    color="#10b981",
    tags=["custom", "awesome"],
))
```

### 3. Create Knowledge Base with Connectors
```python
# Create KB
kb = kb_manager.create_knowledge_base(
    name="Travel Knowledge Base",
    description="All travel-related information",
    agent_keys=["travel_agent"],
)

# Add Notion connector
kb_manager.add_connector(
    kb_id=kb.kb_id,
    connector_type=KnowledgeSourceType.NOTION,
    name="Travel Guides Notion",
    config={
        "notion_token": "secret_...",
        "database_id": "abc123",
    },
    auto_sync=True,
    sync_interval_minutes=60,
)

# Add Google Drive connector
kb_manager.add_connector(
    kb_id=kb.kb_id,
    connector_type=KnowledgeSourceType.GOOGLE_DRIVE,
    name="Travel Documents",
    config={
        "folder_id": "xyz789",
        "service_account": {...},
    },
    auto_sync=True,
    sync_interval_minutes=30,
)
```

### 4. Execute Agent
```python
registry = get_agent_registry()

result = registry.execute_agent(
    agent_key="travel_agent",
    query="Plan a 5-day trip to Paris with $2000 budget",
    context={
        "user_id": "user123",
        "preferences": ["museums", "food"],
    }
)

print(result["answer"])
print(result["plans"])  # Budget, Balanced, Premium plans
```

## 🔐 Security & Permissions

- **User Authentication**: All endpoints require `current_chat_accessible_user`
- **KB Permissions**: Users can only access KBs they have permission for
- **API Keys**: Agents requiring external APIs check for valid keys
- **Rate Limiting**: Prevent abuse of agent execution

## 📈 Monitoring & Metrics

Knowledge Base metrics track:
- Query count and success rate
- Sync statistics
- Document changes
- Agent usage per KB
- Average latency

## 🚀 Future Enhancements

1. **Visual Workflow Builder**: n8n-style UI for composing agents
2. **Agent Marketplace**: Share and discover agents
3. **Multi-Agent Orchestration**: Chain agents together
4. **Advanced Triggers**: More event types, complex conditions
5. **A/B Testing**: Test different agent versions
6. **Cost Tracking**: Monitor token usage and API costs

---

This architecture allows agents to be **first-class citizens** alongside LLMs, with full support for knowledge bases, connectors, triggers, and conditional logic! 🎉
