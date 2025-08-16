"""
Modern Pydantic-based configuration for PM Agent
"""
import os
import yaml
from pathlib import Path
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic.fields import FieldInfo

# ============================================================================
# NESTED CONFIG MODELS
# ============================================================================

class AppInfo(BaseModel):
    name: str = "PM Agent"
    version: str = "1.0.0"
    environment: str = Field(default="development", description="Environment: development, staging, production")

class ModelsConfig(BaseModel):
    """Model configurations for different agents"""
    default_chat: str = "gpt-4.1-2025-04-14"
    default_nano: str = "gpt-4.1-nano-2025-04-14"
    
    # Agent-specific models
    bug_bot: str = "gpt-4.1-2025-04-14"
    review_classifier: str = "gpt-4.1-nano-2025-04-14"
    bug_approval_judge: str = "gpt-4.1-2025-04-14"
    approval_executor: str = "gpt-4.1-2025-04-14"
    
    # Feature Research Bot models
    feature_research_bot: str = "gpt-4.1-nano-2025-04-14"  # Main orchestrator
    feature_research_planner: str = "gpt-4.1-2025-04-14"  # Research planning
    feature_web_researcher: str = "gpt-4.1-2025-04-14"  # Web search execution (needs stronger model)
    feature_competitor_analyst: str = "gpt-4.1-nano-2025-04-14"  # Analysis
    feature_spec_writer: str = "gpt-4.1-2025-04-14"  # Report generation

class MCPConfig(BaseModel):
    """MCP server configuration"""
    youtrack_url: str = "http://mcp_youtrack:8002/mcp"
    timeout_seconds: int = 30
    
    @validator('youtrack_url')
    def validate_url(cls, v):
        if not v.startswith('http'):
            raise ValueError('YouTrack URL must start with http')
        return v

class DatabaseConfig(BaseModel):
    """Database configuration"""
    url_env_var: str = "DATABASE_URL"
    pool_size: int = 10
    timeout_seconds: int = 30

class LangfuseConfig(BaseModel):
    """Langfuse tracing configuration"""
    project_name: str = "pm-agent"
    enabled: bool = True
    trace_all_agents: bool = True

class ServicesConfig(BaseModel):
    """External services configuration"""
    mcp: MCPConfig = MCPConfig()
    database: DatabaseConfig = DatabaseConfig()
    langfuse: LangfuseConfig = LangfuseConfig()

class YouTrackProjectsConfig(BaseModel):
    """YouTrack project configuration"""
    default: str = "DEMO"
    supported: List[str] = ["DEMO", "PROD", "TEST"]

class AgentConfig(BaseModel):
    """Individual agent configuration"""
    timeout_seconds: int = 300
    max_retries: int = 3

class BugBotConfig(AgentConfig):
    """Bug bot specific configuration"""
    default_project: str = "DEMO"

class ReviewClassifierConfig(AgentConfig):
    """Review classifier specific configuration"""
    batch_size: int = 100
    timeout_seconds: int = 120
    confidence_threshold: float = 0.8

class BugApprovalJudgeConfig(AgentConfig):
    """Bug approval judge specific configuration"""
    timeout_seconds: int = 30
    fallback_requires_approval: bool = True
    fallback_risk_level: str = "MEDIUM"

class FeatureResearchBotConfig(AgentConfig):
    """Feature research bot specific configuration"""
    timeout_seconds: int = 600  # Longer timeout for web research
    max_search_queries: int = 10
    max_competitors_to_analyze: int = 5
    require_citations: bool = True
    min_evidence_per_claim: int = 1

class AgentsConfig(BaseModel):
    """All agent configurations"""
    bug_bot: BugBotConfig = BugBotConfig()
    review_classifier: ReviewClassifierConfig = ReviewClassifierConfig()
    bug_approval_judge: BugApprovalJudgeConfig = BugApprovalJudgeConfig()
    feature_research_bot: FeatureResearchBotConfig = FeatureResearchBotConfig()

