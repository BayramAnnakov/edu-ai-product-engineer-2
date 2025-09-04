"""
Approval executor service for processing approved actions asynchronously
"""
import asyncio
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
import structlog

# Removed agent imports - using direct MCP client instead
from ..db.approval_service import ApprovalService, create_approval_service
from ..db.models import ApprovalStatus
from ..constants import SystemActionType
import sys
from pathlib import Path

from .youtrack_client import YouTrackMCPClient

# Add slack_service to path
try:
    # Try local development path first
    slack_service_path = str(Path(__file__).parent.parent.parent.parent.parent / "slack_service")
    if slack_service_path not in sys.path:
        sys.path.insert(0, slack_service_path)
    from client import SlackClient
except ImportError:
    # Fallback for Docker environment
    slack_service_path = "/slack_service"
    if slack_service_path not in sys.path:
        sys.path.insert(0, slack_service_path)
    from client import SlackClient
from ..config import settings

logger = structlog.get_logger()


class ApprovalExecutor:
    """Executes approved actions asynchronously"""
    
    def __init__(
        self,
        approval_service: Optional[ApprovalService] = None,
        slack_client: Optional[SlackClient] = None,
        youtrack_mcp_url: str = None
    ):
        self.approval_service = approval_service
        self.slack_client = slack_client
        self.youtrack_mcp_url = youtrack_mcp_url or settings.services.mcp.youtrack_url
        self.youtrack_client = None
    
    async def _ensure_services(self):
        """Ensure services are initialized"""
        if not self.approval_service:
            self.approval_service = await create_approval_service()
        
        if not self.slack_client:
            try:
                self.slack_client = SlackClient()
                await self.slack_client.test_connection()
            except Exception as e:
                logger.warning("Failed to initialize Slack client", error=str(e))
                self.slack_client = None
        
        if not self.youtrack_client:
            try:
                self.youtrack_client = YouTrackMCPClient(self.youtrack_mcp_url)
                logger.info("YouTrack MCP client initialized", url=self.youtrack_mcp_url)
            except Exception as e:
                logger.warning("Failed to initialize YouTrack client", error=str(e))
                self.youtrack_client = None
    
    async def stop(self):
        """Stop the approval executor service and cleanup resources"""
        if self.youtrack_client:
            await self.youtrack_client.close()
            self.youtrack_client = None
        logger.info("Approval executor stopped")
    
    async def _execute_approval(self, approval):
        """Execute a single approved action"""
        start_time = datetime.utcnow()
        
        logger.info(
            "Executing approved action",
            approval_id=str(approval.id),
            action_type=approval.action_type.value
        )
        
        try:
            if approval.action_type == SystemActionType.CREATE_YOUTRACK_ISSUE:
                result = await self._execute_youtrack_issue_creation(approval)
            elif approval.action_type == SystemActionType.ADD_YOUTRACK_COMMENT:
                result = await self._execute_youtrack_comment_addition(approval)
            elif approval.action_type == SystemActionType.POST_SLACK:
                result = await self._execute_slack_post(approval)
            else:
                raise ValueError(f"Unsupported action type: {approval.action_type}")
            
            # Calculate execution time
            execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Mark as executed
            await self.approval_service.mark_executed(
                approval.id,
                execution_result=result
            )
            
            # Send Slack notification if available
            if self.slack_client and approval.slack_channel:
                await self._send_execution_notification(
                    approval, result, execution_time_ms
                )
            
            logger.info(
                "Approval executed successfully",
                approval_id=str(approval.id),
                execution_time_ms=execution_time_ms
            )
            
        except Exception as e:
            execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            await self.approval_service.mark_executed(
                approval.id,
                execution_error=str(e)
            )
            raise
    
    async def _execute_youtrack_issue_creation(self, approval) -> Dict[str, Any]:
        """Execute YouTrack issue creation directly via MCP tools"""
        payload = approval.payload_json
        
        # Extract parameters for YouTrack issue creation
        project = payload.get("project", settings.youtrack_projects.default)
        summary = payload.get("summary", "")
        description = payload.get("description", "")
        priority = payload.get("priority", "Normal")
        issue_type = payload.get("issue_type", "Bug")
        tags = payload.get("tags")
        
        # Ensure YouTrack client is initialized
        await self._ensure_services()
        
        if not self.youtrack_client:
            raise RuntimeError("YouTrack client not available")
        
        # Create issue directly via MCP client
        result = await self.youtrack_client.create_issue(
            project=project,
            summary=summary,
            description=description,
            issue_type=issue_type,
            priority=priority,
            tags=tags
        )
        
        return {
            "action": "created_issue",
            "issue_id": result.get("issue_id"),
            "url": result.get("url"),
            "summary": summary,
            "project": project,
            "priority": priority,
            "mcp_result": result
        }
    
    async def _execute_youtrack_comment_addition(self, approval) -> Dict[str, Any]:
        """Execute YouTrack comment addition directly via MCP tools"""
        payload = approval.payload_json
        
        # Extract parameters for YouTrack comment addition
        issue_id = payload.get("issue_id", "")
        comment_text = payload.get("comment", "")
        use_markdown = payload.get("use_markdown", True)
        
        if not issue_id:
            raise ValueError("issue_id is required for adding comments")
        if not comment_text:
            raise ValueError("comment text is required for adding comments")
        
        # Ensure YouTrack client is initialized
        await self._ensure_services()
        
        if not self.youtrack_client:
            raise RuntimeError("YouTrack client not available")
        
        # Add comment directly via MCP client
        result = await self.youtrack_client.add_comment(
            issue_id=issue_id,
            text=comment_text,
            use_markdown=use_markdown
        )
        
        return {
            "action": "added_comment",
            "issue_id": issue_id,
            "comment": comment_text,
            "comment_id": result.get("comment_id"),
            "mcp_result": result
        }
    
    async def _execute_slack_post(self, approval) -> Dict[str, Any]:
        """Execute Slack post action"""
        payload = approval.payload_json
        
        if not self.slack_client:
            raise RuntimeError("Slack client not available")
        
        channel = payload.get("channel", settings.integrations.slack.default_channel)
        message = payload.get("message", "")
        
        # Send message
        response = await self.slack_client.client.chat_postMessage(
            channel=channel,
            text=message
        )
        
        return {
            "action": "posted_to_slack",
            "channel": channel,
            "message_ts": response["ts"],
            "message": message
        }
    
    async def _send_execution_notification(
        self,
        approval,
        execution_result: Dict[str, Any],
        execution_time_ms: int
    ):
        """Send Slack notification about execution completion"""
        try:
            if approval.action_type == SystemActionType.CREATE_YOUTRACK_ISSUE:
                await self.slack_client.send_execution_notification(
                    channel=approval.slack_channel,
                    bug_summary=execution_result.get("summary", ""),
                    approved_by=approval.decided_by,
                    executed_at=approval.executed_at,
                    issue_id=execution_result.get("issue_id"),
                    issue_url=execution_result.get("url"),
                    issue_title=execution_result.get("summary"),
                    execution_time_ms=execution_time_ms
                )
            elif approval.action_type == SystemActionType.ADD_YOUTRACK_COMMENT:
                # Send notification for comment addition
                await self.slack_client.send_comment_notification(
                    channel=approval.slack_channel,
                    issue_id=execution_result.get("issue_id"),
                    comment=execution_result.get("comment", ""),
                    approved_by=approval.decided_by,
                    executed_at=approval.executed_at,
                    execution_time_ms=execution_time_ms
                )
            
            logger.info(
                "Execution notification sent",
                approval_id=str(approval.id),
                channel=approval.slack_channel
            )
            
        except Exception as e:
            logger.error(
                "Failed to send execution notification",
                approval_id=str(approval.id),
                error=str(e)
            )
    
    async def execute_single_approval(self, approval_id: uuid.UUID) -> Dict[str, Any]:
        """
        Execute a single approval immediately (for testing or manual execution)
        
        Args:
            approval_id: ID of the approval to execute
            
        Returns:
            Execution result
        """
        await self._ensure_services()
        
        approval = await self.approval_service.get_approval(approval_id)
        if not approval:
            raise ValueError(f"Approval {approval_id} not found")
        
        if approval.status != ApprovalStatus.APPROVED:
            raise ValueError(f"Approval {approval_id} is not approved (status: {approval.status})")
        
        await self._execute_approval(approval)
        
        # Return updated approval
        return await self.approval_service.get_approval(approval_id)


# Convenience function
async def create_approval_executor(**kwargs) -> ApprovalExecutor:
    """Create an approval executor instance"""
    return ApprovalExecutor(**kwargs)