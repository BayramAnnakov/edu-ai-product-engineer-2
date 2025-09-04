"""
Review service for managing review classifications
"""
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import structlog

from .models import Review
from src.constants import ReviewCategory
from .base import AsyncSessionLocal

logger = structlog.get_logger()


class ReviewService:
    """Service for managing review classifications"""
    
    def __init__(self, session: Optional[AsyncSession] = None):
        self._session = session
    
    async def get_session(self) -> AsyncSession:
        """Get database session"""
        if self._session:
            return self._session
        return AsyncSessionLocal()
    
    async def store_review_classification(
        self,
        run_id: uuid.UUID,
        text: str,
        category: ReviewCategory,
        confidence: float,
        source: Optional[str] = None,
        original_rating: Optional[int] = None,
        original_id: Optional[str] = None
    ) -> Review:
        """Store a classified review"""
        session = await self.get_session()
        
        review = Review(
            text=text,
            category=category,
            confidence=confidence,
            run_id=run_id,
            source=source,
            original_rating=original_rating,
            original_id=original_id
        )
        
        session.add(review)
        await session.commit()
        await session.refresh(review)
        
        logger.info("Stored review classification",
                   review_id=str(review.id),
                   category=category.value,
                   confidence=confidence)
        
        return review
    
    async def get_reviews_by_category(
        self, 
        category: ReviewCategory,
        limit: int = 100
    ) -> List[Review]:
        """Get reviews by category"""
        session = await self.get_session()
        
        result = await session.execute(
            select(Review)
            .where(Review.category == category)
            .order_by(Review.confidence.desc())
            .limit(limit)
        )
        
        return result.scalars().all()
    
    async def get_classification_stats(self) -> Dict[str, Any]:
        """Get classification statistics"""
        session = await self.get_session()
        
        # Count by category
        result = await session.execute(
            select(Review.category, func.count(Review.id))
            .group_by(Review.category)
        )
        
        category_counts = dict(result.all())
        
        # Average confidence by category
        result = await session.execute(
            select(Review.category, func.avg(Review.confidence))
            .group_by(Review.category)
        )
        
        avg_confidence = dict(result.all())
        
        # Total reviews
        result = await session.execute(select(func.count(Review.id)))
        total_reviews = result.scalar()
        
        return {
            "total_reviews": total_reviews,
            "category_counts": {cat.value: count for cat, count in category_counts.items()},
            "avg_confidence": {cat.value: float(conf) for cat, conf in avg_confidence.items()},
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def get_review_by_id(self, review_id: uuid.UUID) -> Optional[Review]:
        """Get review by ID"""
        session = await self.get_session()
        
        result = await session.execute(
            select(Review).where(Review.id == review_id)
        )
        
        return result.scalar_one_or_none()


# Convenience function
async def create_review_service() -> ReviewService:
    """Create a review service instance"""
    return ReviewService()


async def store_classification_batch(
    reviews_data: List[Dict[str, Any]],
    workflow_run_id: uuid.UUID
) -> List[Review]:
    """Store a batch of classifications"""
    service = await create_review_service()
    stored_reviews = []
    
    for review_data in reviews_data:
        review = await service.store_review_classification(
            run_id=workflow_run_id,
            text=review_data['text'],
            category=ReviewCategory(review_data['category']),
            confidence=review_data['confidence'],
            source=review_data.get('source'),
            original_rating=review_data.get('rating')
        )
        stored_reviews.append(review)
    
    return stored_reviews