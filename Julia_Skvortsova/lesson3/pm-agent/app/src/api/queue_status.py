"""Queue monitoring endpoints"""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
import structlog

from queues.client import ApprovalQueueClient
from queues.metrics import queue_metrics

logger = structlog.get_logger()
router = APIRouter()

@router.get("/queue/status")
async def get_queue_status() -> Dict[str, Any]:
    """Get current queue status for monitoring"""
    try:
        async with ApprovalQueueClient() as queue_client:
            info = await queue_client.get_queue_info()
            
        # Calculate totals
        total_pending = sum(
            queue_info.get("pending_jobs", 0) 
            for queue_info in info.values()
            if isinstance(queue_info.get("pending_jobs"), int) and queue_info["pending_jobs"] >= 0
        )
        
        return {
            "status": "healthy",
            "total_pending_jobs": total_pending,
            "queues": info,
            "timestamp": "now"
        }
        
    except Exception as e:
        logger.error("Failed to get queue status", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get queue status: {str(e)}"
        )

@router.get("/health/queue")
async def health_check() -> Dict[str, str]:
    """Simple queue health check"""
    try:
        async with ApprovalQueueClient() as queue_client:
            await queue_client.connect()
            
        return {"status": "healthy", "service": "queue"}
        
    except Exception as e:
        logger.error("Queue health check failed", error=str(e))
        raise HTTPException(
            status_code=503,
            detail="Queue service unavailable"
        )

@router.get("/queue/metrics")
async def get_queue_metrics() -> Dict[str, Any]:
    """Get queue execution metrics"""
    try:
        stats = queue_metrics.get_stats()
        return {
            "queue_metrics": stats,
            "timestamp": "now"
        }
        
    except Exception as e:
        logger.error("Failed to get queue metrics", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get queue metrics: {str(e)}"
        )