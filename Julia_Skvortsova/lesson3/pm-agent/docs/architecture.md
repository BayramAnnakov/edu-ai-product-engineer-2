# Project Architecture

## System Overview

This project implements a multi-agent product management system that processes user reviews and converts them into actionable bug reports and feature requests. The system uses AI agents with human-in-the-loop approval workflows, comprehensive observability, and event-driven architecture to ensure quality, scalability, and accuracy.

## Core Components

### 1. PM Agent System (`/pm-agent/`)

**Main Application Container**
- **Language**: Python 3.11+
- **Framework**: FastAPI with SQLAlchemy ORM
- **Package Manager**: uv (Universal Python Package Manager)
- **Database**: PostgreSQL with Alembic migrations
- **Observability**: Langfuse for LLM tracing and monitoring

**Key Modules**:
- `src/pm_agents/`: Core AI agents (ReviewClassifier, BugBot, FeatureResearchBot)
- `src/db/`: Database models and services
- `src/services/`: Business logic and approval workflows
- `src/queues/`: Redis-based approval execution queue system
- `src/guardrails/`: Input validation and safety checks
- `src/prompts/`: LLM prompt templates and instructions
- `src/schemas/`: Pydantic data models for validation

### 2. MCP YouTrack Server (`/pm-agent/mcp_youtrack/`)

**Purpose**: Model Context Protocol server for YouTrack integration
- **Framework**: FastMCP v2
- **Protocol**: MCP (Model Context Protocol)
- **Integration**: YouTrack REST API
- **Deployment**: Docker container

**Tools Provided**:
- `search_youtrack_issues`: Search existing issues for duplicate detection
- `create_youtrack_issue`: Create new bug reports/feature requests
- `get_youtrack_issue`: Retrieve issue details
- `add_issue_comment`: Add comments to existing issues
- `link_issue_as_duplicate`: Mark issues as duplicates
- `get_issue_comments`: Retrieve issue comments

### 3. Slack Service (`/pm-agent/slack_service/`)

**Purpose**: Human approval workflow integration
- **Mode**: Socket Mode for real-time interactions via `slack_approvals` service
- **Templates**: Jinja2 templates for approval requests
- **Features**: Interactive buttons for approve/reject actions
- **Integration**: Direct database access for approval state management
- **Deployment**: Dedicated Docker service with automatic restart

### 4. Redis Queue System (`/pm-agent/app/src/queues/`)

**Purpose**: Event-driven approval execution system
- **Technology**: Redis + arq (async queue library)
- **Architecture**: Event-driven vs database polling
- **Performance**: ~50ms execution vs 30s polling delay
- **Scalability**: Horizontal worker scaling with load balancing
- **Deployment**: Dedicated `approval_worker` service with configurable replicas
- **Persistence**: Redis with appendonly persistence and memory management

**Key Components**:
- `client.py`: Redis queue client with connection management
- `tasks.py`: Worker task definitions for approval execution
- `metrics.py`: Queue performance monitoring and metrics
- `run_worker.py`: Worker process entry point

## Data Flow Architecture

### High-Level Flow
```
User Reviews → Review Classifier → Routing Decision
                    ↓
    ┌──────────────────────────────────────────┐
    │                                          │
    ▼                                          ▼
Bug Reports                              Feature Requests
    │                                          │
    ▼                                          ▼
BugBot Agent                              Feature Agent
    │                                          │
    ▼                                          ▼
Duplicate Check                        Competitor Research
    │                                          │
    ▼                                          ▼
YouTrack Integration                   PM Approval via Slack
```

### Approval Execution Flow (Event-Driven)
```
Review Processing → Approval Creation → Human Decision
                                           ↓
                                       APPROVED
                                           ↓
                              Redis Queue (Immediate)
                                           ↓
                                  Worker Pool (arq)
                                           ↓
                            Direct MCP Tool Execution
                                           ↓
                              YouTrack/Slack Integration
                                           ↓
                               Status Update + Metrics
```

## Agent Workflow Patterns

### 1. Manager/Orchestrator Pattern
- **Primary Agent**: Routes reviews to specialized agents
- **Workflow Coordination**: Manages handoffs between agents
- **Error Handling**: Ensures graceful failure handling