class SlackConfig(BaseModel):
    """Slack integration configuration"""
    enabled: bool = True
    socket_mode: bool = True
    default_channel: str = "approvals"
    channel_by_risk: Dict[str, str] = {
        "HIGH": "critical-approvals",
        "MEDIUM": "approvals",
        "LOW": "approvals"
    }
    timeout_seconds: int = 10
    reviewers_whitelists: List[str] = ["U01234567", "U98765432"]

class YouTrackConfig(BaseModel):
    """YouTrack integration configuration"""
    default_project: str = "DEMO"
    timeout_seconds: int = 60
    max_retries: int = 3

class IntegrationsConfig(BaseModel):
    """External integrations configuration"""
    slack: SlackConfig = SlackConfig()
    youtrack: YouTrackConfig = YouTrackConfig()

class ApprovalConfig(BaseModel):
    """Approval workflow configuration"""
    default_expiration_hours: int = 48
    expiration_by_risk: Dict[str, int] = {
        "HIGH": 24,
        "MEDIUM": 48,
        "LOW": 72
    }
    auto_expire_enabled: bool = True
    check_interval_hours: int = 6

class BugSubmissionConfig(BaseModel):
    """Bug submission guardrails configuration"""
    enabled: bool = True
    slack_notifications: bool = True
    timeout_seconds: int = 45

class GuardrailsConfig(BaseModel):
    """Guardrails configuration"""
    enabled: bool = True
    bug_submission: BugSubmissionConfig = BugSubmissionConfig()
    approval: ApprovalConfig = ApprovalConfig()

class QueueConfig(BaseModel):
    """Redis queue configuration for approval processing"""
    # Redis connection
    redis_url: str = "redis://redis:6379"
    redis_db: int = 0
    
    # Worker configuration  
    max_workers: int = 2
    max_jobs_per_worker: int = 10
    job_timeout_seconds: int = 300
    
    # Retry logic
    max_retries: int = 3
    retry_delay_seconds: int = 60
    retry_backoff_multiplier: float = 2.0
    
    # Queue names by priority
    high_priority_queue: str = "approvals:high"
    normal_queue: str = "approvals:normal"
    low_priority_queue: str = "approvals:low"
    dead_letter_queue: str = "approvals:dlq"
    
    # Queue routing by risk level
    queue_by_risk: Dict[str, str] = {
        "HIGH": "approvals:high",
        "MEDIUM": "approvals:normal", 
        "LOW": "approvals:low"
    }

class BackgroundServicesConfig(BaseModel):
    """Background services configuration"""
    queue: QueueConfig = QueueConfig()

class LoggingConfig(BaseModel):
    """Logging and monitoring configuration"""
    level: str = "INFO"
    format: str = "json"
    
    # What to log
    log_agent_calls: bool = True
    log_mcp_calls: bool = True
    log_database_queries: bool = False
    log_slack_messages: bool = True
    log_approvals: bool = True
    
    # Metrics and monitoring
    enable_metrics: bool = True
    langfuse_tracing: bool = True

class DevelopmentConfig(BaseModel):
    """Development and testing configuration"""
    debug: bool = True
    
    # Mock services for testing
    mock_slack: bool = False
    mock_mcp: bool = False
    mock_database: bool = False
    
    # Bypass features for development
    bypass_guardrails: bool = False
    auto_approve_all: bool = False
    
    # Test data
    use_test_data: bool = False
    dry_run_mode: bool = False

class PerformanceConfig(BaseModel):
    """Performance tuning configuration"""
    max_concurrent_agents: int = 5
    max_db_connections: int = 20
    
    # Caching
    cache_prompts: bool = True
    cache_ttl_seconds: int = 3600
    
    # Rate limiting
    max_requests_per_minute: int = 100

class SecurityConfig(BaseModel):
    """Security settings"""
    required_env_vars: List[str] = [
        "OPENAI_API_KEY",
        "SLACK_BOT_TOKEN",
        "SLACK_APP_TOKEN",
        "DATABASE_URL"
    ]
    optional_env_vars: List[str] = [
        "LANGFUSE_SECRET_KEY",
        "LANGFUSE_PUBLIC_KEY"
    ]
    validate_inputs: bool = True
    sanitize_outputs: bool = True

