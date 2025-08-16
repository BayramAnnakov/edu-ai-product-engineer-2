# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a multi-agent product management system that classifies user reviews and processes them as bug reports or feature requests. The project implements Homework #3 for AI Product Engineering course.

**Current Status**: Core architecture implemented with PostgreSQL database, Langfuse observability, Redis queue system, and foundational AI agents. The system includes review classification, bug processing with YouTrack integration, feature research capabilities, and human approval workflows via Slack.

## General Rules

- Always use English
- Use comments sparingly. Only comment complex code
- Follow "make simple be simple, complex be possible" principle, avoid over-engineering
- **Check SDK first** - Before building custom solutions, thoroughly check what the SDK provides
- **Use SDK idioms** - Follow the intended patterns and decorators
- **Leverage built-ins** - SDK's parallel execution, exception handling, context management
- **Keep it simple** - SDK handles the complexity, focus on business logic

## Key Commands

### Code Quality Checks
```bash
# Format code
uv run --frozen ruff format .

# Check linting
uv run --frozen ruff check .
uv run --frozen ruff check . --fix  # Auto-fix issues

# Type checking
uv run --frozen pyright
```

### Testing
```bash
# Run tests (when implemented)
PYTEST_DISABLE_PLUGIN_AUTOLOAD="" uv run --frozen pytest
```

## Architecture

### Current Implementation
- **PM Agent System** (`/pm-agent/`): Main application with FastAPI, SQLAlchemy, PostgreSQL
- **MCP YouTrack Server**: FastMCP-based server for YouTrack issue management
- **Slack Service**: Socket Mode bot for human approval workflows
- **Redis Queue System**: Event-driven approval execution with arq workers
- **Database Schema**: Comprehensive PostgreSQL schema with 15+ tables
- **AI Agents**: ReviewClassifier, BugBot, FeatureResearchBot, BugApprovalJudge
- **Observability**: Langfuse integration for LLM tracing and monitoring

### Implemented Components (Homework #3)
1. **Review Classification Agent**: Categorizes reviews as Bug Reports, Feature Requests, or Other
2. **Bug Processing Agent**: Duplicate checking, detailed reports, YouTrack integration
3. **Feature Processing Agent**: Competitor research, feature specs, PM approval via Slack
4. **Orchestrator Pattern**: Manager/Orchestrator pattern with handoff workflows
5. **Human-in-the-Loop**: Guardrails with approval gates and uncertainty assessment

### Implemented Design Patterns
- **Manager/Orchestrator Pattern**: Agent coordination with workflow routing
- **Handoff Workflow Pattern**: Review routing to specialized agents
- **Evaluator-Optimizer Pattern**: Quality assessment with BugApprovalJudge
- **Guardrails with HITL**: Human approval gates with risk assessment
- **Event-Driven Architecture**: Redis queue system for approval execution
- **MCP Integration**: YouTrack tools via Model Context Protocol

## Critical Development Rules

### Package Management
- **ONLY use uv**, NEVER pip
- Installation: `uv add package`
- Running: `uv run tool`
- FORBIDDEN: `uv pip install`, `@latest` syntax

### Code Standards
- Type hints required for all code
- Public APIs must have docstrings
- Functions must be focused and small
- Line length: 88 chars (Ruff default)
- Use `logger.exception()` not `logger.error()` when catching exceptions
- Follow existing patterns exactly

### MCP Server Development
- Use FastMCP v2 framework for all MCP servers
- Tools must be async functions with proper type hints
- Resources use URI patterns (e.g., `papers://folders`)
- Prompts should include clear instructions and examples

### Testing Requirements
- Use anyio for async testing, not asyncio
- New features require tests
- Coverage: test edge cases and errors
- Bug fixes require regression tests

### Code Formatting

1. Ruff
   - Format: `uv run --frozen ruff format .`
   - Check: `uv run --frozen ruff check .`
   - Fix: `uv run --frozen ruff check . --fix`
   - Critical issues:
     - Line length (88 chars)
     - Import sorting (I001)
     - Unused imports
   - Line wrapping:
     - Strings: use parentheses
     - Function calls: multi-line with proper indent
     - Imports: split into multiple lines

2. Type Checking
   - Tool: `uv run --frozen pyright`
   - Requirements:
     - Explicit None checks for Optional
     - Type narrowing for strings
     - Version warnings can be ignored if checks pass

3. Pre-commit
   - Config: `.pre-commit-config.yaml`
   - Runs: on git commit
   - Tools: Prettier (YAML/JSON), Ruff (Python)
   - Ruff updates:
     - Check PyPI versions
     - Update config rev
     - Commit config first

## File Organization
```
lesson3/
├── pm-agent/                      # Main application directory
│   ├── app/                       # Python application
│   │   ├── src/                   # Source code
│   │   │   ├── pm_agents/         # AI agents (ReviewClassifier, BugBot, etc.)
│   │   │   ├── db/                # Database models and services
│   │   │   ├── schemas/           # Pydantic data models
│   │   │   ├── services/          # Business logic and integrations
│   │   │   ├── queues/            # Redis queue system
│   │   │   ├── guardrails/        # Input validation and safety
│   │   │   ├── prompts/           # LLM prompt templates
│   │   │   └── config/            # Configuration management
│   │   ├── alembic/               # Database migrations
│   │   └── pyproject.toml         # Python dependencies
│   ├── mcp_youtrack/              # YouTrack MCP server
│   ├── slack_service/             # Slack approval bot
│   ├── docs/                      # Architecture documentation
│   ├── docker-compose.yml         # Service orchestration
│   └── .env.example               # Environment template
├── data/                          # Input data
│   └── reviews.csv                # User reviews for classification
└── docs/                          # Project documentation
    ├── CLAUDE.md                  # This file
    ├── requirements.md            # Homework specification
    └── notes.md                   # Development notes
```

## Development Workflow

### Starting the System
```bash
# Start all services
cd pm-agent
docker compose up

# Check logs
docker compose logs -f app

# Access Langfuse UI
open http://localhost:3000
```

### Running Tests
```bash
# Run all tests
PYTEST_DISABLE_PLUGIN_AUTOLOAD="" uv run --frozen pytest

# Run specific test categories
uv run pytest tests/test_config_system.py
uv run pytest tests/test_hitl_workflow.py
```

### Database Operations
```bash
# Create migration
docker compose exec app alembic revision --autogenerate -m "Description"

# Apply migrations
docker compose exec app alembic upgrade head

# Check current version
docker compose exec app alembic current
```

## Implementation Status

### ✅ Completed Features
- Multi-agent architecture with specialized AI agents
- PostgreSQL database with comprehensive schema
- Langfuse observability and LLM tracing
- Redis-based approval queue system
- YouTrack integration via MCP
- Slack approval workflows
- Human-in-the-loop guardrails
- Uncertainty assessment and confidence scoring
- Comprehensive test suite

### 🚧 In Progress
- End-to-end workflow orchestration
- Advanced duplicate detection
- Performance optimization

### 📋 Planned Enhancements
- Grafana dashboards for monitoring
- GitHub integration
- Advanced security features
- Automated testing pipelines