# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A2A (Application-to-Application) Agent for inter-service communication. This Python FastAPI application provides a framework for agents to communicate with each other, exchange data, and coordinate activities.

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Start development server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start production server
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Alternative using pyproject.toml scripts
python -m pip install -e .
python -m app.main  # or use the configured scripts

# Run tests (when pytest is configured)
pytest

# Format code (if black/flake8 are added)
black app/
flake8 app/
```

## Project Structure

```
app/
├── agent/              # Core A2A agent implementation
│   ├── __init__.py
│   └── a2a_agent.py   # Main agent class with async communication
├── routes/            # FastAPI route handlers
│   ├── __init__.py
│   ├── agent_routes.py # Agent communication endpoints  
│   └── data_routes.py  # Sample data endpoints
├── data/              # Sample data and generators
│   ├── __init__.py
│   └── sample_data.py # Korean sample data with generators
├── utils/             # Utility modules
│   ├── __init__.py
│   ├── config.py      # Pydantic settings management
│   └── logger.py      # Loguru-based logging
└── main.py            # FastAPI application entry point
```

## Architecture

### Core Components

1. **A2AAgent Class** (`app/agent/a2a_agent.py`): Async agent implementation
   - HTTP client-based communication with other agents
   - Pydantic models for message validation
   - Connection management and message queuing
   - Sample data generation and handling

2. **FastAPI Routes**:
   - `/api/agent/*` - Agent communication (handshake, messages, connections)
   - `/api/data/*` - Sample data endpoints (users, orders, products, system, metrics)
   - `/health` - Health check endpoint
   - `/docs` - Auto-generated OpenAPI documentation

3. **Message Types**:
   - `ping/pong` - Connection testing
   - `data_request/data_response` - Data exchange
   - Custom message types can be added

### Key Features

- **Async Agent Communication**: HTTP-based with httpx client
- **Pydantic Data Validation**: Type-safe message and data models
- **Korean Sample Data**: Realistic data with dynamic generation
- **Connection Management**: Track and maintain agent connections
- **Message Queue**: Store and process incoming messages
- **Health Monitoring**: System status and metrics endpoints
- **Auto Documentation**: FastAPI's built-in Swagger/OpenAPI docs

## Configuration

Environment variables (see `.env`):
- `PORT=28000` - Server port
- `AGENT_ID=agent-py-001` - Unique agent identifier  
- `AGENT_NAME=A2A_Python_Agent` - Human-readable agent name
- `LOG_LEVEL=INFO` - Logging level
- `ENVIRONMENT=development` - Environment mode

## AI Integration (Gemini CLI)

### Setup
```bash
# Install Gemini CLI
npm install -g @google/gemini-cli

# Setup authentication
gemini  # Follow authentication prompts

# Or use API key
export GEMINI_API_KEY="your_api_key"

# Run setup script
./setup_gemini.sh
```

### AI Features
- **Smart Messaging**: AI optimizes agent communication
- **Code Analysis**: Analyze Python code for improvements
- **Data Insights**: AI analyzes business data patterns
- **Documentation**: Auto-generate API documentation
- **Translation**: Multi-language support
- **Auto-Response**: AI suggests/generates responses

### AI Endpoints
- `POST /api/ai/chat` - Free-form AI conversation
- `POST /api/ai/analyze-code` - Code analysis and review
- `POST /api/ai/analyze-data` - Business data analysis
- `POST /api/ai/generate-docs` - Auto documentation
- `POST /api/ai/suggest-improvements` - Improvement suggestions
- `POST /api/ai/translate` - Text translation
- `GET /api/ai/status` - AI service status

### Intelligent Agent Features
- **IntelligentA2AAgent**: AI-enhanced agent class
- **Smart message optimization**: AI improves message structure
- **Automated insights**: AI analyzes system patterns
- **Intelligent responses**: AI suggests appropriate responses

## Example Usage

### Run AI Demos
```bash
# Interactive AI workflow demo
python examples/ai_workflow_demo.py

# Test all AI endpoints
python examples/test_ai_endpoints.py

# Start server and test
./run_dev.sh
curl -X POST http://localhost:28000/api/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Explain A2A architecture"}'
```

### Agent + AI Integration
```python
from app.agent.intelligent_agent import IntelligentA2AAgent

# Create AI-powered agent
agent = IntelligentA2AAgent("smart-agent", "AI_Agent")

# Send smart message (AI optimized)
response = await agent.smart_send_message(
    "target-agent", "data_request", {"type": "analytics"}
)

# Get AI insights
insights = await agent.get_ai_insights()
```



## AI Collaboration (Claude Code + Gemini)
Claude Code can collaborate with Gemini to solve complex problems through bash commands. This enables a problem-solving dialogue between the two AI assistants.
### How to Collaborate
1. **Execute Gemini commands via bash**: Use the `gemini` command in bash to interact with Gemini
2. **Pass prompts as arguments**: Provide your question or request as arguments to the gemini command
3. **Iterative problem solving**: Use the responses from Gemini to refine your approach and continue the dialogue
### Example Usage
```bash
# Ask Gemini for help with a specific problem
gemini "How should I optimize this Flutter widget for better performance?"
# Request code review or suggestions
gemini "Review this GetX controller implementation and suggest improvements"
# Collaborate on debugging
gemini "This error occurs when running flutter build ios. What could be the cause?"
```
### Collaboration Workflow
1. **Identify complex problems**: When encountering challenging issues, consider leveraging Gemini's perspective
2. **Formulate clear questions**: Create specific, context-rich prompts for better responses
3. **Iterate on solutions**: Use responses to refine your approach and ask follow-up questions
4. **Combine insights**: Merge insights from both Claude Code and Gemini for comprehensive solutions