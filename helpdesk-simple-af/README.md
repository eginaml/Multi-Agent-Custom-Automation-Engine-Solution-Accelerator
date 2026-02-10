# Simple Helpdesk Backend (Agent Framework Edition) 🤖

A multi-agent helpdesk system powered by **Azure AI Agent Framework** with RAG (Retrieval-Augmented Generation) and automated ticket creation capabilities.

## 🎯 Overview

This is an **upgraded version** of `helpdesk-simple` that uses the Azure AI Agent Framework instead of custom agent implementations. It provides:

- **Framework-Managed Agents**: Uses Azure AI Agents SDK for production-ready capabilities
- **Native Azure AI Search Integration**: Built-in tool for knowledge base queries
- **Function Calling**: Automatic parameter extraction for ticket creation
- **Conversation Threading**: Multi-turn conversations with state management
- **Streaming Responses**: Real-time response generation
- **Production-Ready**: Built-in error handling, retry logic, and telemetry

---

## 🏗️ Architecture

```
┌─────────────┐
│   FastAPI   │  HTTP API Layer
└──────┬──────┘
       │
┌──────▼──────────┐
│  Orchestrator   │  Intent Classification & Routing
└──────┬──────────┘
       │
       ├─────────────┬─────────────┬──────────────┐
       │             │             │              │
┌──────▼──────┐ ┌───▼────────┐ ┌──▼────────┐ ┌──▼──────┐
│  RAG Agent  │ │Ticket Agent│ │Status Check│ │ (Future)│
│ (Framework) │ │(Framework) │ │  (Simple)  │ │ Agents  │
└──────┬──────┘ └───┬────────┘ └────────────┘ └─────────┘
       │            │
┌──────▼────────────▼──────┐
│   Azure AI Services      │
│ - Agent Framework Client │
│ - Azure AI Search Tool   │
│ - Function Calling       │
│ - Azure DevOps API       │
└──────────────────────────┘
```

---

## 📁 Project Structure

```
helpdesk-simple-af/
├── agents/                     # Agent Framework implementations
│   ├── base_agent.py          # Base agent with lifecycle management
│   ├── rag_agent.py           # RAG agent with Azure AI Search tool
│   ├── ticket_agent.py        # Ticket agent with function calling
│   ├── intent_classifier.py   # Intent classification (pattern-based)
│   └── orchestrator.py        # Multi-agent orchestration
│
├── api/                        # REST API layer
│   └── router.py              # FastAPI endpoints (sync + streaming)
│
├── config/                     # Configuration
│   └── settings.py            # Environment settings
│
├── models/                     # Pydantic models
│   ├── requests.py            # Request models
│   └── responses.py           # Response models
│
├── services/                   # Service layer
│   ├── foundry_service.py     # Azure AI Foundry client
│   ├── openai_service.py      # Azure OpenAI wrapper
│   ├── search_service.py      # Azure AI Search (for setup)
│   └── devops_service.py      # Azure DevOps API
│
├── tools/                      # Function tools
│   └── devops_tool.py         # DevOps ticket creation tool
│
├── data/                       # Mock data
│   ├── helpdesk_docs.json     # Sample helpdesk articles
│   └── README.md              # Data management guide
│
├── scripts/                    # Setup scripts
│   └── setup_search.py        # Azure AI Search index setup
│
├── app.py                      # Main application entry point
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
└── README.md                   # This file
```

---

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.10+
- Azure subscription
- Azure AI Foundry project
- Azure OpenAI resource
- Azure AI Search resource
- Azure DevOps organization (with PAT)

### 2. Installation

```bash
# Clone the repository (or navigate to helpdesk-simple-af/)
cd helpdesk-simple-af

# Create virtual environment
python -m venv venv

# Activate - Windows:
venv\Scripts\activate

# Activate - Mac/Linux:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

> **Full Azure setup guide:** See [SETUP_GUIDE.md](SETUP_GUIDE.md) — covers Foundry project, Azure AI Search, connections, and .env configuration.

### 3. Configuration

```bash
# Copy environment template (Windows)
copy .env.example .env

### 4. Setup Azure AI Search Index

```bash
# Create index and upload mock data
python scripts/setup_search.py
```

### 5. Run the Application

```bash
# Start the server
python app.py

# Server will run at http://localhost:8000
# API docs at http://localhost:8000/docs
```

---

## 📡 API Endpoints

### **POST /query** (Non-Streaming)

Process a user query and return the complete response.

**Request:**
```json
{
  "message": "How do I reset my password?",
  "thread_id": "thread_abc123"  // Optional for multi-turn
}
```

**Response:**
```json
{
  "intent": "rag",
  "message": "Here's how to reset your password:\n\n1. Go to...",
  "sources": [
    {
      "title": "Password Reset Guide",
      "content": "...",
      "score": 0.95
    }
  ],
  "thread_id": "thread_abc123",
  "fallback": false,
  "suggest_ticket": false
}
```

### **POST /query/stream** (Streaming)

Stream the response in real-time using Server-Sent Events (SSE).

**Request:** Same as `/query`

**Response:** SSE stream
```
data: {"type": "text_delta", "text": "Here's how", "intent": "rag"}
data: {"type": "text_delta", "text": " to reset", "intent": "rag"}
...
data: {"type": "final", "message": "...", "sources": [...]}
data: {"type": "done"}
```

### **GET /health**

Health check endpoint.

---

## 🎨 Agent Framework Features

### **1. RAG Agent**

**File:** `agents/rag_agent.py`

**Features:**
- Uses native Azure AI Search tool (no manual search calls)
- Automatic retrieval and generation
- Streaming responses
- Fallback detection

