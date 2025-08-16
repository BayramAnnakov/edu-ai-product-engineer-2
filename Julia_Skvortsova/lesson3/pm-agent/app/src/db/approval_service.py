"""
Approval service for managing HITL approval workflow
"""
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from .models import Approval, ApprovalStatus, RiskLevel
from src.constants import SystemActionType
from .base import AsyncSessionLocal
from src.config import settings

logger = structlog.get_logger()


class ApprovalService:
    """Service for managing approval workflow"""
    
    def __init__(self, session: Optional[AsyncSession] = None):
        self._session = session
    
    async def get_session(self) -> AsyncSession:
        """Get database session"""
        if self._session:
            return self._session
        return AsyncSessionLocal()
    
    async def create_approval(
        self,
        action_type: SystemActionType,
        payload_json: Dict[str, Any],
        risk: RiskLevel = RiskLevel.MEDIUM,
        reviewer_whitelist: Optional[List[str]] = None,
        slack_channel: Optional[str] = None,
        expires_in_hours: int = 48,
        related_entity_id: Optional[uuid.UUID] = None,
        langfuse_trace_id: Optional[str] = None
    ) -> Approval:
        """
        Create a new approval request
        
        Args:
            action_type: Type of action requiring approval
            payload_json: JSON payload with action details
            risk: Risk level assessment
            reviewer_whitelist: Optional list of allowed reviewers
            slack_channel: Slack channel for notification
            expires_in_hours: Hours until approval expires
            related_entity_id: Related entity ID (e.g., review_id)
            langfuse_trace_id: Trace ID for observability
            
        Returns:
            Created Approval object
        """
        session = await self.get_session()
        
        approval = Approval(
            action_type=action_type,
            payload_json=payload_json,
            risk=risk,
            status=ApprovalStatus.PENDING,
            reviewer_whitelist=reviewer_whitelist,
            slack_channel=slack_channel or settings.integrations.slack.default_channel,
            expires_at=datetime.utcnow() + timedelta(hours=expires_in_hours),
            related_entity_id=related_entity_id,
            langfuse_trace_id=langfuse_trace_id
        )
        
        session.add(approval)
        await session.commit()
        await session.refresh(approval)
        
        logger.info(
            "Created approval request",
            approval_id=str(approval.id),
            action_type=action_type.value,
            risk=risk.value
        )
        
        return approval
    
    async def get_approval(self, approval_id: uuid.UUID) -> Optional[Approval]:
        """Get approval by ID"""
        session = await self.get_session()
        
        result = await session.execute(
            select(Approval).where(Approval.id == approval_id)
        )
        
        return result.scalar_one_or_none()
    
    async def approve(
        self,
        approval_id: uuid.UUID,
        decided_by: str,
        reason: Optional[str] = None
    ) -> Approval:
        """
        Approve an action
        
        Args:
            approval_id: ID of the approval
            decided_by: User who approved
            reason: Optional reason for approval
            
        Returns:
            Updated Approval object
        """
        session = await self.get_session()
        
        # Query approval in the current session
        result = await session.execute(
            select(Approval).where(Approval.id == approval_id)
        )
        approval = result.scalar_one_or_none()
        
        if not approval:
            raise ValueError(f"Approval {approval_id} not found")
        
        if approval.status != ApprovalStatus.PENDING:
            raise ValueError(f"Approval {approval_id} is not pending (status: {approval.status})")
        
        # Check if reviewer is whitelisted
        if approval.reviewer_whitelist and decided_by not in approval.reviewer_whitelist:
            raise ValueError(f"User {decided_by} is not authorized to approve this action")
        
        approval.status = ApprovalStatus.APPROVED
        approval.decided_at = datetime.utcnow()
        approval.decided_by = decided_by
        approval.reason = reason
        
        await session.commit()
        await session.refresh(approval)
        
        logger.info(
            "Approval granted",
            approval_id=str(approval_id),
            decided_by=decided_by
        )

        # Immediately queue for execution instead of waiting for polling
        from queues.client import ApprovalQueueClient
        
        async with ApprovalQueueClient() as queue_client:
            try:
                await queue_client.enqueue_approval(
                    approval_id=approval.id,
                    risk=approval.risk,
                    metadata={
                        "decided_by": decided_by,
                        "action_type": approval.action_type.value
                    }
                )
                logger.info(f"Approval {approval_id} queued for execution")
            except Exception as e:
                logger.error(f"Failed to queue approval {approval_id}: {e}")
                # Don't fail the approval - worker will pick it up eventually
        
        return approval
    
    async def reject(
        self,
        approval_id: uuid.UUID,
        decided_by: str,
        reason: str
    ) -> Approval:
        """
        Reject an action
        
        Args:
            approval_id: ID of the approval
            decided_by: User who rejected
            reason: Reason for rejection
            
        Returns:
            Updated Approval object
        """
        session = await self.get_session()
        
        # Query approval in the current session
        result = await session.execute(
            select(Approval).where(Approval.id == approval_id)
        )
        approval = result.scalar_one_or_none()
        
        if not approval:
            raise ValueError(f"Approval {approval_id} not found")
        
        if approval.status != ApprovalStatus.PENDING:
            raise ValueError(f"Approval {approval_id} is not pending (status: {approval.status})")
        
        approval.status = ApprovalStatus.REJECTED
        approval.decided_at = datetime.utcnow()
        approval.decided_by = decided_by
        approval.reason = reason
        
        await session.commit()
        await session.refresh(approval)
        
        logger.info(
            "Approval rejected",
            approval_id=str(approval_id),
            decided_by=decided_by,
            reason=reason
        )
        
        return approval
    
    async def mark_executed(
        self,
        approval_id: uuid.UUID,
        execution_result: Optional[Dict[str, Any]] = None,
        execution_error: Optional[str] = None
    ) -> Approval:
        """
        Mark approval as executed
        
        Args:
            approval_id: ID of the approval
            execution_result: Result of execution
            execution_error: Error if execution failed
            
        Returns:
            Updated Approval object
        """
        session = await self.get_session()
        
        approval = await self.get_approval(approval_id)
        if not approval:
            raise ValueError(f"Approval {approval_id} not found")
        
        if approval.status != ApprovalStatus.APPROVED:
            raise ValueError(f"Approval {approval_id} is not approved (status: {approval.status})")
        
        approval.status = ApprovalStatus.EXECUTED
        approval.executed_at = datetime.utcnow()
        approval.execution_result = execution_result
        approval.execution_error = execution_error
        
        await session.commit()
        await session.refresh(approval)
        
        logger.info(
            "Approval executed",
            approval_id=str(approval_id),
            success=execution_error is None
        )
        
        return approval
    
    async def get_pending_approvals(
        self,
        action_type: Optional[SystemActionType] = None,
        include_expired: bool = False
    ) -> List[Approval]:
        """
        Get pending approvals
        
        Args:
            action_type: Optional filter by action type
            include_expired: Whether to include expired approvals
            
        Returns:
            List of pending approvals
        """
        session = await self.get_session()
        
        query = select(Approval).where(Approval.status == ApprovalStatus.PENDING)
        
        if action_type:
            query = query.where(Approval.action_type == action_type)
        
        if not include_expired:
            query = query.where(
                or_(
                    Approval.expires_at.is_(None),
                    Approval.expires_at > datetime.utcnow()
                )
            )
        
        result = await session.execute(query.order_by(Approval.created_at))
        return result.scalars().all()
    
    async def get_pending_approvals_for_entity(
        self,
        entity_id: uuid.UUID
    ) -> List[Approval]:
        """
        Get pending approvals for a specific entity
        
        Args:
            entity_id: Related entity ID
            
        Returns:
            List of pending approvals for the entity
        """
        session = await self.get_session()
        
        result = await session.execute(
            select(Approval)
            .where(
                and_(
                    Approval.related_entity_id == entity_id,
                    Approval.status == ApprovalStatus.PENDING
                )
            )
            .order_by(Approval.created_at)
        )
        
        return result.scalars().all()
    
    async def expire_old_approvals(self) -> int:
        """
        Mark expired approvals as expired
        
        Returns:
            Number of approvals expired
        """
        session = await self.get_session()
        
        result = await session.execute(
            select(Approval)
            .where(
                and_(
                    Approval.status == ApprovalStatus.PENDING,
                    Approval.expires_at < datetime.utcnow()
                )
            )
        )
        
        expired_approvals = result.scalars().all()
        count = 0
        
        for approval in expired_approvals:
            approval.status = ApprovalStatus.EXPIRED
            count += 1
        
        if count > 0:
            await session.commit()
            logger.info(f"Expired {count} old approvals")
        
        return count
    
    async def get_approval_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get approval statistics
        
        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Dictionary with approval statistics
        """
        session = await self.get_session()
        
        query = select(Approval)
        
        if start_date:
            query = query.where(Approval.created_at >= start_date)
        if end_date:
            query = query.where(Approval.created_at <= end_date)
        
        result = await session.execute(query)
        approvals = result.scalars().all()
        
        # Calculate stats
        total = len(approvals)
        pending = sum(1 for a in approvals if a.status == ApprovalStatus.PENDING)
        approved = sum(1 for a in approvals if a.status == ApprovalStatus.APPROVED)
        rejected = sum(1 for a in approvals if a.status == ApprovalStatus.REJECTED)
        executed = sum(1 for a in approvals if a.status == ApprovalStatus.EXECUTED)
        expired = sum(1 for a in approvals if a.status == ApprovalStatus.EXPIRED)
        
        # Calculate average response time for decided approvals
        response_times = []
        for approval in approvals:
            if approval.decided_at and approval.created_at:
                response_time = (approval.decided_at - approval.created_at).total_seconds()
                response_times.append(response_time)
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            "total": total,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "executed": executed,
            "expired": expired,
            "approval_rate": approved / (approved + rejected) if (approved + rejected) > 0 else 0,
            "avg_response_time_seconds": avg_response_time,
            "generated_at": datetime.utcnow().isoformat()
        }


# Convenience function
async def create_approval_service() -> ApprovalService:
    """Create an approval service instance"""
    return ApprovalService()