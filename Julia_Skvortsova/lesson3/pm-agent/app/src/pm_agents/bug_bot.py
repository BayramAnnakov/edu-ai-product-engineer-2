"""
Bug Bot Agent - Processes bug reports from reviews and manages YouTrack issues
"""
import json
import os
import uuid
import time
import structlog
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from agents import Agent
from agents.mcp import MCPServerStreamableHttp, MCPServerStreamableHttpParams

# Load environment variables
load_dotenv()

from langfuse_integration import create_traced_runner
from db.review_service import create_review_service
from db.models import Review
from prompts import format_prompt, BugBotPrompts
from schemas import (
    BugProcessingResult,
    BugProcessingOutcome,
    ApprovalStatus,
    get_bug_processing_schema_formatted
)
from guardrails import bug_submission_input_guardrail, bug_submission_output_guardrail
from src.config import settings

logger = structlog.get_logger()

class BugBotAgent:
    """Agent that processes bug reports and manages YouTrack issues using MCP server"""
    
    def __init__(self, project: str = None):
        self.runner = create_traced_runner()
        self.db_service = None
        self.project = project or settings.youtrack_projects.default
        
        # Configure MCP server for YouTrack (FastMCP with HTTP transport)
        mcp_params = MCPServerStreamableHttpParams(
            url=settings.services.mcp.youtrack_url
        )
        self.youtrack_mcp_server = MCPServerStreamableHttp(
            params=mcp_params,
            name="youtrack",
            cache_tools_list=True
        )
        
        # Create the bug bot agent with MCP server and SDK guardrails
        self.agent = Agent(
            name="BugBot",
            instructions=format_prompt(BugBotPrompts.INSTRUCTIONS),
            model=settings.models.bug_bot,
            mcp_servers=[self.youtrack_mcp_server],
            input_guardrails=[bug_submission_input_guardrail],
            output_guardrails=[bug_submission_output_guardrail]
        )
        
        logger.info("BugBot agent initialized with MCP server and SDK guardrails", 
                   agent_name=self.agent.name,
                   project=self.project,
                   mcp_url=settings.services.mcp.youtrack_url)
    
    async def _ensure_db_service(self):
        """Ensure database service is initialized"""
        if not self.db_service:
            self.db_service = await create_review_service()
    
    async def _ensure_mcp_connection(self):
        """Ensure MCP server is connected"""
        try:
            await self.youtrack_mcp_server.connect()
            logger.debug("MCP server connection ensured")
        except Exception as e:
            logger.warning("Failed to connect MCP server", error=str(e))
    
    async def process_bug_review(
        self,
        review: Review,
        langfuse_trace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a single bug review and create/update YouTrack issue"""
        await self._ensure_db_service()
        await self._ensure_mcp_connection()
        
        # Generate trace ID if not provided
        if not langfuse_trace_id:
            langfuse_trace_id = str(uuid.uuid4())
        
        try:
            logger.info("Processing bug review",
                       review_id=str(review.id),
                       review_text=review.text[:100],
                       langfuse_trace_id=langfuse_trace_id)
            
            # Load templates for the workflow
            bug_report_template = format_prompt(BugBotPrompts.BUG_REPORT_TEMPLATE,
                review_text=review.text,
                confidence=review.confidence,
                review_id=str(review.original_id or review.id),
                review_date=review.processed_at.isoformat()
            )
            
            duplicate_comment_template = format_prompt(BugBotPrompts.DUPLICATE_COMMENT_TEMPLATE)
            
            # Generate session ID for tracking
            session_id = str(uuid.uuid4())
            start_time = time.time()
            
            # Create the staged workflow prompt with session tracking
            # The LLM will extract component information during workflow execution
            workflow_prompt = format_prompt(
                BugBotPrompts.STAGED_WORKFLOW,
                project=self.project,
                review_id=str(review.original_id or review.id),
                confidence=review.confidence,
                review_text=review.text,
                review_date=review.processed_at.isoformat(),
                bug_processing_schema=get_bug_processing_schema_formatted(),
                bug_report_template=bug_report_template,
                duplicate_comment_template=duplicate_comment_template,
                session_id=session_id
            )

            try:
                # Run the agent with structured workflow - SDK guardrails will intercept if needed
                # Pass trace_id to runner for proper Langfuse integration
                result = await self.runner.run(
                    self.agent, 
                    workflow_prompt,
                    trace_id=langfuse_trace_id,  # Pass trace ID to runner
                    context={
                        "review_id": str(review.id),
                        "review_text": review.text,  # Add actual review text for guardrails
                        "langfuse_trace_id": langfuse_trace_id,
                        "project": self.project
                    }
                )
                agent_output = result.final_output if hasattr(result, 'final_output') else str(result)
                
            except Exception as e:
                # Check if it's a guardrail tripwire exception
                if "tripwire" in str(e).lower() or "approval" in str(e).lower():
                    logger.info(
                        "Bug processing blocked by guardrails",
                        review_id=str(review.id),
                        error=str(e)
                    )
                    # Calculate processing time for pending approval
                    processing_time_ms = int((time.time() - start_time) * 1000)
                    
                    # Return a pending approval result
                    result_data = BugProcessingResult(
                        action=BugProcessingOutcome.SKIPPED,
                        approval_status=ApprovalStatus.PENDING,
                        summary="Bug processing requires approval",
                        uncertainty_reason=str(e),
                        duplicate_session_id=session_id,
                        processing_time_ms=processing_time_ms
                    )
                    
                    return {
                        "review_id": str(review.id),
                        "action": result_data.action.value,
                        "approval_status": result_data.approval_status.value,
                        "summary": result_data.summary,
                        "uncertainty_reason": result_data.uncertainty_reason,
                        "session_id": result_data.duplicate_session_id,
                        "processing_time_ms": result_data.processing_time_ms,
                        "agent_output": str(e)
                    }
                else:
                    # Re-raise non-guardrail related exceptions
                    raise
            
            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Parse and validate the structured response
            try:
                result_data = self._parse_and_validate_response(agent_output)
                
                # Add session tracking data if not already present
                if not result_data.duplicate_session_id:
                    result_data.duplicate_session_id = session_id
                if not result_data.processing_time_ms:
                    result_data.processing_time_ms = processing_time_ms
                    
                logger.info("Parsed structured response", 
                           action=result_data.action,
                           issue_id=result_data.issue_id,
                           session_id=session_id,
                           processing_time_ms=processing_time_ms)
                
            except Exception as e:
                logger.error("Failed to parse structured response", 
                           error=str(e), 
                           output=agent_output[:500])
                # Fallback to error result with session tracking
                result_data = BugProcessingResult(
                    action=BugProcessingOutcome.ERROR,
                    summary="Failed to parse agent response",
                    error_message=str(e),
                    duplicate_session_id=session_id,
                    processing_time_ms=processing_time_ms
                )
            
            # Store ticket information in database
            if result_data.action in [BugProcessingOutcome.CREATED_ISSUE, BugProcessingOutcome.COMMENTED_ON_DUPLICATE]:
                ticket = await self._store_ticket_record(review, result_data)
                logger.info("Ticket record created",
                           ticket_id=str(ticket.id),
                           issue_id=ticket.issue_id,
                           action=result_data.action.value)
            
            # Get actual trace ID used
            actual_trace_id = self.runner.get_last_trace_id() or langfuse_trace_id
            
            return {
                "review_id": str(review.id),
                "langfuse_trace_id": actual_trace_id,  # Include actual trace ID
                "action": result_data.action.value,
                "issue_id": result_data.issue_id,
                "url": result_data.url,
                "summary": result_data.summary,
                "similarity_score": result_data.duplicate_analysis.similarity_score if result_data.duplicate_analysis else None,
                "search_queries": result_data.search_queries_used,
                "issues_examined": result_data.issues_examined,
                "agent_output": agent_output,
                # Staged processing tracking
                "session_id": result_data.duplicate_session_id,
                "total_candidates_found": result_data.total_candidates_found,
                "candidates_analyzed_in_detail": result_data.candidates_analyzed_in_detail,
                "processing_time_ms": result_data.processing_time_ms,
                "api_calls_made": result_data.api_calls_made
            }
            
        except Exception as e:
            logger.exception("Bug processing failed", review_id=str(review.id))
            raise
    
    def _parse_and_validate_response(self, agent_output: str) -> BugProcessingResult:
        """Parse and validate agent response using Pydantic schemas"""
        try:
            # Extract JSON from agent output
            import re
            json_match = re.search(r'\{.*\}', agent_output, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in agent output")
            
            json_str = json_match.group()
            json_data = json.loads(json_str)
            
            # Validate using Pydantic schema
            validated_result = BugProcessingResult(**json_data)
            return validated_result
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in agent output: {e}")
        except Exception as e:
            raise ValueError(f"Schema validation failed: {e}")
    
    async def _store_ticket_record(self, review: Review, result_data: BugProcessingResult):
        """Store ticket record in database"""
        if not self.db_service:
            raise RuntimeError("Database service not initialized")
            
        similarity_score = None
        duplicate_of = None
        
        if result_data.duplicate_analysis:
            similarity_score = result_data.duplicate_analysis.similarity_score
            duplicate_of = result_data.duplicate_of
        
        return await self.db_service.create_ticket(
            review_id=review.id,
            project=self.project,
            issue_id=result_data.issue_id,
            url=result_data.url,
            title=result_data.summary,
            duplicate_of=duplicate_of,
            similarity_score=similarity_score
        )
    
    async def test_mcp_connection(self) -> Dict[str, Any]:
        """Test the MCP connection and list available tools"""
        try:
            # First, connect the MCP server
            await self.youtrack_mcp_server.connect()
            logger.info("MCP server connected successfully", 
                       server_url=settings.services.mcp.youtrack_url)
            
            # Test with a simple prompt that should use MCP tools
            test_prompt = f"List the available YouTrack tools for project {self.project}."
            result = await self.runner.run(self.agent, test_prompt)
            
            return {
                "status": "connected",
                "mcp_server": settings.services.mcp.youtrack_url,
                "response": str(result.final_output if hasattr(result, 'final_output') else result)
            }
        except Exception as e:
            logger.error("MCP connection test failed", error=str(e))
            return {
                "status": "failed", 
                "error": str(e),
                "mcp_server": settings.services.mcp.youtrack_url
            }

# Convenience function
async def process_bug_report(review: Review, project: str = None) -> Dict[str, Any]:
    """Process a bug report from a review using structured approach with MCP"""
    bot = BugBotAgent(project=project or settings.youtrack_projects.default)
    return await bot.process_bug_review(review)