# ============================================================================
# MAIN SETTINGS CLASS
# ============================================================================

class PMAgentSettings(BaseSettings):
    """
    Main PM Agent configuration using Pydantic Settings
    
    Loads configuration from (in order of precedence):
    1. Environment variables (with PM_AGENT_ prefix) - highest priority
    2. app_config.yaml file
    3. .env file
    4. Default values defined in the models above - lowest priority
    """
    
    app: AppInfo = AppInfo()
    models: ModelsConfig = ModelsConfig()
    services: ServicesConfig = ServicesConfig()
    youtrack_projects: YouTrackProjectsConfig = YouTrackProjectsConfig()
    competitors: List[str] = ["Slack", "Microsoft Teams", "Discord", "Zoom", "Miro"]
    agents: AgentsConfig = AgentsConfig()
    integrations: IntegrationsConfig = IntegrationsConfig()
    guardrails: GuardrailsConfig = GuardrailsConfig()
    services_config: BackgroundServicesConfig = BackgroundServicesConfig()
    logging: LoggingConfig = LoggingConfig()
    development: DevelopmentConfig = DevelopmentConfig()
    performance: PerformanceConfig = PerformanceConfig()
    security: SecurityConfig = SecurityConfig()
    
    model_config = SettingsConfigDict(
        env_prefix="PM_AGENT_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_delimiter="__",
        extra="ignore"  # Ignore extra fields in YAML
    )
    
    @classmethod
    def load_yaml_config(cls, yaml_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if yaml_path is None:
            # Look for app_config.yaml in the same directory as this file
            config_dir = Path(__file__).parent
            yaml_file = config_dir / "app_config.yaml"
        else:
            yaml_file = Path(yaml_path)
        
        if not yaml_file.exists():
            print(f"Warning: YAML config file not found: {yaml_file}")
            return {}
        
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f) or {}
            print(f"Loaded config from: {yaml_file}")
            return config_data
        except Exception as e:
            print(f"Error loading YAML config from {yaml_file}: {e}")
            return {}
    
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        """
        Define the settings sources priority order.
        This ensures proper precedence: env vars > yaml > .env > defaults
        """
        # Load YAML configuration
        yaml_settings = cls.load_yaml_config()
        
        class YamlSource:
            def __init__(self, yaml_data):
                self.yaml_data = yaml_data
            
            def __call__(self):
                return self.yaml_data
        
        return (
            init_settings,        # Highest priority - direct instantiation
            env_settings,         # Environment variables
            YamlSource(yaml_settings),  # YAML file
            dotenv_settings,      # .env file
            file_secret_settings, # File secrets
        )
    
    @classmethod
    def create_with_yaml(cls, yaml_path: Optional[str] = None) -> "PMAgentSettings":
        """Create settings instance with YAML config loaded"""
        # Just create the instance - settings_customise_sources handles loading
        return cls()
    
    # ========================================================================
    # COMPUTED PROPERTIES & HELPER METHODS
    # ========================================================================
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.app.environment == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.app.environment == "production"
    
    def get_model_for_agent(self, agent_name: str) -> str:
        """Get model for specific agent with fallback to default"""
        return getattr(self.models, agent_name, self.models.default_chat)
    
    def get_slack_channel_for_risk(self, risk_level: str) -> str:
        """Get Slack channel for specific risk level"""
        return self.integrations.slack.channel_by_risk.get(
            risk_level, 
            self.integrations.slack.default_channel
        )
    
    def get_approval_expiration_hours(self, risk_level: Optional[str] = None) -> int:
        """Get approval expiration hours by risk level"""
        if risk_level:
            return self.guardrails.approval.expiration_by_risk.get(
                risk_level,
                self.guardrails.approval.default_expiration_hours
            )
        return self.guardrails.approval.default_expiration_hours
    
    def is_project_supported(self, project: str) -> bool:
        """Check if project is supported"""
        return project in self.youtrack_projects.supported

# ============================================================================
# GLOBAL SETTINGS INSTANCE
# ============================================================================

# Global settings instance - import this throughout the app
# This loads from app_config.yaml + environment variables + .env file
settings = PMAgentSettings.create_with_yaml()