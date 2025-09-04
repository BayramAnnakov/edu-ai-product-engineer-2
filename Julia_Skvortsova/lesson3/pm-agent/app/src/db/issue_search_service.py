"""
Issue search service for managing YouTrack issue search and duplicate detection workflow
"""
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
import structlog

from .models import (
    IssueSearchSession, IssueSearchQuery, IssueDuplicateCandidate, 
    IssueSearchProgress
)
from src.constants import IssueSearchStage
from .base import AsyncSessionLocal

logger = structlog.get_logger()


class IssueSearchService:
    """Service for managing YouTrack issue search sessions"""
    
    def __init__(self, session: Optional[AsyncSession] = None):
        self._session = session
    
    async def get_session(self) -> AsyncSession:
        """Get database session"""
        if self._session:
            return self._session
        return AsyncSessionLocal()
    
    async def create_issue_search_session(
        self,
        session_id: str,
        review_id: uuid.UUID,
        project: str,
        bug_report_text: str,
        max_candidates_to_analyze: int = 10,
        similarity_threshold: float = 0.75
    ) -> IssueSearchSession:
        """Create a new issue search session"""
        session = await self.get_session()
        
        analysis_session = IssueSearchSession(
            session_id=session_id,
            review_id=review_id,
            project=project,
            bug_report_text=bug_report_text,
            max_candidates_to_analyze=max_candidates_to_analyze,
            similarity_threshold=similarity_threshold
        )
        
        session.add(analysis_session)
        await session.commit()
        await session.refresh(analysis_session)
        
        logger.info("Created issue search session",
                   session_id=session_id,
                   review_id=str(review_id),
                   project=project)
        
        return analysis_session
    
    async def complete_issue_search_session(
        self,
        session_id: str,
        duplicate_found: bool,
        selected_duplicate_issue_id: Optional[str] = None,
        final_action: str = "created_issue",
        total_api_calls: int = 0,
        total_processing_time_ms: int = 0,
        total_candidates_found: int = 0,
        candidates_analyzed_in_detail: int = 0
    ) -> IssueSearchSession:
        """Complete an issue search session with results"""
        session = await self.get_session()
        
        result = await session.execute(
            select(IssueSearchSession).where(IssueSearchSession.session_id == session_id)
        )
        analysis_session = result.scalar_one_or_none()
        
        if not analysis_session:
            raise ValueError(f"Issue search session {session_id} not found")
        
        analysis_session.duplicate_found = duplicate_found
        analysis_session.selected_duplicate_issue_id = selected_duplicate_issue_id
        analysis_session.final_action = final_action
        analysis_session.total_api_calls = total_api_calls
        analysis_session.total_processing_time_ms = total_processing_time_ms
        analysis_session.total_candidates_found = total_candidates_found
        analysis_session.candidates_analyzed_in_detail = candidates_analyzed_in_detail
        analysis_session.completed_at = datetime.utcnow()
        
        await session.commit()
        await session.refresh(analysis_session)
        
        logger.info("Completed issue search session",
                   session_id=session_id,
                   duplicate_found=duplicate_found,
                   final_action=final_action)
        
        return analysis_session
    
    async def add_search_query(
        self,
        session_id: str,
        query: str,
        search_type: str,
        results_count: int = 0,
        execution_time_ms: int = 0
    ) -> IssueSearchQuery:
        """Add a search query to an issue search session"""
        session = await self.get_session()
        
        # Get the session
        result = await session.execute(
            select(IssueSearchSession).where(IssueSearchSession.session_id == session_id)
        )
        analysis_session = result.scalar_one_or_none()
        
        if not analysis_session:
            raise ValueError(f"Issue search session {session_id} not found")
        
        search_query = IssueSearchQuery(
            session_id=analysis_session.id,
            query=query,
            search_type=search_type,
            results_count=results_count,
            execution_time_ms=execution_time_ms
        )
        
        session.add(search_query)
        await session.commit()
        await session.refresh(search_query)
        
        return search_query
    
    async def add_candidate_issue(
        self,
        session_id: str,
        issue_id: str,
        title: str,
        description: Optional[str] = None,
        created_date: Optional[datetime] = None,
        **scores
    ) -> IssueDuplicateCandidate:
        """Add a candidate issue to an issue search session"""
        session = await self.get_session()
        
        # Get the session
        result = await session.execute(
            select(IssueSearchSession).where(IssueSearchSession.session_id == session_id)
        )
        analysis_session = result.scalar_one_or_none()
        
        if not analysis_session:
            raise ValueError(f"Issue search session {session_id} not found")
        
        candidate = IssueDuplicateCandidate(
            session_id=analysis_session.id,
            issue_id=issue_id,
            title=title,
            description=description,
            created_date=created_date,
            **scores
        )
        
        session.add(candidate)
        await session.commit()
        await session.refresh(candidate)
        
        return candidate
    
    async def update_candidate_analysis(
        self,
        session_id: str,
        issue_id: str,
        detailed_analysis_completed: bool = True,
        semantic_similarity_score: Optional[float] = None,
        problem_similarity_score: Optional[float] = None,
        context_similarity_score: Optional[float] = None,
        impact_similarity_score: Optional[float] = None,
        final_similarity_score: Optional[float] = None,
        duplicate_confidence: Optional[float] = None,
        analysis_notes: Optional[str] = None,
        selected_as_duplicate: bool = False
    ) -> IssueDuplicateCandidate:
        """Update candidate issue with detailed analysis results"""
        session = await self.get_session()
        
        # Get the session
        result = await session.execute(
            select(IssueSearchSession).where(IssueSearchSession.session_id == session_id)
        )
        analysis_session = result.scalar_one_or_none()
        
        if not analysis_session:
            raise ValueError(f"Issue search session {session_id} not found")
        
        # Get the candidate
        result = await session.execute(
            select(IssueDuplicateCandidate)
            .where(IssueDuplicateCandidate.session_id == analysis_session.id)
            .where(IssueDuplicateCandidate.issue_id == issue_id)
        )
        candidate = result.scalar_one_or_none()
        
        if not candidate:
            raise ValueError(f"Candidate issue {issue_id} not found in session {session_id}")
        
        # Update fields
        candidate.detailed_analysis_completed = detailed_analysis_completed
        if semantic_similarity_score is not None:
            candidate.semantic_similarity_score = semantic_similarity_score
        if problem_similarity_score is not None:
            candidate.problem_similarity_score = problem_similarity_score
        if context_similarity_score is not None:
            candidate.context_similarity_score = context_similarity_score
        if impact_similarity_score is not None:
            candidate.impact_similarity_score = impact_similarity_score
        if final_similarity_score is not None:
            candidate.final_similarity_score = final_similarity_score
        if duplicate_confidence is not None:
            candidate.duplicate_confidence = duplicate_confidence
        if analysis_notes is not None:
            candidate.analysis_notes = analysis_notes
        candidate.selected_as_duplicate = selected_as_duplicate
        candidate.analyzed_at = datetime.utcnow()
        
        await session.commit()
        await session.refresh(candidate)
        
        return candidate
    
    async def add_stage_progress(
        self,
        session_id: str,
        stage: IssueSearchStage,
        items_processed: int = 0,
        items_remaining: int = 0,
        stage_metadata: Optional[Dict[str, Any]] = None
    ) -> IssueSearchProgress:
        """Add stage progress tracking"""
        session = await self.get_session()
        
        # Get the session
        result = await session.execute(
            select(IssueSearchSession).where(IssueSearchSession.session_id == session_id)
        )
        analysis_session = result.scalar_one_or_none()
        
        if not analysis_session:
            raise ValueError(f"Issue search session {session_id} not found")
        
        progress = IssueSearchProgress(
            session_id=analysis_session.id,
            stage=stage,
            items_processed=items_processed,
            items_remaining=items_remaining,
            stage_metadata=stage_metadata or {}
        )
        
        session.add(progress)
        await session.commit()
        await session.refresh(progress)
        
        return progress
    
    async def complete_stage_progress(
        self,
        session_id: str,
        stage: IssueSearchStage,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> Optional[IssueSearchProgress]:
        """Complete a stage progress record"""
        session = await self.get_session()
        
        # Get the session
        result = await session.execute(
            select(IssueSearchSession).where(IssueSearchSession.session_id == session_id)
        )
        analysis_session = result.scalar_one_or_none()
        
        if not analysis_session:
            raise ValueError(f"Issue search session {session_id} not found")
        
        # Get the most recent stage progress for this stage
        result = await session.execute(
            select(IssueSearchProgress)
            .where(IssueSearchProgress.session_id == analysis_session.id)
            .where(IssueSearchProgress.stage == stage)
            .where(IssueSearchProgress.completed_at.is_(None))
            .order_by(IssueSearchProgress.started_at.desc())
        )
        progress = result.scalar_one_or_none()
        
        if not progress:
            logger.warning("No in-progress stage found to complete", session_id=session_id, stage=stage.value)
            return None
        
        progress.completed_at = datetime.utcnow()
        progress.success = success
        progress.error_message = error_message
        
        await session.commit()
        await session.refresh(progress)
        
        return progress
    
    async def get_issue_search_session(
        self, 
        session_id: str,
        include_details: bool = False
    ) -> Optional[IssueSearchSession]:
        """Get an issue search session with optional detailed data"""
        session = await self.get_session()
        
        query = select(IssueSearchSession).where(IssueSearchSession.session_id == session_id)
        
        if include_details:
            query = query.options(
                selectinload(IssueSearchSession.search_queries),
                selectinload(IssueSearchSession.candidate_issues),
                selectinload(IssueSearchSession.stage_progress)
            )
        
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_issue_search_stats(self, project: str) -> Dict[str, Any]:
        """Get statistics about issue search sessions"""
        session = await self.get_session()
        
        # Total sessions
        result = await session.execute(
            select(func.count(IssueSearchSession.id))
            .where(IssueSearchSession.project == project)
        )
        total_sessions = result.scalar() or 0
        
        # Sessions with duplicates found
        result = await session.execute(
            select(func.count(IssueSearchSession.id))
            .where(IssueSearchSession.project == project)
            .where(IssueSearchSession.duplicate_found == True)
        )
        duplicates_found = result.scalar() or 0
        
        # Average processing time
        result = await session.execute(
            select(func.avg(IssueSearchSession.total_processing_time_ms))
            .where(IssueSearchSession.project == project)
            .where(IssueSearchSession.completed_at.isnot(None))
        )
        avg_processing_time = result.scalar() or 0
        
        # Average candidates found
        result = await session.execute(
            select(func.avg(IssueSearchSession.total_candidates_found))
            .where(IssueSearchSession.project == project)
        )
        avg_candidates = result.scalar() or 0
        
        return {
            "total_sessions": total_sessions,
            "duplicates_found": duplicates_found,
            "duplicate_rate": duplicates_found / total_sessions if total_sessions > 0 else 0,
            "avg_processing_time_ms": float(avg_processing_time),
            "avg_candidates_found": float(avg_candidates),
            "project": project,
            "generated_at": datetime.utcnow().isoformat()
        }


# Convenience function
async def create_issue_search_service() -> IssueSearchService:
    """Create an issue search service instance"""
    return IssueSearchService()