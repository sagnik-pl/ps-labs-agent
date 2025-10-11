# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Photosphere Labs agent system enables e-commerce brand owners to get actionable insights from their data using natural language queries. Users can ask questions like:
- "Compare my social media performance with these competitors"
- "Analyze competitor ads and suggest product photoshoot guidance"
- "Review product-specific P&L and suggest improvements"
- "Create a media plan for $2000 ad budget this month"
- "What is the brand sentiment on the web?"

This repository implements a multi-agent system that orchestrates specialized agents to answer these queries.

## Project Management

**⚠️ CRITICAL**: This project works VERY closely with Jira for all task management.

### Jira Integration (PRIMARY)

**Jira Project**: PSAGENT (Key: PSAG)
**Board**: https://photospherelabs.atlassian.net/jira/software/projects/PSAG/board
**All Tasks**: https://photospherelabs.atlassian.net/browse/PSAG

**When working on this codebase, you MUST**:

1. **Before Starting Work**: Check Jira board for current tasks and priorities
2. **During Development**: Reference Jira task IDs in commits and comments
3. **When Finding Issues**: Create new Jira tasks immediately (don't just note in code)
4. **When Seeing Improvements**: Add tasks to Jira backlog with appropriate priority (P0/P1/P2/P3)
5. **After Completing Work**: Update Jira task status to Done

**Detailed Jira Workflow**: See [docs/project_management/JIRA_INTEGRATION.md](docs/project_management/JIRA_INTEGRATION.md)

### TODO.md (Secondary)

**TODO Tracking**: This project maintains [TODO.md](TODO.md) for high-level implementation notes:
- Check TODO.md for current work-in-progress implementation details
- Update TODO.md when working on complex multi-step features
- Use TODO.md for technical notes, but use Jira for task tracking

## Commands

### Development Setup
```bash
# Create and activate virtual environment
python3 -m venv agent_venv
source agent_venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials
```

### Running the Application
```bash
# CLI interface (for manual testing)
python main.py

# API server
python api.py
# or
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

### Testing
```bash
# Run tests (when implemented)
pytest

# Code formatting
black .
```

## Architecture

### Multi-Agent System

**Supervisor/Router Agent:**
- Receives user queries with conversation context from Firestore
- Determines which specialized agent(s) to invoke
- Coordinates multi-agent workflows (sequential or parallel)
- Synthesizes responses from multiple agents

**Specialized Agents:**

1. **Data Analytics Agent** - Queries user's analytics data from Glue Data Catalog via Athena
2. **Competitor Intelligence Agent** - Web scraping and Meta Ads Library API for competitor research
3. **Creative Agent** - Ad creative generation using DALL-E/Midjourney
4. **Financial Analyst Agent** - P&L calculations, profitability analysis, forecasting
5. **Media Planner Agent** - Budget optimization, channel allocation, media mix modeling
6. **Sentiment Analyst Agent** - Web scraping, sentiment analysis, brand perception tracking

### Tech Stack

- **LLM Framework**: LangChain/LangGraph
- **LLM Provider**: Claude or OpenAI
- **Context Storage**: Firestore (`conversations/{user_id}/chats/{conversation_id}`)
- **Data Access**: AWS Athena (queries Glue Data Catalog tables)
- **Response Pattern**: TBD (WebSocket streaming vs async job pattern)

### Data Flow

1. User sends natural language query via chat interface (frontend repo)
2. API endpoint receives: `user_id`, `conversation_id`, `message`
3. Load conversation context from Firestore
4. Supervisor agent analyzes query and routes to specialized agent(s)
5. Agents execute tools (Athena queries, web scraping, API calls, etc.)
6. Response formatted and returned to chat interface
7. Updated context saved to Firestore

### Key Principles

- **User Isolation**: All data queries and operations are scoped to `user_id` to prevent data crossovers
- **Context Preservation**: Conversation history maintained in Firestore for multi-turn interactions
- **Tool-Based Architecture**: Each agent has access to specific tools for its domain
