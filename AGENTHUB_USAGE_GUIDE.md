# AgentHub Usage Guide

## 🎯 Tổng Quan

AgentHub là nơi quản lý các AI Agents được wrapper theo chuẩn OpenAI, cho phép bạn:
1. **Push agents vào hub** qua 2 cách: API Key hoặc low-level code
2. **Chọn agents trong UI** giống như chọn GPT-4o, Claude
3. **Visualize planning** và xem agent hoạt động
4. **Enable/disable agents** trong model selector

## 🚀 Hiện Trạng

### ✅ Đã Hoạt Động
- Backend API Server: `http://localhost:8080`
- Frontend Web Server: `http://localhost:3000` hoặc `http://localhost`
- AgentHub API: `http://localhost/api/agenthub/*`
- Travel Planning Agent đã được đăng ký và hoạt động

### 🔗 API Endpoints Hoạt Động

```bash
# Lấy danh sách tất cả agents
curl http://localhost/api/agenthub/agents

# Lấy agents cho model selector (format UI)
curl http://localhost/api/agenthub/agents/models

# Chi tiết 1 agent
curl http://localhost/api/agenthub/agents/travel_planning_agent

# Chạy agent
curl -X POST http://localhost/api/agenthub/run \
  -H "Content-Type: application/json" \
  -d '{
    "agent_key": "travel_planning_agent",
    "query": "Plan a 7-day trip to Tokyo"
  }'
```

## 📝 Cách 1: Đăng Ký Agent Qua API (High-Level)

### Bước 1: Tạo Agent Definition File

```python
# my_agent.py
from onyx.agents.base import AgentDefinition, AgentType, AgentCapability

my_agent = AgentDefinition(
    key="my_custom_agent",
    name="My Custom Agent",
    description="Agent mô tả ở đây",
    type=AgentType.CONVERSATIONAL,
    capabilities=[
        AgentCapability.WEB_SEARCH,
        AgentCapability.RAG,
    ],
    version="1.0.0",
    icon="🤖",
    color="#FF6B6B",
    runner=my_agent_runner_function,  # Function xử lý logic
)
```

### Bước 2: Register Agent

```python
from onyx.agents.registry import get_agent_registry

registry = get_agent_registry()
registry.register(my_agent)
```

### Bước 3: Agent Runner Function

```python
def my_agent_runner_function(query: str, context: dict) -> dict:
    """
    Logic xử lý của agent
    
    Args:
        query: Câu hỏi từ user
        context: Context bao gồm user info, KB, tools
    
    Returns:
        dict với keys:
        - answer: str (Câu trả lời)
        - sources: list[dict] (Nguồn tham khảo)
        - plans: Optional[list[dict]] (Các plans nếu có)
        - needs_clarification: bool (Cần hỏi thêm không)
        - metadata: dict (Metadata khác)
    """
    # Your logic here
    answer = f"Processing: {query}"
    
    return {
        "answer": answer,
        "sources": [],
        "needs_clarification": False,
        "metadata": {}
    }
```

## 📂 Cách 2: Low-Level Code (Như Assistants API)

### Ví Dụ: Travel Agent

File: `/Users/nguyenbinhan/Workspace/AgentAI/Onyx/onyx/backend/onyx/agents/implementations/travel_planning_agent.py`

```python
from onyx.agents.base import AgentDefinition, AgentType
from onyx.agents.registry import register_agent

def travel_agent_runner(query: str, context: dict) -> dict:
    # Step 1: Analyze query
    # Step 2: Deep search if needed
    # Step 3: Create plans
    # Step 4: Return structured result
    
    return {
        "answer": "Your travel plan here...",
        "plans": [
            {"type": "budget", "details": "..."},
            {"type": "balanced", "details": "..."},
            {"type": "premium", "details": "..."}
        ],
        "sources": [],
        "needs_clarification": False,
        "metadata": {}
    }

# Register agent
@register_agent
def get_travel_agent() -> AgentDefinition:
    return AgentDefinition(
        key="travel_planning_agent",
        name="AI Travel Planning Assistant",
        description="Trợ lý du lịch thông minh...",
        type=AgentType.CONVERSATIONAL,
        version="1.0.0",
        icon="✈️",
        color="#6366f1",
        runner=travel_agent_runner,
    )
```

