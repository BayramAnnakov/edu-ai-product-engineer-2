"""Redis queue client for approval processing"""
import asyncio
from typing import Optional, Dict, Any
from uuid import UUID
import json
from datetime import datetime

from arq import create_pool
from arq.connections import RedisSettings, ArqRedis
from arq.jobs import Job
import structlog

from src.config import settings
from db.models import RiskLevel

logger = structlog.get_logger()

class ApprovalQueueClient:
    """Client for managing approval execution queue"""
    
    def __init__(self):
        self.redis_settings = RedisSettings.from_dsn(settings.services_config.queue.redis_url)
        self._pool: Optional[ArqRedis] = None
        
    async def connect(self):
        """Connect to Redis"""
        if not self._pool:
            self._pool = await create_pool(self.redis_settings)
            logger.info("Connected to Redis queue")
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self._pool:
            await self._pool.close()
            self._pool = None
            
    async def enqueue_approval(
        self, 
        approval_id: UUID, 
        risk: RiskLevel,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Job:
        """Enqueue approval for execution"""
        if not self._pool:
            await self.connect()
            
        queue_name = self._get_queue_by_risk(risk)
        
        job_data = {
            "approval_id": str(approval_id),
            "risk": risk.value,
            "enqueued_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        job = await self._pool.enqueue_job(
            'execute_approval',
            **job_data,
            _queue_name=queue_name,
            _job_id=f"approval:{approval_id}",
            _defer_by=0,  # Execute immediately
            _expire=settings.services_config.queue.job_timeout_seconds
        )
        
        logger.info(
            "Approval enqueued",
            approval_id=str(approval_id),
            queue=queue_name,
            job_id=job.job_id
        )
        
        return job
        
    def _get_queue_by_risk(self, risk: RiskLevel) -> str:
        """Get queue name based on risk level"""
        return settings.services_config.queue.queue_by_risk.get(
            risk.value, 
            settings.services_config.queue.normal_queue
        )

    async def get_queue_info(self) -> Dict[str, Any]:
        """Get queue status information for monitoring"""
        if not self._pool:
            await self.connect()
            
        info = {}
        for risk, queue_name in settings.services_config.queue.queue_by_risk.items():
            try:
                # Get queue length
                length = await self._pool.llen(queue_name)
                info[queue_name] = {
                    "risk_level": risk,
                    "pending_jobs": length
                }
            except Exception as e:
                logger.warning(f"Failed to get info for queue {queue_name}: {e}")
                info[queue_name] = {
                    "risk_level": risk,
                    "pending_jobs": -1,
                    "error": str(e)
                }
                
        return info

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()