**How it works:**
```python
# Agent created with built-in search tool
agent = await client.create_agent(
    model="gpt-4o",
    tools=[{"type": "azure_ai_search"}],
    tool_resources={
        "azure_ai_search": {
            "indexes": [{
                "index_connection_id": connection_id,
                "index_name": "helpdesk-docs",
                "query_type": "vector_semantic_hybrid"
            }]
        }
    }
)

# Framework handles: search → retrieve → generate
async for update in agent.invoke("How do I..."):
    print(update)
```

### **2. Ticket Agent**

**File:** `agents/ticket_agent.py`

**Features:**
- Function calling for ticket creation
- Automatic parameter extraction
- Type-safe tool definitions
- Confirmation workflow

**How it works:**
```python
# Define DevOps function tool
tool = {
    "type": "function",
    "function": {
        "name": "create_devops_ticket",
        "parameters": {
            "title": {"type": "string"},
            "description": {"type": "string"},
            "priority": {"type": "integer"}
        }
    }
}

# Agent automatically:
# 1. Extracts parameters from natural language
# 2. Calls the function
# 3. Returns structured result
```

### **3. Base Agent Lifecycle**

**File:** `agents/base_agent.py`

**Features:**
- Async context management
- Resource cleanup
- Credential management
- Error handling

**Usage:**
```python
async with RAGAgent() as agent:
    async for update in agent.invoke("question"):
        print(update)
# Automatic cleanup on exit
```

---

## 🔧 Configuration

### **Key Environment Variables**

#### **Azure AI Foundry**
```bash
AZURE_AI_PROJECT_ENDPOINT=https://eastus.api.azureml.ms
AZURE_AI_PROJECT_NAME=helpdesk-project
AZURE_SUBSCRIPTION_ID=...
AZURE_RESOURCE_GROUP=helpdesk-rg
```

#### **Azure AI Search**
```bash
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_API_KEY=...
AZURE_SEARCH_INDEX_NAME=helpdesk-docs
AZURE_AI_SEARCH_CONNECTION_NAME=search-connection
```

#### **Agent Configuration**
```bash
AGENT_TEMPERATURE=0.1
RAG_TOP_K=2
RAG_SCORE_THRESHOLD=0.7
RAG_QUERY_TYPE=vector_semantic_hybrid
ENABLE_CONVERSATION_THREADING=true
```

---

## 🧪 Testing

### **Test RAG Query**

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I reset my password?"}'
```

### **Test Ticket Creation**

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"message": "Create a ticket: VPN connection keeps dropping"}'
```

### **Test Streaming**

```bash
curl -N http://localhost:8000/query/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I set up the printer?"}'
```

---

## 🔄 Migration from helpdesk-simple

### **What Changed?**

| Component | Before (Custom) | After (Framework) |
|-----------|----------------|-------------------|
| **RAG Agent** | Manual search + LLM calls | Native Azure AI Search tool |
| **Ticket Agent** | Manual LLM extraction + API | Function calling tool |
| **Orchestrator** | Simple routing | Framework-based with lifecycle |
| **API** | Sync responses | Async + streaming support |
| **State** | Stateless | Thread-based conversations |
| **Error Handling** | Manual | Framework-managed |

### **What Stayed the Same?**

- ✅ Intent classifier (pattern-based)
- ✅ Data folder structure
- ✅ Setup scripts
- ✅ Service layer (OpenAI, DevOps)
- ✅ API endpoints (backward compatible)

---

## 📚 Key Differences vs Custom Implementation

### **Benefits of Agent Framework**

✅ **Production-Ready**
- Built-in retry logic
- Automatic error handling
- Telemetry and monitoring

✅ **Less Code**
- ~40% less boilerplate
- No manual tool orchestration
- Framework handles streaming

✅ **Better Integration**
- Native Azure AI Search tool
- Managed Identity support
- Foundry connection discovery

✅ **Advanced Features**
- Conversation threading
- Function calling
- Code Interpreter (optional)

### **Trade-offs**

⚠️ **More Complex**
- Additional dependencies
- Framework learning curve
- Async/await everywhere

⚠️ **Setup Requirements**
- Need Azure AI Foundry project
- More environment variables
- Additional Azure resources

---

## 🛠️ Development

### **Adding a New Agent**

1. **Create agent class:**
```python
from agents.base_agent import BaseAgent

class MyAgent(BaseAgent):
    async def _after_open(self):
        # Create agent with tools
        agent = await self._client.create_agent(...)
        self._agent_id = agent.id

    async def invoke(self, message, thread_id=None):
        # Process and stream responses
        async for update in ...:
            yield update
```

2. **Register in orchestrator:**
```python
# In orchestrator.initialize()
self._my_agent = MyAgent()
await self._my_agent.open()
```

### **Adding a New Tool**

1. **Define tool:**
```python
# In tools/my_tool.py
MY_TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "my_function",
        "parameters": {...}
    }
}

async def my_function(param1, param2):
    # Tool implementation
    return {"result": "..."}
```

2. **Add to agent:**
```python
agent = await self._client.create_agent(
    tools=[MY_TOOL_DEFINITION],
    ...
)
```

---

## 📖 Documentation

- **Azure AI Agent Framework**: [Microsoft Docs](https://learn.microsoft.com/azure/ai-services/agents/)
- **Azure AI Foundry**: [Foundry Documentation](https://learn.microsoft.com/azure/ai-studio/)
- **Azure AI Search**: [Search Documentation](https://learn.microsoft.com/azure/search/)

---

## 🤝 Contributing

This is a solution accelerator. Feel free to customize and extend for your use case.

---

## 📄 License

MIT License

---

**Built with Azure AI Agent Framework** 🚀
