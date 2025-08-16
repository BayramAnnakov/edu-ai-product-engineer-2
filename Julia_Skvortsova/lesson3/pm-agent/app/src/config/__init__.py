"""
Pydantic-based configuration management for PM Agent

This module provides a clean, type-safe configuration system using Pydantic Settings.
All configuration is centralized and can be overridden via environment variables.

Usage:
    from src.config import settings
    
    # Access config with dot notation and full type safety
    print(settings.models.bug_bot)                    # "gpt-4.1-2025-04-14"
    print(settings.services.mcp.youtrack_url)         # "http://mcp_youtrack:8002/mcp"
    print(settings.integrations.slack.default_channel) # "approvals"
    
    # Helper methods
    model = settings.get_model_for_agent("bug_bot")
    channel = settings.get_slack_channel_for_risk("HIGH")
    
    # Environment checks
    if settings.is_development:
        logger.setLevel("DEBUG")
"""

# Import the main settings instance
from .settings import (
    settings,
)

# Import the settings class for type hints and testing
from .settings import PMAgentSettings

# Re-export for convenience
__all__ = [
    "settings",
    "PMAgentSettings",
]


# ============================================================================
# ENVIRONMENT VARIABLE HELPERS
# ============================================================================

import os
import structlog

logger = structlog.get_logger()

def validate_required_env_vars() -> bool:
    """Validate that all required environment variables are set"""
    missing_vars = []
    
    for var in settings.security.required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error("Missing required environment variables", missing_vars=missing_vars)
        return False
    
    logger.info("All required environment variables are set")
    return True

def log_config_summary():
    """Log a summary of current configuration"""
    logger.info(
        "PM Agent configuration loaded",
        app_name=settings.app.name,
        version=settings.app.version,
        environment=settings.app.environment,
        default_project=settings.youtrack_projects.default,
        guardrails_enabled=settings.guardrails.enabled,
        slack_enabled=settings.integrations.slack.enabled,
        debug_mode=settings.development.debug
    )