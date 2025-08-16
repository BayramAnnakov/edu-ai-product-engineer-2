"""
Bug submission guardrails using OpenAI Agent SDK native guardrails
"""
import uuid
import json
import re
from typing import Dict, Any, Optional
from datetime import datetime
import structlog

from agents import input_guardrail, output_guardrail, Agent, Runner
from agents import GuardrailFunctionOutput, RunContextWrapper

from db.approval_service import create_approval_service
from db.models import RiskLevel
from src.constants import SystemActionType, BugProcessingOutcome
# No longer need config imports - LLM-as-a-judge approach

logger = structlog.get_logger()

# Import Slack client with proper fallback
import sys
from pathlib import Path

# Try to import SlackClient from the slack_service
SlackClient = None
try:
    # Check if we're in Docker environment
    import os
    if os.path.exists("/app/slack_service"):
        sys.path.insert(0, "/app/slack_service")
        from client import SlackClient
        logger.info("SlackClient imported from /app/slack_service")
    else:
        # Try relative import for local development
        slack_service_path = str(Path(__file__).parent.parent.parent.parent / "slack_service")
        if os.path.exists(slack_service_path):
            if slack_service_path not in sys.path:
                sys.path.insert(0, slack_service_path)
            from client import SlackClient
            logger.info(f"SlackClient imported from {slack_service_path}")
        else:
            raise ImportError("slack_service directory not found")
except ImportError as e:
    logger.warning(f"SlackClient import failed - approval features will be disabled: {e}")
    # Create a stub SlackClient that won't crash but won't send messages
    class SlackClient:
        def __init__(self, *args, **kwargs):
            logger.warning("Using stub SlackClient - no actual Slack messages will be sent")
        
        async def send_approval_request(self, *args, **kwargs):
            logger.warning("Stub SlackClient: send_approval_request called but not implemented")
            return {"status": "stub", "message": "SlackClient not available"}
        
        def create_approval(self, *args, **kwargs):
            logger.warning("Stub SlackClient: create_approval called but not implemented")
            return {"status": "stub", "message": "SlackClient not available"}

# Global services (initialized lazily)
_approval_service = None
_slack_client = None

async def _ensure_services():
    """Ensure services are initialized"""
    global _approval_service, _slack_client
    
    if not _approval_service:
        _approval_service = await create_approval_service()
    
    if not _slack_client:
        try:
            from src.config import settings
            _slack_client = SlackClient(
                default_channel=settings.integrations.slack.default_channel
            )
            await _slack_client.test_connection()
        except Exception as e:
            logger.warning("Failed to initialize Slack client", error=str(e))
            _slack_client = None

def _extract_youtrack_operations(input_text: str) -> list:
    """Extract YouTrack operations from agent input"""
    operations = []
    
    # Look for YouTrack operation patterns
    if "create_youtrack_issue" in input_text.lower():
        operations.append({
            "type": "create_issue",
            "context": input_text
        })
    
    if "add_issue_comment" in input_text.lower():
        operations.append({
            "type": "add_comment", 
            "context": input_text
        })
    
    return operations

async def _assess_bug_submission(input_text: str) -> tuple[bool, str, str]:
    """Assess bug submission using LLM-as-a-judge"""
    try:
        from pm_agents.bug_approval_judge import get_bug_approval_judge
        
        # Get the judge instance
        judge = await get_bug_approval_judge()
        
        # Assess bug submission using LLM
        assessment = await judge.assess_bug_submission(input_text)
        
        logger.info(
            "LLM bug submission assessment completed",
            needs_approval=assessment.needs_approval,
            confidence=assessment.confidence_score,
            risk_level=assessment.risk_level
        )
        
        return assessment.needs_approval, assessment.reasoning, assessment.risk_level
        
    except Exception as e:
        logger.error("LLM bug submission assessment failed", error=str(e))
        # Conservative fallback - require approval for safety
        return True, f"LLM assessment failed: {str(e)}", "MEDIUM"

