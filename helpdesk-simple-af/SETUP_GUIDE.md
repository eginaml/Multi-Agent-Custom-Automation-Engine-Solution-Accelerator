# Azure AI Foundry Setup Guide

This guide walks you through setting up all Azure resources required for **helpdesk-simple-af**.

---

## ❓ Do I Need to Create Azure AI Search Through Foundry?

**Short answer: No, but you MUST add it as a connection in Foundry.**

Here's why:

The Agent Framework accesses Azure AI Search through **Foundry Connections** — not directly via API key. The `RAGAgent` calls:
```python
async for connection in self.project_client.connections.list():
    if connection.type == ConnectionType.AZURE_AI_SEARCH:
        # Uses this connection to set up the search tool
```

You have **two options**:

| Option | Description | When to use |
|--------|-------------|-------------|
| **Option A** (Recommended) | Create Azure AI Search **from within Foundry** — connection is auto-created | Starting fresh |
| **Option B** | Create Azure AI Search **independently**, then add a connection in Foundry manually | Already have a Search resource |

Both options result in the same outcome: a Foundry project with a connected Azure AI Search instance.

---

## 📋 What You Need to Create

```
Azure Resources:
├── Azure AI Foundry Hub
│   └── Azure AI Foundry Project        ← you'll run agents from here
│       ├── Azure OpenAI Connection     ← GPT-4o + embeddings
│       ├── Azure AI Search Connection  ← helpdesk knowledge base
│       └── (Azure DevOps → via PAT, not Foundry)
│
└── Azure DevOps Organization           ← created separately, connected via PAT
```

---

## 🛠️ Step-by-Step Setup

---

### STEP 1: Create Azure AI Foundry Hub & Project