## 🎨 Frontend Integration

### Model Selector Modification

File: `web/src/components/llm/LLMProviderSelector.tsx` (hoặc tương tự)

```typescript
// Fetch both models and agents
const fetchModelsAndAgents = async () => {
  const [models, agents] = await Promise.all([
    fetch('/api/models').then(r => r.json()),
    fetch('/api/agenthub/agents/models').then(r => r.json())
  ]);
  
  // Merge và hiển thị
  const allOptions = [...models, ...agents];
  setAvailableModels(allOptions);
};

// Khi user chọn agent
const handleModelSelect = (selectedId: string) => {
  if (selectedId.startsWith('agent:')) {
    // This is an agent
    const agentKey = selectedId.replace('agent:', '');
    setSelectedAgent(agentKey);
    setUseAgent(true);
  } else {
    // This is a normal LLM model
    setSelectedModel(selectedId);
    setUseAgent(false);
  }
};

// Khi gửi message
const sendMessage = async (message: string) => {
  if (useAgent) {
    // Call agent API
    const response = await fetch('/api/agenthub/run', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        agent_key: selectedAgent,
        query: message
      })
    });
    const result = await response.json();
    // Display result.answer
  } else {
    // Normal LLM call
    // ... existing code
  }
};
```

## 🔧 Enable/Disable Agents

### Backend: Agent Toggle API

```python
@router.patch("/agents/{agent_key}/toggle")
def toggle_agent(
    agent_key: str,
    enabled: bool,
    user: User | None = Depends(current_admin_user),
):
    """Enable or disable an agent"""
    registry = get_agent_registry()
    agent = registry.get(agent_key)
    
    if not agent:
        raise HTTPException(404, "Agent not found")
    
    agent.enabled = enabled
    registry.update(agent)
    
    return {"success": True, "enabled": enabled}
```

### Frontend: Toggle UI

```typescript
// Admin panel hoặc settings
const AgentToggle = ({ agent }) => {
  const [enabled, setEnabled] = useState(agent.enabled);
  
  const handleToggle = async () => {
    await fetch(`/api/agenthub/agents/${agent.key}/toggle`, {
      method: 'PATCH',
      body: JSON.stringify({ enabled: !enabled })
    });
    setEnabled(!enabled);
  };
  
  return (
    <div>
      <span>{agent.name}</span>
      <Switch checked={enabled} onChange={handleToggle} />
    </div>
  );
};
```

## 📊 Visualize Planning

### Backend: Planning Metadata

```python
def travel_agent_runner(query: str, context: dict) -> dict:
    # ... logic
    
    return {
        "answer": final_answer,
        "plans": [
            {
                "type": "budget",
                "title": "Budget Plan",
                "total_cost": "$1,500",
                "details": {...}
            },
            {
                "type": "balanced",
                "title": "Balanced Plan",
                "total_cost": "$2,500",
                "details": {...}
            },
            {
                "type": "premium",
                "title": "Premium Plan",
                "total_cost": "$4,000",
                "details": {...}
            }
        ],
        "metadata": {
            "planning_steps": [
                {"step": 1, "action": "Analyzed query", "time": "0.5s"},
                {"step": 2, "action": "Web search", "time": "2.3s"},
                {"step": 3, "action": "Created plans", "time": "1.2s"}
            ]
        }
    }
```

### Frontend: Planning Visualization

```typescript
const PlanningVisualization = ({ result }) => {
  const { plans, metadata } = result;
  
  return (
    <div>
      {/* Planning Steps Timeline */}
      <div className="planning-timeline">
        {metadata.planning_steps.map(step => (
          <div key={step.step} className="step">
            <div className="step-number">{step.step}</div>
            <div className="step-action">{step.action}</div>
            <div className="step-time">{step.time}</div>
          </div>
        ))}
      </div>
      
      {/* Plans Comparison */}
      <div className="plans-grid">
        {plans.map(plan => (
          <div key={plan.type} className="plan-card">
            <h3>{plan.title}</h3>
            <div className="cost">{plan.total_cost}</div>
            <div className="details">{/* Render details */}</div>
          </div>
        ))}
      </div>
    </div>
  );
};
```