### 2. Handoff Workflow Pattern
- **Review Classification**: Categorizes incoming reviews
- **Specialized Processing**: Routes to BugBot or FeatureBot
- **Human Approval**: Integrates approval gates

### 3. Evaluator-Optimizer Pattern
- **Content Generation**: Creates structured bug reports/feature specs
- **Quality Assessment**: Uses BugApprovalJudge for confidence scoring
- **Iterative Improvement**: Refines output based on feedback

## Database Schema

The system uses PostgreSQL with SQLAlchemy ORM and Alembic migrations. All tables use UUID primary keys and include comprehensive indexing for performance.

### Core Workflow Tables

**WorkflowRuns**
- Primary workflow execution tracking
- Fields: `id`, `input_text`, `result_text`, `status`, `langfuse_trace_id`, `created_at`, `updated_at`, `completed_at`, `run_metadata`
- Relationships: One-to-many with Reviews
- Indexes: `created_at`, `status`

**Reviews** 
- User review data with classification results
- Fields: `id`, `original_id`, `text`, `category` (enum), `confidence`, `run_id`, `source`, `original_rating`, `processed_at`
- Validation: Confidence must be between 0-1
- Relationships: Belongs to WorkflowRun, has many Tickets and FeatureReports
- Indexes: `category + confidence` composite

**Tickets**
- YouTrack issues created from reviews
- Fields: `id`, `review_id`, `project`, `issue_id`, `issue_number`, `url`, `title`, `duplicate_of`, `similarity_score`, `created_at`
- Constraints: Unique `review_id + project` combination
- Relationships: Belongs to Review, has many FixSuggestions
- Indexes: `project + created_at` composite

### Feature Research Tables

**FeatureReports**
- Feature specifications from research workflow
- Fields: `id`, `review_id`, `summary_md`, `competitor_analysis`, `sources_json`, `feature_spec`, `status`, `slack_thread_ts`, `created_at`, `approved_at`, `approved_by`
- Relationships: Belongs to Review
- Indexes: `status`

**FeatureResearchSessions**
- Main session tracking for feature research workflow
- Fields: `id`, `session_id`, `review_id`, `feature_description`, `project`, `competitors_list`, `max_search_queries`, `require_citations`, `status`, `current_stage`, research metrics, deliverables, approval workflow fields, timestamps, `langfuse_trace_id`
- Relationships: Has many WebResearchFindings, WebSearchQueries, CompetitorAnalysis, FeatureResearchProgress
- Indexes: `review_id + started_at`, `status`, `project + completed_at`, `approval_status`

### Approval System Tables

**Approvals**
- Human approval workflow state with queue integration
- Fields: `id`, `action_type` (enum), `payload_json`, `risk` (enum), `status` (enum), approval metadata (`reviewer_whitelist`, `slack_channel`, `slack_ts`, `slack_message_url`), audit fields (`created_at`, `expires_at`, `decided_at`, `decided_by`, `reason`), execution tracking (`executed_at`, `execution_result`, `execution_error`), tracing (`langfuse_trace_id`, `related_entity_id`)
- Supported Actions: `CREATE_YOUTRACK_ISSUE`, `ADD_YOUTRACK_COMMENT`, `POST_SLACK`
- Risk Levels: `HIGH`, `MEDIUM`, `LOW` (affects queue priority)
- Status Flow: `PENDING` → `APPROVED`/`REJECTED` → `EXECUTED`/`FAILED`
- Indexes: `status + created_at`, `risk + status`

**GuardrailLogs**
- Approval validation and safety check logs
- Fields: `id`, `approval_id`, `check_type`, `rule_name`, `passed`, `details`, `created_at`
- Relationships: Belongs to Approval
- Indexes: `approval_id + passed`

### Issue Search & Duplicate Detection

**IssueSearchSessions**
- YouTrack duplicate detection workflow tracking
- Fields: `id`, `session_id`, `review_id`, `project`, `bug_report_text`, configuration, results, metrics, timestamps
- Relationships: Has many IssueSearchQueries, IssueDuplicateCandidate, IssueSearchProgress
- Indexes: `review_id + started_at`, `project + completed_at`

