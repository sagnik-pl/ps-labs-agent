# Photosphere Labs Agent System

Multi-agent system for natural language analytics with real-time streaming responses.

## Overview

This system provides an intelligent conversational interface for data analytics using a multi-agent architecture. It processes natural language queries, retrieves data from various sources, and returns actionable insights with context and recommendations.

## Features

- **Real-time WebSocket Communication** - Streaming progress updates and responses
- **Multi-Agent Architecture** - Specialized agents for planning, data retrieval, and interpretation
- **Conversation Management** - Persistent conversation history with auto-generated titles
- **Data Source Integration** - AWS Athena, Glue Data Catalog, and extensible for other sources
- **Context-Aware Responses** - Domain knowledge integration and benchmarking

## Quick Start

### Installation

```bash
# Create virtual environment
python3 -m venv agent_venv
source agent_venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Configure required environment variables
# - OpenAI API key
# - Firebase credentials (via AWS Secrets Manager)
# - AWS credentials (Athena, S3)
# - Environment settings (development/production)
```

### Running the Server

```bash
# Activate environment
source agent_venv/bin/activate

# Start WebSocket API server
python api_websocket.py

# Server runs on http://localhost:8000
```

## API Documentation

### WebSocket Endpoint

**Connect:** `ws://localhost:8000/ws/{user_id}/{conversation_id}`

**Send Message:**
```json
{
  "query": "Your question here",
  "conversation_id": "conv-123"
}
```

**Receive Events:**
- `started` - Query processing started
- `progress` - Progress updates with stage information
- `conversation_metadata` - Conversation title and date
- `completed` - Final response with insights
- `error` - Error information

### REST Endpoints

- `GET /` - Health check
- `GET /conversations/{user_id}` - List user conversations
- `GET /conversations/{user_id}/{conversation_id}/messages` - Get conversation messages

## Architecture

The system uses a LangGraph-based multi-agent workflow:

1. **Planner** - Analyzes query and creates execution plan
2. **Router** - Determines which agents to invoke
3. **Data Retrieval** - SQL generation, validation, and execution
4. **Interpretation** - Analyzes data with domain knowledge and provides insights
5. **Validation** - Quality control for SQL and interpretations

For detailed architecture documentation, see [CLAUDE.md](CLAUDE.md).

## Development

### Environment Variables

Key configuration options:
- `ENVIRONMENT` - `development` or `production`
- `OPENAI_API_KEY` - OpenAI API key for LLM
- `FIREBASE_SECRET_NAME` - AWS Secrets Manager secret name
- `AWS_REGION` - AWS region for services
- `GLUE_DATABASE` - AWS Glue database name
- `ATHENA_S3_OUTPUT_LOCATION` - S3 path for Athena results

### Testing

```bash
# Test WebSocket connection
python test_websocket.py

# Run with specific query
python main.py
```

## Documentation

- [CLAUDE.md](CLAUDE.md) - Complete architecture and codebase documentation
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - API reference and examples
- [FRONTEND_INTEGRATION_PLAN.md](FRONTEND_INTEGRATION_PLAN.md) - Frontend integration guide

## License

Proprietary - Photosphere Labs