## 🔐 Authentication với API Key

### Backend: API Key Validation

```python
from onyx.auth.api_key import validate_api_key

@router.post("/run")
async def run_agent(
    body: RunAgentRequest,
    api_key: str = Header(None, alias="X-API-Key"),
):
    """Run agent with API key auth"""
    # Validate API key
    user = validate_api_key(api_key)
    if not user:
        raise HTTPException(401, "Invalid API key")
    
    # Add user to context
    context = body.context or {}
    context["user_id"] = user.id
    
    # Execute agent
    registry = get_agent_registry()
    result = registry.execute_agent(
        agent_key=body.agent_key,
        query=body.query,
        context=context
    )
    
    return result
```

### Usage với API Key

```bash
curl -X POST http://localhost/api/agenthub/run \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "agent_key": "travel_planning_agent",
    "query": "Plan trip to Tokyo"
  }'
```

## 📦 Wrap External Agents (n8n, etc.)

### Wrapper cho n8n Workflow

```python
import requests
from onyx.agents.base import AgentDefinition, AgentType
from onyx.agents.registry import register_agent

def n8n_agent_runner(query: str, context: dict) -> dict:
    """Wrapper cho n8n workflow"""
    # Call n8n webhook
    response = requests.post(
        "https://your-n8n-instance.com/webhook/agent-endpoint",
        json={
            "query": query,
            "user_id": context.get("user_id"),
            "context": context
        },
        headers={"Authorization": f"Bearer {N8N_API_KEY}"}
    )
    
    result = response.json()
    
    # Convert n8n response to AgentHub format
    return {
        "answer": result.get("output", ""),
        "sources": result.get("sources", []),
        "needs_clarification": result.get("needs_input", False),
        "metadata": {
            "n8n_workflow_id": result.get("workflow_id"),
            "execution_time": result.get("execution_time")
        }
    }

@register_agent
def get_n8n_agent() -> AgentDefinition:
    return AgentDefinition(
        key="n8n_workflow_agent",
        name="N8N Workflow Agent",
        description="Agent powered by n8n workflow",
        type=AgentType.AUTOMATED,
        version="1.0.0",
        icon="🔄",
        color="#FF6D5A",
        runner=n8n_agent_runner,
        requires_api_key=True,
    )
```

## 🧪 Testing

```bash
# Test agent registration
curl http://localhost/api/agenthub/agents

# Test agent execution
curl -X POST http://localhost/api/agenthub/run \
  -H "Content-Type: application/json" \
  -d '{
    "agent_key": "travel_planning_agent",
    "query": "I want to visit Tokyo for 7 days"
  }'

# Expected response
{
  "answer": "Here are 3 travel plans for your 7-day Tokyo trip...",
  "plans": [...],
  "sources": [...],
  "needs_clarification": false,
  "metadata": {...}
}
```

## 📝 Next Steps

1. **Frontend Integration**: Tích hợp agents vào model selector
2. **Agent Toggle UI**: Tạo UI để enable/disable agents
3. **Planning Visualization**: Hiển thị planning steps và plans
4. **API Key Management**: Tạo UI để quản lý API keys
5. **Knowledge Base Integration**: Kết nối agents với KB
6. **More Agents**: Thêm nhiều agents (Research, Code, etc.)

## 🐛 Troubleshooting

### Agent không xuất hiện trong list
- Kiểm tra agent đã được register: `registry.list_all()`
- Kiểm tra logs: `docker compose logs api_server | grep agent`

### Agent execution fails
- Kiểm tra runner function có return đúng format
- Xem logs: `docker compose logs api_server --tail=100`

### Frontend không nhận được agents
- Kiểm tra API: `curl http://localhost/api/agenthub/agents/models`
- Kiểm tra CORS nếu gọi từ domain khác
- Xem browser console cho errors

## 🎉 Kết Luận

AgentHub đã sẵn sàng! Bạn có thể:
✅ Register agents qua code hoặc API
✅ Agents xuất hiện trong model selector
✅ Execute agents như LLM models
✅ Visualize planning process
✅ Toggle agents on/off

Happy building! 🚀