1. Go to [https://ai.azure.com](https://ai.azure.com)

2. Sign in with your Azure account

3. Click **"+ Create project"**

4. Fill in:
   - **Project name:** `helpdesk-project`
   - **Hub:** Click **"Create new hub"**
     - Hub name: `helpdesk-hub`
     - Subscription: *your subscription*
     - Resource group: `helpdesk-rg` (create new)
     - Region: `East US` (or your preferred region)

5. Click **"Create"** — this takes 2-3 minutes

6. Once created, you're inside your Foundry project

---

### STEP 2: Deploy Azure OpenAI Models

Still inside your Foundry project:

1. Click **"Models + endpoints"** in the left sidebar

2. Click **"+ Deploy model"**

3. Deploy **GPT-4o**:
   - Search for `gpt-4o`
   - Select `gpt-4o`
   - Click **"Confirm"**
   - Deployment name: `gpt-4o` (keep the default)
   - Click **"Deploy"**

4. Deploy **text-embedding-3-large**:
   - Click **"+ Deploy model"** again
   - Search for `text-embedding-3-large`
   - Select it
   - Deployment name: `text-embedding-3-large`
   - Click **"Deploy"**

5. Wait for both deployments to show **"Succeeded"**

---

### STEP 3: Set Up Azure AI Search

Choose **Option A** (recommended) or **Option B**.

---

#### Option A: Create Azure AI Search from Foundry (Recommended)

1. Still in your Foundry project, click **"Connected resources"** in the left sidebar

2. Click **"+ New connection"**

3. Select **"Azure AI Search"**

4. Click **"Create new Azure AI Search"** (bottom of the panel)

5. Fill in:
   - **Service name:** `helpdesk-search`
   - **Location:** Same as your Foundry hub (e.g., East US)
   - **Pricing tier:** `Basic` (sufficient for development)

6. Click **"Create"** — this takes 1-2 minutes

7. Once created, it automatically appears as a connection. Give it the name:
   - **Connection name:** `search-connection`

8. Click **"Add connection"**

✅ Done! Azure AI Search is created AND connected to Foundry.

---

#### Option B: Connect an Existing Azure AI Search

If you already have an Azure AI Search resource:

1. In your Foundry project, click **"Connected resources"**

2. Click **"+ New connection"**

3. Select **"Azure AI Search"**

4. Under **"Select from your Azure resources"**, find your existing Search service

5. Set:
   - **Connection name:** `search-connection`
   - **Authentication:** `API Key` (for development)

6. Click **"Add connection"**

✅ Done! Your existing Azure AI Search is connected to Foundry.

---

### STEP 4: Get Your Configuration Values

#### 4a. Get the Foundry Project Endpoint

1. In your Foundry project, click **"Overview"**

2. Look for **"Project connection string"** or **"API endpoint"**

3. It looks like:
   ```
   https://eastus.api.azureml.ms
   ```
   or
   ```
   https://YOUR-HUB.eastus.api.azureml.ms
   ```

4. Copy this — this is `AZURE_AI_PROJECT_ENDPOINT`

---

#### 4b. Get Azure OpenAI Credentials

1. In Foundry, click **"Models + endpoints"**

2. Click on your `gpt-4o` deployment

3. Look for the **connection details** panel on the right

4. Copy:
   - **Target URI** → this is `AZURE_OPENAI_ENDPOINT`
   - **Key** → this is `AZURE_OPENAI_API_KEY`

---

#### 4c. Get Azure AI Search Credentials

1. Go to the [Azure Portal](https://portal.azure.com)

2. Navigate to your Search service (`helpdesk-search`)

3. Click **"Keys"** in the left menu

4. Copy:
   - **URL** from the Overview page → `AZURE_SEARCH_ENDPOINT`
   - **Primary admin key** → `AZURE_SEARCH_API_KEY`

---

#### 4d. Get Subscription & Resource Group Info

1. Go to [Azure Portal](https://portal.azure.com)

2. Navigate to your resource group (`helpdesk-rg`)

3. From the URL or Overview, copy:
   - **Subscription ID** → `AZURE_SUBSCRIPTION_ID`
   - **Resource group name** → `AZURE_RESOURCE_GROUP` (e.g., `helpdesk-rg`)

---

### STEP 5: Verify Connection Name

The connection name you set in Step 3 must match `.env`. Verify it:

1. In Foundry, click **"Connected resources"**

2. Find your Azure AI Search connection

3. Note the **Name** column — by default you set it to `search-connection`

4. This value goes in `.env` as:
   ```bash
   AZURE_AI_SEARCH_CONNECTION_NAME=search-connection
   ```

> ⚠️ If your connection name is different, update `AZURE_AI_SEARCH_CONNECTION_NAME` to match exactly.

---

### STEP 6: Set Up Azure DevOps

Azure DevOps is **not managed through Foundry** — it uses a Personal Access Token (PAT).

1. Go to `https://dev.azure.com/YOUR-ORG`

2. Click your **profile icon** (top right) → **Personal access tokens**

3. Click **"+ New Token"**

4. Configure:
   - **Name:** `Helpdesk Backend`
   - **Expiration:** 90 days (or your preference)
   - **Scopes:** Custom defined
     - ✅ Work Items: **Read, Write**

5. Click **"Create"** and **copy the token immediately**

6. Note down:
   - **Org URL:** `https://dev.azure.com/YOUR-ORG`
   - **Project name:** the project where tickets will be created
   - **PAT:** the token you just copied

---

### STEP 7: Fill in .env

Now you have everything. Copy `.env.example` and fill in all values:

```bash
# Windows
copy .env.example .env

# Mac/Linux
cp .env.example .env
```

Open `.env` and fill in:

```bash
# ============================================
# Azure AI Foundry Project Configuration
# ============================================
AZURE_AI_PROJECT_ENDPOINT=https://eastus.api.azureml.ms    # from Step 4a
AZURE_AI_PROJECT_NAME=helpdesk-project                      # name you chose
AZURE_SUBSCRIPTION_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx  # from Step 4d
AZURE_RESOURCE_GROUP=helpdesk-rg                            # from Step 4d

# ============================================
# Azure OpenAI Configuration
# ============================================
AZURE_OPENAI_ENDPOINT=https://YOUR-RESOURCE.openai.azure.com/  # from Step 4b
AZURE_OPENAI_API_KEY=your-openai-api-key                       # from Step 4b
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-08-01-preview
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large

# ============================================
# Azure AI Search Configuration
# ============================================
AZURE_SEARCH_ENDPOINT=https://helpdesk-search.search.windows.net  # from Step 4c
AZURE_SEARCH_API_KEY=your-search-api-key                           # from Step 4c
AZURE_SEARCH_INDEX_NAME=helpdesk-docs
AZURE_AI_SEARCH_CONNECTION_NAME=search-connection                  # from Step 5

# ============================================
# Azure DevOps Configuration
# ============================================
AZURE_DEVOPS_ORG_URL=https://dev.azure.com/YOUR-ORG  # from Step 6
AZURE_DEVOPS_PROJECT=YOUR-PROJECT-NAME               # from Step 6
AZURE_DEVOPS_PAT=your-pat-token                      # from Step 6
```

---

### STEP 8: Run Setup Script

```bash
# Create search index and upload mock data
python scripts/setup_search.py
```

Expected output:
```
============================================================
Azure AI Search Setup - Helpdesk Simple (AF)
============================================================
INFO: Loading documents from: data/helpdesk_docs.json
INFO: ✓ Loaded 3 documents from JSON file
INFO: Creating Azure AI Search index...
INFO: ✓ Created index: helpdesk-docs
INFO: Uploading mock documents...
INFO: Generating embedding for: Password Reset Guide
INFO: Generating embedding for: VPN Setup Instructions
INFO: Generating embedding for: Printer Setup and Configuration
INFO: ✓ Uploaded 3/3 documents successfully
INFO: ✓ Setup completed successfully!
============================================================
```

---

### STEP 9: Run the Application

```bash
python app.py
```

Expected startup:
```
INFO: Starting Simple Helpdesk (Agent Framework)
INFO: Initializing agents...
INFO: Initialized Azure credentials
INFO: Initialized AgentsClient
INFO: Using search connection: search-connection
INFO: Created RAG agent (id=asst_xxx) with Azure AI Search tool
INFO: ✓ RAG agent initialized
INFO: Created Ticket agent (id=asst_yyy) with function calling
INFO: ✓ Ticket agent initialized
INFO: ✓ Agents initialized successfully
INFO: Server running at http://0.0.0.0:8000
INFO: API Documentation: http://localhost:8000/docs
```

---

## 🧪 Test It Works

```bash
# Test RAG query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"How do I reset my password?\"}"

# Test ticket creation
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Create a ticket: VPN not connecting\"}"

# Test streaming
curl -N -X POST http://localhost:8000/query/stream \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"How do I set up the printer?\"}"
```

---

## ❗ Troubleshooting

### Error: "No Azure AI Search connection found"

**Cause:** The connection name in `.env` doesn't match Foundry.

**Fix:**
1. Go to Foundry → **Connected resources**
2. Find your Azure AI Search connection
3. Copy the exact **Name** value
4. Update `.env`: `AZURE_AI_SEARCH_CONNECTION_NAME=<exact name>`

---

### Error: "Failed to open agent: 401 Unauthorized"

**Cause:** Wrong project endpoint or credentials.

**Fix:**
1. Verify `AZURE_AI_PROJECT_ENDPOINT` — go to Foundry → Overview → copy the endpoint
2. Verify you're logged in with the right Azure account
3. Try running: `az login` to refresh credentials

---

### Error: "ResourceNotFound: The index 'helpdesk-docs' was not found"

**Cause:** Setup script hasn't been run yet.

**Fix:**
```bash
python scripts/setup_search.py
```

---

### Error: "TF400813: The user is not authorized" (DevOps)

**Cause:** PAT doesn't have correct permissions.

**Fix:**
1. Go to Azure DevOps → Profile → Personal access tokens
2. Edit your PAT or create a new one
3. Ensure **Work Items: Read, Write** is checked
4. Update `AZURE_DEVOPS_PAT` in `.env`

---

### Agent takes a long time to start

**Cause:** Normal on first run — agents are being registered with Azure AI Foundry.

**Note:** Subsequent starts are faster as agents are cached.

---

## 📋 Resource Checklist

Before running, confirm you have:

- [ ] Azure AI Foundry project created
- [ ] GPT-4o deployed
- [ ] text-embedding-3-large deployed
- [ ] Azure AI Search created and connected to Foundry
- [ ] Connection name matches `.env`
- [ ] Azure DevOps PAT created with Work Items: Read/Write
- [ ] `.env` file filled in with all values
- [ ] `python scripts/setup_search.py` has been run successfully

---

## 🔗 Useful Links

- [Azure AI Foundry Portal](https://ai.azure.com)
- [Azure Portal](https://portal.azure.com)
- [Azure DevOps](https://dev.azure.com)
- [Azure AI Agents SDK Docs](https://learn.microsoft.com/azure/ai-services/agents/)
- [Azure AI Search Docs](https://learn.microsoft.com/azure/search/)
