"""
Database service for feature research workflow
"""
import uuid
import structlog
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, update, desc, and_

from .models import (
    FeatureResearchSession,
    WebResearchFinding,
    WebSearchQuery, 
    CompetitorAnalysis,
    FeatureResearchProgress,
    Review
)
from src.constants import FeatureResearchStage, ResearchConfidence
from .base import AsyncSessionLocal
from src.schemas.feature_research import (
    CompetitorFinding,
    CompetitorFeatureAnalysis,
    CompetitorResearchReport,
    FeatureResearchPlan
)

logger = structlog.get_logger()


class FeatureResearchService:
    """Service for managing feature research workflow data"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_research_session(
        self,
        review_id: uuid.UUID,
        feature_description: str,
        project: str,
        competitors_list: List[str],
        session_id: Optional[str] = None,
        langfuse_trace_id: Optional[str] = None
    ) -> FeatureResearchSession:
        """Create a new feature research session"""
        
        if not session_id:
            session_id = str(uuid.uuid4())
        
        research_session = FeatureResearchSession(
            session_id=session_id,
            review_id=review_id,
            feature_description=feature_description,
            project=project,
            competitors_list=competitors_list,
            langfuse_trace_id=langfuse_trace_id,
            status="pending",
            current_stage="planning"
        )
        
        self.session.add(research_session)
        await self.session.commit()
        await self.session.refresh(research_session)
        
        logger.info("Created feature research session",
                   session_id=session_id,
                   review_id=str(review_id),
                   feature=feature_description[:100])
        
        return research_session
    
    async def get_research_session(
        self,
        session_id: str,
        include_relationships: bool = False
    ) -> Optional[FeatureResearchSession]:
        """Get research session by ID"""
        
        query = select(FeatureResearchSession).where(
            FeatureResearchSession.session_id == session_id
        )
        
        if include_relationships:
            query = query.options(
                selectinload(FeatureResearchSession.findings),
                selectinload(FeatureResearchSession.queries),
                selectinload(FeatureResearchSession.analyses),
                selectinload(FeatureResearchSession.stage_progress)
            )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def update_session_stage(
        self,
        session_id: str,
        stage: FeatureResearchStage,
        agent_name: str
    ) -> None:
        """Update the current stage of research session"""
        
        # Update session current stage
        await self.session.execute(
            update(FeatureResearchSession)
            .where(FeatureResearchSession.session_id == session_id)
            .values(current_stage=stage.value)
        )
        
        # Create stage progress record
        stage_progress = FeatureResearchProgress(
            session_id=(await self.get_research_session(session_id)).id,
            stage=stage,
            agent_name=agent_name,
            started_at=datetime.utcnow()
        )
        
        self.session.add(stage_progress)
        await self.session.commit()
        
        logger.info("Updated research session stage",
                   session_id=session_id,
                   stage=stage.value,
                   agent=agent_name)
    
    async def complete_stage(
        self,
        session_id: str,
        stage: FeatureResearchStage,
        success: bool,
        items_processed: int = 0,
        error_message: Optional[str] = None,
        stage_metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Mark a stage as completed"""
        
        session = await self.get_research_session(session_id)
        if not session:
            raise ValueError(f"Research session not found: {session_id}")
        
        # Find the most recent stage progress record
        result = await self.session.execute(
            select(FeatureResearchProgress)
            .where(
                and_(
                    FeatureResearchProgress.session_id == session.id,
                    FeatureResearchProgress.stage == stage
                )
            )
            .order_by(desc(FeatureResearchProgress.started_at))
            .limit(1)
        )
        stage_progress = result.scalar_one_or_none()
        
        if stage_progress:
            stage_progress.completed_at = datetime.utcnow()
            stage_progress.success = success
            stage_progress.items_processed = items_processed
            stage_progress.error_message = error_message
            if stage_metadata:
                stage_progress.stage_metadata = stage_metadata
            
            await self.session.commit()
            
            logger.info("Completed research stage",
                       session_id=session_id,
                       stage=stage.value,
                       success=success,
                       items_processed=items_processed)
    
    async def add_research_finding(
        self,
        session_id: str,
        finding: CompetitorFinding,
        search_query: Optional[str] = None,
        agent_name: Optional[str] = None
    ) -> WebResearchFinding:
        """Add a research finding to the session"""
        
        session = await self.get_research_session(session_id)
        if not session:
            raise ValueError(f"Research session not found: {session_id}")
        
        # Convert confidence string to enum
        confidence_map = {
            "low": ResearchConfidence.LOW,
            "medium": ResearchConfidence.MEDIUM,
            "high": ResearchConfidence.HIGH
        }
        confidence_enum = confidence_map.get(finding.confidence, ResearchConfidence.MEDIUM)
        
        research_finding = WebResearchFinding(
            session_id=session.id,
            competitor=finding.competitor,
            feature=finding.feature,
            claim=finding.claim,
            evidence_url=str(finding.evidence_url),
            evidence_snippet=finding.evidence_snippet,
            confidence=confidence_enum,
            is_official_source=finding.is_official_source,
            date_found=finding.date_found,
            search_query_used=search_query,
            found_by_agent=agent_name
        )
        
        self.session.add(research_finding)
        await self.session.commit()
        await self.session.refresh(research_finding)
        
        logger.info("Added research finding",
                   session_id=session_id,
                   competitor=finding.competitor,
                   confidence=finding.confidence)
        
        return research_finding
    
    async def add_research_query(
        self,
        session_id: str,
        query: str,
        search_type: Optional[str] = None,
        target_competitor: Optional[str] = None,
        agent_name: Optional[str] = None,
        results_count: int = 0,
        findings_extracted: int = 0,
        execution_time_ms: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> WebSearchQuery:
        """Record a web search query"""
        
        session = await self.get_research_session(session_id)
        if not session:
            raise ValueError(f"Research session not found: {session_id}")
        
        research_query = WebSearchQuery(
            session_id=session.id,
            query=query,
            search_type=search_type,
            target_competitor=target_competitor,
            executed_by_agent=agent_name,
            results_count=results_count,
            findings_extracted=findings_extracted,
            execution_time_ms=execution_time_ms,
            success=success,
            error_message=error_message
        )
        
        self.session.add(research_query)
        await self.session.commit()
        await self.session.refresh(research_query)
        
        logger.debug("Recorded research query",
                    session_id=session_id,
                    query=query[:50],
                    results=results_count)
        
        return research_query
    
    async def add_competitor_analysis(
        self,
        session_id: str,
        analysis: CompetitorFeatureAnalysis
    ) -> CompetitorAnalysis:
        """Add competitor analysis results"""
        
        session = await self.get_research_session(session_id)
        if not session:
            raise ValueError(f"Research session not found: {session_id}")
        
        competitor_analysis = CompetitorAnalysis(
            session_id=session.id,
            competitor=analysis.competitor,
            feature=analysis.feature,
            has_feature=analysis.has_feature,
            implementation_details=analysis.implementation_details,
            pricing_tier=analysis.pricing_tier,
            limitations=analysis.limitations,
            strengths=analysis.strengths,
            last_updated=analysis.last_updated,
            proof_urls=[str(url) for url in analysis.proof_urls],
            analysis_notes=analysis.analysis_notes,
            confidence_score=None  # Could be derived from findings
        )
        
        self.session.add(competitor_analysis)
        await self.session.commit()
        await self.session.refresh(competitor_analysis)
        
        logger.info("Added competitor analysis",
                   session_id=session_id,
                   competitor=analysis.competitor,
                   has_feature=analysis.has_feature)
        
        return competitor_analysis
    
    async def complete_research_session(
        self,
        session_id: str,
        final_report: CompetitorResearchReport,
        processing_time_ms: int,
        agent_turns_used: int = 0,
        web_searches_performed: int = 0
    ) -> None:
        """Complete the research session with final results"""
        
        session = await self.get_research_session(session_id)
        if not session:
            raise ValueError(f"Research session not found: {session_id}")
        
        # Update session with final results
        session.status = "completed"
        session.completed_at = datetime.utcnow()
        session.processing_time_ms = processing_time_ms
        session.agent_turns_used = agent_turns_used
        session.web_searches_performed = web_searches_performed
        
        # Store final deliverables
        session.feature_spec_json = final_report.feature_spec.model_dump()
        session.competitor_matrix_json = final_report.competitor_matrix.model_dump()
        session.final_report_json = final_report.model_dump()
        
        # Calculate metrics
        session.total_competitors_analyzed = len(final_report.competitor_matrix.rows)
        session.total_evidence_urls = len(final_report.appendix_sources)
        session.research_quality_score = final_report.research_quality_score
        
        await self.session.commit()
        
        logger.info("Completed research session",
                   session_id=session_id,
                   competitors_analyzed=session.total_competitors_analyzed,
                   evidence_urls=session.total_evidence_urls,
                   processing_time_ms=processing_time_ms)
    
    async def fail_research_session(
        self,
        session_id: str,
        error_message: str,
        processing_time_ms: Optional[int] = None
    ) -> None:
        """Mark research session as failed"""
        
        await self.session.execute(
            update(FeatureResearchSession)
            .where(FeatureResearchSession.session_id == session_id)
            .values(
                status="failed",
                completed_at=datetime.utcnow(),
                processing_time_ms=processing_time_ms
            )
        )
        await self.session.commit()
        
        logger.error("Research session failed",
                    session_id=session_id,
                    error=error_message)
    
    async def get_research_sessions_by_review(
        self,
        review_id: uuid.UUID
    ) -> List[FeatureResearchSession]:
        """Get all research sessions for a review"""
        
        result = await self.session.execute(
            select(FeatureResearchSession)
            .where(FeatureResearchSession.review_id == review_id)
            .order_by(desc(FeatureResearchSession.created_at))
        )
        return result.scalars().all()
    
    async def get_recent_research_sessions(
        self,
        project: str,
        limit: int = 10
    ) -> List[FeatureResearchSession]:
        """Get recent research sessions for a project"""
        
        result = await self.session.execute(
            select(FeatureResearchSession)
            .where(FeatureResearchSession.project == project)
            .order_by(desc(FeatureResearchSession.created_at))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_session_metrics(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """Get comprehensive metrics for a research session"""
        
        session = await self.get_research_session(session_id, include_relationships=True)
        if not session:
            return {}
        
        # Calculate various metrics
        total_findings = len(session.findings)
        high_confidence_findings = sum(1 for f in session.findings if f.confidence == ResearchConfidence.HIGH)
        official_sources = sum(1 for f in session.findings if f.is_official_source)
        
        successful_queries = sum(1 for q in session.queries if q.success)
        total_queries = len(session.queries)
        
        completed_stages = sum(1 for s in session.stage_progress if s.success)
        total_stages = len(session.stage_progress)
        
        return {
            "session_id": session_id,
            "status": session.status,
            "total_findings": total_findings,
            "high_confidence_findings": high_confidence_findings,
            "official_sources": official_sources,
            "successful_queries": successful_queries,
            "total_queries": total_queries,
            "query_success_rate": successful_queries / total_queries if total_queries > 0 else 0,
            "completed_stages": completed_stages,
            "total_stages": total_stages,
            "stage_completion_rate": completed_stages / total_stages if total_stages > 0 else 0,
            "competitors_analyzed": session.total_competitors_analyzed,
            "evidence_urls": session.total_evidence_urls,
            "research_quality_score": session.research_quality_score,
            "processing_time_ms": session.processing_time_ms,
            "agent_turns_used": session.agent_turns_used,
            "web_searches_performed": session.web_searches_performed
        }


# Global service factory
async def create_feature_research_service() -> FeatureResearchService:
    """Create feature research service with database session"""
    session = await get_session()
    return FeatureResearchService(session)