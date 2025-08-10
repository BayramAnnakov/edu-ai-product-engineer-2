"""
Ticket service for managing YouTrack ticket records
"""
import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import structlog

from .models import Ticket, Review
from src.constants import ReviewCategory
from .base import AsyncSessionLocal

logger = structlog.get_logger()


class TicketService:
    """Service for managing YouTrack ticket records"""
    
    def __init__(self, session: Optional[AsyncSession] = None):
        self._session = session
    
    async def get_session(self) -> AsyncSession:
        """Get database session"""
        if self._session:
            return self._session
        return AsyncSessionLocal()
    
    async def create_ticket(
        self,
        review_id: uuid.UUID,
        project: str,
        issue_id: Optional[str] = None,
        issue_number: Optional[int] = None,
        url: Optional[str] = None,
        title: str = "",
        duplicate_of: Optional[str] = None,
        similarity_score: Optional[float] = None
    ) -> Ticket:
        """Create a ticket record for YouTrack issue"""
        session = await self.get_session()
        
        ticket = Ticket(
            review_id=review_id,
            project=project,
            issue_id=issue_id,
            issue_number=issue_number,
            url=url,
            title=title,
            duplicate_of=duplicate_of,
            similarity_score=similarity_score
        )
        
        session.add(ticket)
        await session.commit()
        await session.refresh(ticket)
        
        logger.info("Created ticket record",
                   ticket_id=str(ticket.id),
                   issue_id=issue_id,
                   is_duplicate=bool(duplicate_of))
        
        return ticket
    
    async def get_ticket_by_issue_id(self, issue_id: str) -> Optional[Ticket]:
        """Get ticket by YouTrack issue ID"""
        session = await self.get_session()
        
        result = await session.execute(
            select(Ticket).where(Ticket.issue_id == issue_id)
        )
        
        return result.scalar_one_or_none()
    
    async def get_tickets_by_review(self, review_id: uuid.UUID) -> List[Ticket]:
        """Get all tickets associated with a review"""
        session = await self.get_session()
        
        result = await session.execute(
            select(Ticket)
            .where(Ticket.review_id == review_id)
            .order_by(Ticket.created_at.desc())
        )
        
        return result.scalars().all()
    
    async def count_duplicate_reports(self, issue_id: str) -> int:
        """Count how many times an issue has been reported as duplicate"""
        session = await self.get_session()
        
        result = await session.execute(
            select(func.count(Ticket.id))
            .where(Ticket.duplicate_of == issue_id)
        )
        
        return result.scalar() or 0
    
    async def get_recent_tickets(
        self,
        project: str,
        limit: int = 20,
        include_duplicates: bool = True
    ) -> List[Ticket]:
        """Get recent tickets for a project"""
        session = await self.get_session()
        
        query = select(Ticket).where(Ticket.project == project)
        
        if not include_duplicates:
            query = query.where(Ticket.duplicate_of.is_(None))
        
        result = await session.execute(
            query.order_by(Ticket.created_at.desc()).limit(limit)
        )
        
        return result.scalars().all()
    
    async def get_bug_reviews_without_tickets(self, limit: int = 10) -> List[Review]:
        """Get bug reviews that haven't been processed to tickets yet"""
        session = await self.get_session()
        
        # Subquery to find reviews with tickets
        reviews_with_tickets = select(Ticket.review_id).distinct()
        
        result = await session.execute(
            select(Review)
            .where(Review.category == ReviewCategory.BUG)
            .where(Review.id.notin_(reviews_with_tickets))
            .order_by(Review.confidence.desc())
            .limit(limit)
        )
        
        return result.scalars().all()


# Convenience function
async def create_ticket_service() -> TicketService:
    """Create a ticket service instance"""
    return TicketService()