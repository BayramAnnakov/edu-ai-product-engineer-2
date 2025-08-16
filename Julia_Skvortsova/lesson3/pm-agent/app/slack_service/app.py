"""
Consolidated Slack service - handles all Slack interactions
"""
import os
import asyncio
import uuid
import sys
from pathlib import Path
import structlog
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

# Add main app src to path for imports
app_src_path = str(Path(__file__).parent.parent / "src")
if app_src_path not in sys.path:
    sys.path.insert(0, app_src_path)

# Add slack_service to path for template_renderer
slack_service_path = str(Path(__file__).parent)
if slack_service_path not in sys.path:
    sys.path.insert(0, slack_service_path)

from template_renderer import TemplateRenderer
from db.approval_service import create_approval_service

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Initialize Slack app
app = AsyncApp(token=os.environ.get("SLACK_BOT_TOKEN"))

# Initialize services
approval_service = None
template_renderer = TemplateRenderer()

async def ensure_services():
    """Ensure services are initialized"""
    global approval_service
    if not approval_service:
        approval_service = await create_approval_service()

@app.action("approve")
async def approve_action(ack, body, client):
    """Handle approval button clicks"""
    await ack()
    await ensure_services()
    
    approval_id = body["actions"][0]["value"]
    user_id = body["user"]["id"]
    channel_id = body["channel"]["id"]
    message_ts = body["message"]["ts"]
    
    logger.info("Approval received", approval_id=approval_id, user=user_id)
    
    try:
        # Convert approval_id to UUID
        approval_uuid = uuid.UUID(approval_id)
        
        # Update approval status in database
        approval = await approval_service.approve(
            approval_id=approval_uuid,
            decided_by=user_id,
            reason="Approved via Slack"
        )
        
        # Get approval details for message update
        payload = approval.payload_json
        bug_summary = payload.get("summary", "Bug report")
        
        # Update the message with approval confirmation
        blocks = template_renderer.render(
            "bug_approval_approved.j2",
            decided_by=user_id,
            decided_at=approval.decided_at,
            reason=approval.reason,
            bug_summary=bug_summary,
            immediate_execution=False  # Will be executed by background service
        )
        
        await client.chat_update(
            channel=channel_id,
            ts=message_ts,
            blocks=blocks["blocks"]
        )
        
        # Note: Slack message info could be stored via approval service update method if needed
        
        logger.info(
            "Approval processed successfully",
            approval_id=approval_id,
            decided_by=user_id
        )
        
    except Exception as e:
        logger.error(
            "Failed to process approval",
            approval_id=approval_id,
            error=str(e)
        )
        
        # Send error message
        await client.chat_postMessage(
            channel=channel_id,
            text=f"❌ Error processing approval: {str(e)}",
            thread_ts=message_ts
        )

@app.action("reject")
async def reject_action(ack, body, client):
    """Handle rejection button clicks"""
    await ack()
    await ensure_services()
    
    approval_id = body["actions"][0]["value"]
    user_id = body["user"]["id"]
    channel_id = body["channel"]["id"]
    message_ts = body["message"]["ts"]
    
    logger.info("Rejection received", approval_id=approval_id, user=user_id)
    
    try:
        # Convert approval_id to UUID
        approval_uuid = uuid.UUID(approval_id)
        
        # Update approval status in database
        approval = await approval_service.reject(
            approval_id=approval_uuid,
            decided_by=user_id,
            reason="Rejected via Slack"
        )
        
        # Get approval details for message update
        payload = approval.payload_json
        bug_summary = payload.get("summary", "Bug report")
        
        # Update the message with rejection confirmation
        blocks = template_renderer.render(
            "bug_approval_rejected.j2",
            decided_by=user_id,
            decided_at=approval.decided_at,
            reason=approval.reason,
            bug_summary=bug_summary
        )
        
        await client.chat_update(
            channel=channel_id,
            ts=message_ts,
            blocks=blocks["blocks"]
        )
        
        logger.info(
            "Rejection processed successfully",
            approval_id=approval_id,
            decided_by=user_id
        )
        
    except Exception as e:
        logger.error(
            "Failed to process rejection",
            approval_id=approval_id,
            error=str(e)
        )
        
        # Send error message
        await client.chat_postMessage(
            channel=channel_id,
            text=f"❌ Error processing rejection: {str(e)}",
            thread_ts=message_ts
        )

async def main():
    """Main entry point for Slack service"""
    logger.info("Starting Slack service...")
    
    # Start the app using Socket Mode
    handler = AsyncSocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
    
    try:
        await handler.start_async()
    except KeyboardInterrupt:
        logger.info("Shutting down Slack service...")

if __name__ == "__main__":
    asyncio.run(main())