**IssueSearchQueries**
- Individual search queries executed during duplicate detection
- Fields: `id`, `session_id`, `query`, `search_type`, `results_count`, `execution_time_ms`, `executed_at`
- Indexes: `session_id + executed_at`

**IssueDuplicateCandidate**
- Potential duplicate issues with similarity scoring
- Fields: `id`, `session_id`, `issue_id`, metadata, pre-filtering scores, detailed analysis scores, selection status, timestamps
- Multi-stage analysis: title similarity → keyword overlap → semantic analysis → final scoring
- Indexes: `session_id + final_similarity_score`, `session_id + selected_as_duplicate`

### Supporting Tables

**FixSuggestions**
- Code fix recommendations for bug tickets
- Fields: `id`, `ticket_id`, `file_path`, `snippet`, `diff_md`, `confidence`, `line_start`, `line_end`, `created_at`
- Relationships: Belongs to Ticket

**WebResearchFindings** & **WebSearchQueries** & **CompetitorAnalysis**
- Feature research workflow data with evidence tracking, search execution logs, and competitor feature analysis
- Comprehensive citation and confidence scoring system

**Progress Tracking Tables**
- `IssueSearchProgress` and `FeatureResearchProgress` for workflow stage monitoring
- Track success/failure, timing, and stage-specific metadata

### Key Design Patterns

**UUID Primary Keys**: All tables use UUID for distributed system compatibility
**Audit Trails**: Comprehensive timestamp and user tracking
**JSON Storage**: Flexible payload and metadata storage for dynamic content
**Enum Constraints**: Type-safe status and category management
**Cascade Deletes**: Proper cleanup of related data
**Performance Indexing**: Strategic composite indexes for query optimization
**Validation**: Database-level and application-level data validation

## Technology Stack

### Core Technologies
- **Python 3.11+**: Primary development language
- **FastAPI**: Web framework for API endpoints
- **SQLAlchemy**: ORM for database operations
- **Alembic**: Database migration management
- **PostgreSQL**: Primary data store
- **Docker**: Containerization and deployment

### AI/ML Stack
- **OpenAI GPT-4**: Primary LLM for text processing
- **Anthropic Claude**: Alternative LLM provider
- **Langfuse**: LLM observability and tracing
- **Pydantic**: Data validation and serialization

### Integration Technologies
- **MCP (Model Context Protocol)**: AI agent communication
- **FastMCP**: MCP server framework
- **YouTrack REST API**: Issue tracking integration
- **Slack Socket Mode**: Real-time approval workflows
- **Redis**: Event-driven queue system for approval execution
- **arq**: Async Redis queue library for Python

### Development Tools
- **uv**: Fast Python package manager
- **Ruff**: Python linter and formatter
- **Pyright**: Type checking
- **Docker Compose**: Local development environment

## Security Considerations

### Authentication & Authorization
- API key management for external services
- Environment variable configuration
- Service-to-service authentication

### Data Protection
- Input validation through Pydantic schemas
- Guardrails for malicious content detection
- Sensitive data handling in observability tools

### Rate Limiting & Error Handling
- API rate limit management for external services
- Graceful degradation on service failures
- Comprehensive error logging and monitoring

## Deployment Architecture

### Container Strategy
- **Multi-container deployment** using Docker Compose
- **Service isolation** for different components
- **Volume management** for persistent data

### Services
1. **PostgreSQL**: Database service with persistent volumes and health checks
2. **Redis**: Queue and caching service with persistence and memory optimization
3. **Langfuse**: Self-hosted observability platform with shared PostgreSQL instance
4. **PM Agent App**: Main application container with automatic migrations
5. **Approval Workers**: Background workers for approval execution (configurable replicas)
6. **YouTrack MCP**: HTTP-based MCP server for YouTrack integration
7. **Slack Service**: Socket Mode approval workflow handler with auto-restart
8. **PgAdmin**: Database administration interface (optional development tool)

### Configuration Management
- Environment-based configuration with .env files
- Secure API key management
- Docker networking for service discovery
- Health check-based service startup ordering
- Configurable worker replicas and resource limits
- Development and production environment profiles

## Monitoring & Observability

