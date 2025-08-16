"""Worker tasks for approval execution"""
import asyncio
import time
from typing import Dict, Any
from uuid import UUID
import structlog

from src.services.approval_executor import create_approval_executor
from src.db.approval_service import create_approval_service
from src.config import settings
from src.queues.metrics import queue_metrics

logger = structlog.get_logger()

async def startup(ctx: Dict[str, Any]) -> None:
    """Worker startup - initialize shared resources"""
    logger.info("Starting approval worker")
    
    # Create shared services
    ctx['approval_service'] = await create_approval_service()
    ctx['executor'] = await create_approval_executor()
    
    # Initialize executor services (YouTrack client, Slack client, etc.)
    await ctx['executor']._ensure_services()
    
    logger.info("Approval worker ready with initialized services")

async def shutdown(ctx: Dict[str, Any]) -> None:
    """Worker shutdown - cleanup resources"""
    logger.info("Shutting down approval worker")
    
    # Cleanup if needed
    if 'executor' in ctx:
        await ctx['executor'].stop()

async def execute_approval(
    ctx: Dict[str, Any],
    approval_id: str,
    risk: str,
    enqueued_at: str,
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute approved action
    
    Args:
        ctx: Worker context with shared services
        approval_id: UUID of approval to execute
        risk: Risk level string
        enqueued_at: When job was enqueued (ISO format)
        metadata: Additional job metadata
        
    Returns:
        Execution result
    """
    start_time = time.time()
    
    logger.info(
        "Executing approval",
        approval_id=approval_id,
        risk=risk
    )
    
    try:
        # Get services from context
        executor = ctx['executor']
        
        # Execute with timeout
        async with asyncio.timeout(settings.services_config.queue.job_timeout_seconds):
            result = await executor.execute_single_approval(UUID(approval_id))
            
        execution_time = time.time() - start_time
        
        # Record success metrics
        await queue_metrics.record_success(execution_time)
        
        logger.info(
            "Approval executed successfully",
            approval_id=approval_id,
            execution_time_seconds=execution_time
        )
        
        return {
            "success": True,
            "approval_id": approval_id,
            "execution_time_seconds": execution_time,
            "result": result
        }
        
    except asyncio.TimeoutError:
        # Record timeout metrics
        await queue_metrics.record_timeout()
        
        logger.error(
            "Approval execution timeout",
            approval_id=approval_id,
            timeout_seconds=settings.services_config.queue.job_timeout_seconds
        )
        raise  # Let arq handle retry
        
    except Exception as e:
        execution_time = time.time() - start_time
        
        # Record failure metrics
        await queue_metrics.record_failure(str(e))
        
        logger.error(
            "Approval execution failed",
            approval_id=approval_id,
            error=str(e),
            execution_time_seconds=execution_time
        )
        raise  # Let arq handle retry