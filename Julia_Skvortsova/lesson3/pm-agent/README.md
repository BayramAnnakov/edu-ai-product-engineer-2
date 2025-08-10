# PM Agent System

A multi-agent system for processing user reviews into actionable bug reports and feature requests with human approval gates, comprehensive observability, and event-driven architecture.

## Quick Start

1. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

2. **Start all services**:
   ```bash
   docker compose up -d
   ```

3. **Access Langfuse UI**:
   - URL: http://localhost:3000
   - Create an account on first access
   - Get API keys from Settings → API Keys
   - Update .env with LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY
   - Restart services: `docker compose restart`

4. **Monitor services**:
   ```bash
   # Check all services status
   docker compose ps
   
   # Follow main application logs
   docker compose logs -f app
   
   # Monitor approval workers
   docker compose logs -f approval_worker
   
   # Check Slack approval service
   docker compose logs -f slack_approvals
   ```

5. **Access additional interfaces**:
   - **PgAdmin**: http://localhost:8080 (Database administration)
   - **MCP YouTrack**: http://localhost:8002/mcp/ (Health check)
   - **Langfuse**: http://localhost:3000 (LLM observability)

## Architecture

- **PostgreSQL**: Multi-database setup (pm_agent + langfuse) with persistent volumes
- **Redis**: Event-driven queue system with persistence and memory optimization
- **Langfuse**: Self-hosted LLM observability with health checks
- **Main App**: Python agent system with SQLAlchemy, Alembic, and auto-migration
- **Approval Workers**: Background queue processors with configurable replicas
- **Slack Approvals**: Socket Mode bot for interactive approval workflows
- **MCP YouTrack**: HTTP-based YouTrack integration server
- **PgAdmin**: Database administration interface (development tool)

## Database Management

```bash
# Create new migration
docker compose exec app alembic revision --autogenerate -m "Description"

# Apply migrations (auto-run on startup)
docker compose exec app alembic upgrade head

# Check current migration version
docker compose exec app alembic current

# Access database directly
docker compose exec postgres psql -U agent -d pm_agent

# View database via PgAdmin
open http://localhost:8080
# Use connection: postgres:5432, user: agent, password: from .env
```

## Development

```bash
# Format code
docker compose exec app uv run --frozen ruff format .

# Lint with auto-fix
docker compose exec app uv run --frozen ruff check . --fix

# Type check
docker compose exec app uv run --frozen pyright

# Run tests
docker compose exec app bash -c "PYTEST_DISABLE_PLUGIN_AUTOLOAD='' uv run --frozen pytest"

# Run specific test files
docker compose exec app uv run pytest tests/test_config_system.py
docker compose exec app uv run pytest tests/test_hitl_workflow.py

# Interactive shell in container
docker compose exec app bash
```

## Environment Variables

### Required Configuration
- `OPENAI_API_KEY`: Your OpenAI API key for AI agents
- `YOUTRACK_BASE_URL` & `YOUTRACK_TOKEN`: YouTrack integration credentials
- `SLACK_BOT_TOKEN` & `SLACK_APP_TOKEN`: Slack app for approval workflows

### Langfuse Configuration (Generated on first run)
- `LANGFUSE_PUBLIC_KEY` & `LANGFUSE_SECRET_KEY`: From Langfuse UI Settings
- `LANGFUSE_HOST`: http://langfuse:3000 (container networking)

### Optional Configuration
- `DB_PASSWORD`: PostgreSQL password (default: secure_password)
- `DEBUG`: Enable debug logging (default: false)
- `YOUTRACK_DEFAULT_PROJECT`: Default project key (default: INT)
- `PGADMIN_EMAIL` & `PGADMIN_PASSWORD`: PgAdmin access credentials

## Service Status & Health Checks

```bash
# Check service health
docker compose ps

# Monitor queue metrics
curl http://localhost:8000/queue/status
curl http://localhost:8000/queue/metrics

# Check MCP YouTrack server
curl http://localhost:8002/mcp/

# Monitor all logs
docker compose logs -f
```

## Production Deployment

For production deployment:

1. **Security**: Update all default passwords and secrets
2. **Scaling**: Increase approval worker replicas via `deploy.replicas`
3. **Monitoring**: Enable structured logging and metrics collection
4. **Backup**: Configure PostgreSQL and Redis backup strategies
5. **SSL/TLS**: Add reverse proxy for HTTPS endpoints

## Architecture Documentation

See `docs/architecture.md` for comprehensive system architecture details.

## Contributing

Before contributing:
1. Run the full test suite: `pytest`
2. Format code: `ruff format .`
3. Check linting: `ruff check . --fix`
4. Verify types: `pyright`