### LLM Tracing
- **Langfuse Integration**: Complete LLM call tracing with shared PostgreSQL backend
- **Performance Metrics**: Response times, token usage, cost tracking
- **Error Tracking**: Failed requests and retry logic
- **Multi-Service Tracing**: Unified tracing across all components

### Application Monitoring
- **Database Metrics**: Query performance, connection pooling, health checks
- **Queue Metrics**: Queue depth by priority, processing time, success rates
- **API Metrics**: Request/response patterns, health endpoints
- **Business Metrics**: Review processing success rates, approval workflows
- **Worker Metrics**: Execution time, failure rates, throughput, auto-scaling
- **Service Health**: Comprehensive health checks for all services
- **Container Monitoring**: Resource usage, restart policies, service dependencies

## Production Architecture: Performance & Reliability

### Docker Compose Service Architecture

**Service Dependencies & Health Checks**:
- **PostgreSQL**: Primary database with multi-database support (pm_agent + langfuse)
- **Redis**: Persistent queue with memory optimization (256MB limit, LRU eviction)
- **Langfuse**: Observability platform with health checks and experimental features
- **App**: Main service with database migration automation
- **Approval Worker**: Background queue processor with configurable replicas
- **Slack Approvals**: Socket Mode bot with automatic restart
- **MCP YouTrack**: HTTP-based MCP server with health monitoring
- **PgAdmin**: Optional database administration interface

### Supported Action Types

The queue system supports these approval actions via direct MCP calls:

1. **CREATE_YOUTRACK_ISSUE**: Create new issues with full metadata
2. **ADD_YOUTRACK_COMMENT**: Add comments to existing issues
3. **POST_SLACK**: Post messages to Slack channels
4. **LINK_ISSUE_AS_DUPLICATE**: Mark issues as duplicates

### Queue Architecture Details

**Queue Routing by Risk Level**:
- **HIGH** → `approvals:high` (priority processing)
- **MEDIUM** → `approvals:normal` 
- **LOW** → `approvals:low`

**Error Handling**:
- Automatic retries (3 attempts with exponential backoff)
- Dead letter queue for permanent failures
- Timeout handling (5 minutes default)
- Comprehensive error logging and metrics
- Worker auto-restart on failure

**Monitoring Endpoints**:
- `/queue/status` - Current queue depth by priority
- `/queue/metrics` - Execution statistics and performance
- `/health/queue` - Queue service health check
- HTTP health checks for all services

### Deployment Features

**Container Orchestration**:
- Multi-container deployment with Docker Compose
- Service isolation with dedicated networks
- Persistent volumes for data retention
- Automatic service restart policies
- Health check-based service dependencies

**Environment Configuration**:
- Environment variable-based configuration
- Secure defaults with override capability
- API key management via .env files
- Development and production environment support

**Development Tools**:
- Hot reload for application code
- Database administration via PgAdmin
- Structured logging with JSON output
- Type checking and code formatting automation

## Current Implementation Status

### ✅ Production-Ready Features
1. **Multi-Agent Architecture**: ReviewClassifier, BugBot, FeatureResearchBot, UncertaintyJudge
2. **Database Schema**: 15+ tables with comprehensive relationships and indexing
3. **Event-Driven Queues**: Redis-based approval execution with worker scaling
4. **MCP Integration**: YouTrack tools via Model Context Protocol
5. **Human-in-the-Loop**: Slack approval workflows with interactive buttons
6. **Observability**: Langfuse LLM tracing with unified monitoring
7. **Docker Deployment**: Multi-service orchestration with health checks
8. **Testing Framework**: Comprehensive test suite with async support

### 🚧 In Development
1. **End-to-End Orchestration**: Complete workflow automation
2. **Advanced Duplicate Detection**: Semantic similarity using embeddings
3. **Performance Optimization**: Database query optimization and caching

### 📋 Future Enhancements
1. **Enhanced Security**: Advanced guardrails and validation
2. **Additional MCP Tools**: GitHub PR creation, Jira integration
3. **Advanced Monitoring**: Grafana dashboards, Prometheus metrics
4. **Kubernetes Deployment**: Production-scale orchestration
5. **CI/CD Pipeline**: Automated testing and deployment