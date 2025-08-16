"""
Slack client for sending messages and notifications
"""
import os
from typing import Dict, Any, Optional
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError
import structlog

from template_renderer import TemplateRenderer

logger = structlog.get_logger()


class SlackClient:
    """Client for sending Slack messages"""
    
    def __init__(
        self,
        bot_token: Optional[str] = None,
        default_channel: str = "approvals"
    ):
        self.bot_token = bot_token or os.getenv("SLACK_BOT_TOKEN")
        if not self.bot_token:
            raise ValueError("SLACK_BOT_TOKEN environment variable is required")
        
        self.client = AsyncWebClient(token=self.bot_token)
        self.default_channel = default_channel
        self.template_renderer = TemplateRenderer()
        
        logger.info("Slack client initialized")
    
    async def send_bug_approval_request(
        self,
        approval_id: str,
        bug_summary: str,
        bug_description: str = None,
        approval_reason: str = None,
        approval_confidence: float = None,
        priority: str = "Normal",
        risk_level: str = "medium",
        duplicate_candidates: list = None,
        review_id: str = None,
        langfuse_trace_id: str = None,
        agent_name: str = "BugBot",
        channel: str = None
    ) -> str:
        """
        Send bug approval request
        
        Returns:
            Message timestamp (ts) for tracking
        """
        try:
            blocks = self.template_renderer.render(
                "bug_approval_request.j2",
                approval_id=approval_id,
                bug_summary=bug_summary,
                bug_description=bug_description,
                reason=approval_reason,
                priority=priority,
                risk_level=risk_level,
                duplicate_candidates=duplicate_candidates or [],
                review_id=review_id,
                langfuse_trace_id=langfuse_trace_id,
                agent_name=agent_name
            )
            
            response = await self.client.chat_postMessage(
                channel=channel or self.default_channel,
                blocks=blocks["blocks"],
                text="Bug report requires approval"  # Fallback text
            )
            
            message_ts = response["ts"]
            
            logger.info(
                "Bug approval request sent",
                approval_id=approval_id,
                channel=channel or self.default_channel,
                message_ts=message_ts
            )
            
            return message_ts
            
        except SlackApiError as e:
            logger.error(
                "Failed to send bug approval request",
                approval_id=approval_id,
                error=str(e)
            )
            raise
    
    async def send_duplicate_approval_request(
        self,
        approval_id: str,
        bug_summary: str,
        similarity_score: float,
        duplicate_issue_id: str,
        duplicate_title: str,
        duplicate_url: str,
        duplicate_description: str = None,
        risk_level: str = "medium",
        channel: str = None
    ) -> str:
        """
        Send duplicate detection approval request
        
        Returns:
            Message timestamp (ts) for tracking
        """
        try:
            blocks = self.template_renderer.render(
                "duplicate_approval_request.j2",
                approval_id=approval_id,
                bug_summary=bug_summary,
                similarity_score=similarity_score,
                duplicate_issue_id=duplicate_issue_id,
                duplicate_title=duplicate_title,
                duplicate_url=duplicate_url,
                duplicate_description=duplicate_description,
                risk_level=risk_level
            )
            
            response = await self.client.chat_postMessage(
                channel=channel or self.default_channel,
                blocks=blocks["blocks"],
                text="Uncertain duplicate detection requires approval"
            )
            
            message_ts = response["ts"]
            
            logger.info(
                "Duplicate approval request sent",
                approval_id=approval_id,
                similarity_score=similarity_score,
                message_ts=message_ts
            )
            
            return message_ts
            
        except SlackApiError as e:
            logger.error(
                "Failed to send duplicate approval request",
                approval_id=approval_id,
                error=str(e)
            )
            raise
    
    async def send_execution_notification(
        self,
        channel: str,
        bug_summary: str,
        approved_by: str,
        executed_at: Any,
        issue_id: str = None,
        issue_url: str = None,
        issue_title: str = None,
        duplicate_issue_id: str = None,
        duplicate_url: str = None,
        similarity_score: float = None,
        execution_time_ms: int = None
    ) -> str:
        """
        Send notification that an approved action was executed
        
        Returns:
            Message timestamp (ts)
        """
        try:
            blocks = self.template_renderer.render(
                "bug_approval_executed.j2",
                bug_summary=bug_summary,
                approved_by=approved_by,
                executed_at=executed_at,
                issue_id=issue_id,
                issue_url=issue_url,
                issue_title=issue_title,
                duplicate_issue_id=duplicate_issue_id,
                duplicate_url=duplicate_url,
                similarity_score=similarity_score,
                execution_time_ms=execution_time_ms
            )
            
            response = await self.client.chat_postMessage(
                channel=channel,
                blocks=blocks["blocks"],
                text="Approved action completed"
            )
            
            message_ts = response["ts"]
            
            logger.info(
                "Execution notification sent",
                channel=channel,
                message_ts=message_ts
            )
            
            return message_ts
            
        except SlackApiError as e:
            logger.error(
                "Failed to send execution notification",
                channel=channel,
                error=str(e)
            )
            raise
    
    async def test_connection(self) -> bool:
        """Test Slack connection"""
        try:
            response = await self.client.auth_test()
            logger.info(
                "Slack connection test successful",
                team=response.get("team"),
                user=response.get("user")
            )
            return True
        except SlackApiError as e:
            logger.error("Slack connection test failed", error=str(e))
            return False