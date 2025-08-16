"""
Workflow service for managing workflow runs
"""
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import structlog

from .models import WorkflowRun
from .base import AsyncSessionLocal

logger = structlog.get_logger()


class WorkflowService:
    """Service for managing workflow runs"""
    
    def __init__(self, session: Optional[AsyncSession] = None):
        self._session = session
    
    async def get_session(self) -> AsyncSession:
        """Get database session"""
        if self._session:
            return self._session
        return AsyncSessionLocal()
    
    async def create_workflow_run(
        self, 
        input_text: str, 
        langfuse_trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> WorkflowRun:
        """Create a new workflow run"""
        session = await self.get_session()
        
        workflow_run = WorkflowRun(
            input_text=input_text,
            status="running",
            langfuse_trace_id=langfuse_trace_id,
            run_metadata=metadata or {}
        )
        
        session.add(workflow_run)
        await session.commit()
        await session.refresh(workflow_run)
        
        logger.info("Created workflow run", 
                   run_id=str(workflow_run.id),
                   trace_id=langfuse_trace_id)
        
        return workflow_run
    
    async def complete_workflow_run(
        self,
        run_id: uuid.UUID,
        result_text: str,
        status: str = "completed"
    ) -> WorkflowRun:
        """Mark workflow run as completed"""
        session = await self.get_session()
        
        result = await session.execute(
            select(WorkflowRun).where(WorkflowRun.id == run_id)
        )
        workflow_run = result.scalar_one_or_none()
        
        if not workflow_run:
            raise ValueError(f"Workflow run {run_id} not found")
        
        workflow_run.result_text = result_text
        workflow_run.status = status
        workflow_run.completed_at = datetime.utcnow()
        
        await session.commit()
        await session.refresh(workflow_run)
        
        logger.info("Completed workflow run",
                   run_id=str(run_id),
                   status=status)
        
        return workflow_run
    
    async def get_workflow_run_with_reviews(self, run_id: uuid.UUID) -> Optional[WorkflowRun]:
        """Get workflow run with all its reviews"""
        session = await self.get_session()
        
        result = await session.execute(
            select(WorkflowRun)
            .options(selectinload(WorkflowRun.reviews))
            .where(WorkflowRun.id == run_id)
        )
        
        return result.scalar_one_or_none()
    
    async def get_workflow_run(self, run_id: uuid.UUID) -> Optional[WorkflowRun]:
        """Get workflow run by ID"""
        session = await self.get_session()
        
        result = await session.execute(
            select(WorkflowRun).where(WorkflowRun.id == run_id)
        )
        
        return result.scalar_one_or_none()


# Convenience function
async def create_workflow_service() -> WorkflowService:
    """Create a workflow service instance"""
    return WorkflowService()