@input_guardrail
async def bug_submission_input_guardrail(
    ctx: RunContextWrapper[None],
    agent: Agent,
    input: str | list
) -> GuardrailFunctionOutput:
    """
    Input guardrail that checks if bug submission requires approval
    """
    try:
        await _ensure_services()
        
        # Convert input to string if it's a list
        input_text = str(input) if isinstance(input, list) else input
        
        # Extract YouTrack operations from input
        operations = _extract_youtrack_operations(input_text)
        
        if not operations:
            # No YouTrack operations detected, allow
            return GuardrailFunctionOutput(
                output_info="No YouTrack operations detected",
                tripwire_triggered=False
            )
        
        # Assess bug submission using LLM-as-a-judge
        needs_approval, reason, risk_level = await _assess_bug_submission(input_text)
        
        if not needs_approval:
            logger.info(
                "Bug submission auto-approved",
                operations_count=len(operations),
                risk_level=risk_level
            )
            return GuardrailFunctionOutput(
                output_info="Auto-approved bug submission",
                tripwire_triggered=False
            )
        
        # Create approval request
        approval = await _approval_service.create_approval(
            action_type=SystemActionType.CREATE_YOUTRACK_ISSUE,
            payload_json={
                "input_text": input_text,
                "operations": operations,
                "reason": reason,
                "tool_name": "bug_submission_input_guardrail"
            },
            risk=_map_risk_level(risk_level),
            related_entity_id=ctx.context.get("review_id") if ctx.context else None,
            langfuse_trace_id=ctx.context.get("langfuse_trace_id") if ctx.context else None
        )
        
        # Send Slack notification if available
        if _slack_client:
            try:
                # Extract bug summary from context or input text
                bug_summary = _extract_bug_summary_from_context(ctx, input_text)
                
                await _slack_client.send_bug_approval_request(
                    approval_id=str(approval.id),
                    bug_summary=bug_summary,
                    approval_reason=reason,
                    risk_level=approval.risk.value,
                    review_id=str(ctx.context.get("review_id")) if ctx.context and ctx.context.get("review_id") else None,
                    langfuse_trace_id=ctx.context.get("langfuse_trace_id") if ctx.context else None,
                    agent_name=agent.name
                )
            except Exception as e:
                logger.error("Failed to send Slack notification", error=str(e))
        
        logger.info(
            "Bug submission requires approval",
            approval_id=str(approval.id),
            reason=reason,
            operations=operations
        )
        
        # Trigger tripwire to halt execution
        return GuardrailFunctionOutput(
            output_info=f"Approval required: {reason} (ID: {approval.id})",
            tripwire_triggered=True
        )
        
    except Exception as e:
        logger.error("Input guardrail failed", error=str(e))
        # In case of error, allow execution to proceed
        return GuardrailFunctionOutput(
            output_info=f"Guardrail error: {str(e)}",
            tripwire_triggered=False
        )

@output_guardrail
async def bug_submission_output_guardrail(
    ctx: RunContextWrapper[None],
    agent: Agent,
    output: str
) -> GuardrailFunctionOutput:
    """
    Output guardrail that validates bug submission results
    """
    try:
        await _ensure_services()
        
        # Try to parse JSON output
        try:
            result_data = json.loads(output)
        except json.JSONDecodeError:
            # If not JSON, treat as text output
            result_data = {"text_output": output}
        
        # Check if the output indicates a successful action that should be logged
        if isinstance(result_data, dict):
            action = result_data.get("action")
            issue_id = result_data.get("issue_id")
            
            if (
                action in [
                    BugProcessingOutcome.CREATED_ISSUE.value,
                    BugProcessingOutcome.COMMENTED_ON_DUPLICATE.value
                ]
                and issue_id
            ):
                logger.info(
                    "Bug submission completed successfully",
                    action=action,
                    issue_id=issue_id,
                    agent=agent.name
                )
        
        # Output guardrail primarily for logging and monitoring
        # Could add additional validations here if needed
        
        return GuardrailFunctionOutput(
            output_info="Bug submission output validated",
            tripwire_triggered=False
        )
        
    except Exception as e:
        logger.error("Output guardrail failed", error=str(e))
        # Don't block output in case of errors
        return GuardrailFunctionOutput(
            output_info=f"Output validation error: {str(e)}",
            tripwire_triggered=False
        )

def _map_risk_level(risk_level: str) -> RiskLevel:
    """Map string risk level to RiskLevel enum"""
    risk_mapping = {
        "HIGH": RiskLevel.HIGH,
        "MEDIUM": RiskLevel.MEDIUM, 
        "LOW": RiskLevel.LOW
    }
    return risk_mapping.get(risk_level, RiskLevel.MEDIUM)

def _extract_bug_summary_from_context(ctx: RunContextWrapper, input_text: str) -> str:
    """Extract bug summary from context - use original review text"""
    # Get the original review text from context (much simpler!)
    if ctx and ctx.context and "review_text" in ctx.context:
        review_text = ctx.context["review_text"]
        # Return first 80 characters as summary
        return review_text[:80] + "..." if len(review_text) > 80 else review_text
    
    # Fallback: extract from the input template (old complex logic)
    return _extract_bug_summary_from_template(input_text)


def _extract_bug_summary_from_template(input_text: str) -> str:
    """Extract bug summary from workflow template text"""
    # Look for the actual review text in the workflow template
    # Pattern: **Review Text**: \n  > [actual review text]
    review_text_pattern = r'\*\*Review Text\*\*:\s*\n\s*>\s*([^\n]+)'
    match = re.search(review_text_pattern, input_text)
    if match:
        review_text = match.group(1).strip()
        # Return first 80 characters for summary
        return review_text[:80] + "..." if len(review_text) > 80 else review_text
    
    # Fallback: look for review information section
    review_info_pattern = r'## Review Information.*?- \*\*Review Text\*\*:\s*\n\s*>\s*([^\n]+)'
    match = re.search(review_info_pattern, input_text, re.DOTALL)
    if match:
        review_text = match.group(1).strip()
        return review_text[:80] + "..." if len(review_text) > 80 else review_text
    
    # Last fallback: look for any text after "Review Text:"
    simple_pattern = r'Review Text[:\s]*[>\s]*([^\n]+)'
    match = re.search(simple_pattern, input_text, re.IGNORECASE)
    if match:
        review_text = match.group(1).strip()
        return review_text[:80] + "..." if len(review_text) > 80 else review_text
    
    # Final fallback
    return "Bug report requiring approval"