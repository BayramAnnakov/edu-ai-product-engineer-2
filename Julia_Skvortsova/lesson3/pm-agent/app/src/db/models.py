from sqlalchemy import (
    Column, String, Float, Text, DateTime, ForeignKey, 
    JSON, ARRAY, Enum as SQLEnum, Index, UniqueConstraint,
    Boolean, Integer
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
import uuid
from .base import Base

# Import centralized constants
from src.constants import (
    ReviewCategory,
    ApprovalStatus,
    RiskLevel,
    SystemActionType,
    IssueSearchStage,
    FeatureResearchStage,
    ResearchConfidence
)

class WorkflowRun(Base):
    __tablename__ = "workflow_runs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    input_text = Column(Text, nullable=False)
    result_text = Column(Text)
    status = Column(String(50), nullable=False, default="pending")
    langfuse_trace_id = Column(String(255), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))
    run_metadata = Column(JSON, default={})
    
    # Relationships
    reviews = relationship("Review", back_populates="workflow_run", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_workflow_runs_created_at', 'created_at'),
        Index('idx_workflow_runs_status', 'status'),
    )

class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_id = Column(String(255), index=True)  # Original ID from CSV file
    text = Column(Text, nullable=False)
    category = Column(SQLEnum(ReviewCategory), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    run_id = Column(UUID(as_uuid=True), ForeignKey("workflow_runs.id", ondelete="CASCADE"))
    source = Column(String(100))  # e.g., "app_store", "play_store", "web"
    original_rating = Column(Integer)
    processed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    workflow_run = relationship("WorkflowRun", back_populates="reviews")
    tickets = relationship("Ticket", back_populates="review", cascade="all, delete-orphan")
    feature_reports = relationship("FeatureReport", back_populates="review", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_reviews_category_confidence', 'category', 'confidence'),
    )
    
    @validates('confidence')
    def validate_confidence(self, key, value):
        if not 0 <= value <= 1:
            raise ValueError("Confidence must be between 0 and 1")
        return value

class Ticket(Base):
    __tablename__ = "tickets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id = Column(UUID(as_uuid=True), ForeignKey("reviews.id", ondelete="CASCADE"))
    project = Column(String(100), nullable=False)
    issue_id = Column(String(50), unique=True)
    issue_number = Column(Integer)
    url = Column(Text)
    title = Column(String(255), nullable=False)
    duplicate_of = Column(String(50))
    similarity_score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    review = relationship("Review", back_populates="tickets")
    fix_suggestions = relationship("FixSuggestion", back_populates="ticket", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_tickets_project_created', 'project', 'created_at'),
        UniqueConstraint('review_id', 'project', name='uq_review_project'),
    )

class FeatureReport(Base):
    __tablename__ = "feature_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id = Column(UUID(as_uuid=True), ForeignKey("reviews.id", ondelete="CASCADE"))
    summary_md = Column(Text, nullable=False)
    competitor_analysis = Column(JSON)
    sources_json = Column(JSON)
    feature_spec = Column(JSON)
    status = Column(String(50), default="draft")
    slack_thread_ts = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    approved_at = Column(DateTime(timezone=True))
    approved_by = Column(String(100))
    
    # Relationships
    review = relationship("Review", back_populates="feature_reports")
    
    __table_args__ = (
        Index('idx_feature_reports_status', 'status'),
    )

class FixSuggestion(Base):
    __tablename__ = "fix_suggestions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"))
    file_path = Column(Text, nullable=False)
    snippet = Column(Text)
    diff_md = Column(Text, nullable=False)
    confidence = Column(Float)
    line_start = Column(Integer)
    line_end = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    ticket = relationship("Ticket", back_populates="fix_suggestions")

class Approval(Base):
    __tablename__ = "approvals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action_type = Column(SQLEnum(SystemActionType), nullable=False, index=True)
    payload_json = Column(JSON, nullable=False)
    risk = Column(SQLEnum(RiskLevel), nullable=False, default=RiskLevel.MEDIUM)
    status = Column(SQLEnum(ApprovalStatus), nullable=False, default=ApprovalStatus.PENDING, index=True)
    
    # Approval metadata
    reviewer_whitelist = Column(ARRAY(String))
    slack_channel = Column(String(50))
    slack_ts = Column(String(50))
    slack_message_url = Column(Text)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    decided_at = Column(DateTime(timezone=True))
    decided_by = Column(String(100))
    reason = Column(Text)
    
    # Execution tracking
    executed_at = Column(DateTime(timezone=True))
    execution_result = Column(JSON)
    execution_error = Column(Text)
    
    # Tracing
    langfuse_trace_id = Column(String(255), index=True)
    related_entity_id = Column(UUID(as_uuid=True))  # Can reference review, ticket, etc.
    
    __table_args__ = (
        Index('idx_approvals_status_created', 'status', 'created_at'),
        Index('idx_approvals_risk_status', 'risk', 'status'),
    )

class GuardrailLog(Base):
    __tablename__ = "guardrail_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    approval_id = Column(UUID(as_uuid=True), ForeignKey("approvals.id", ondelete="CASCADE"))
    check_type = Column(String(50))  # "hard" or "soft"
    rule_name = Column(String(100))
    passed = Column(Boolean, nullable=False)
    details = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_guardrail_logs_approval_passed', 'approval_id', 'passed'),
    )

class IssueSearchSession(Base):
    """Stores YouTrack issue search sessions for duplicate detection"""
    __tablename__ = "issue_search_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    review_id = Column(UUID(as_uuid=True), ForeignKey("reviews.id", ondelete="CASCADE"))
    project = Column(String(100), nullable=False)
    bug_report_text = Column(Text, nullable=False)
    
    # Configuration
    max_candidates_to_analyze = Column(Integer, default=10)
    similarity_threshold = Column(Float, default=0.75)
    
    # Final results
    duplicate_found = Column(Boolean, default=False)
    selected_duplicate_issue_id = Column(String(50))
    final_action = Column(String(50))  # created_issue, commented_on_duplicate, error
    
    # Metrics
    total_api_calls = Column(Integer, default=0)
    total_processing_time_ms = Column(Integer)
    total_candidates_found = Column(Integer, default=0)
    candidates_analyzed_in_detail = Column(Integer, default=0)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    review = relationship("Review")
    search_queries = relationship("IssueSearchQuery", back_populates="session", cascade="all, delete-orphan")
    candidate_issues = relationship("IssueDuplicateCandidate", back_populates="session", cascade="all, delete-orphan")
    stage_progress = relationship("IssueSearchProgress", back_populates="session", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_dup_sessions_review_started', 'review_id', 'started_at'),
        Index('idx_dup_sessions_project_completed', 'project', 'completed_at'),
    )

class IssueSearchQuery(Base):
    """Individual YouTrack issue search queries for duplicate detection"""
    __tablename__ = "issue_search_queries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("issue_search_sessions.id", ondelete="CASCADE"))
    
    query = Column(Text, nullable=False)
    search_type = Column(String(50))  # keywords, error, component, recent
    results_count = Column(Integer, default=0)
    execution_time_ms = Column(Integer)
    executed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("IssueSearchSession", back_populates="search_queries")
    
    __table_args__ = (
        Index('idx_dup_queries_session_executed', 'session_id', 'executed_at'),
    )

class IssueDuplicateCandidate(Base):
    """Potential duplicate YouTrack issues found during search"""
    __tablename__ = "issue_duplicate_candidates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("issue_search_sessions.id", ondelete="CASCADE"))
    
    issue_id = Column(String(50), nullable=False)
    title = Column(Text)
    description = Column(Text)
    created_date = Column(DateTime(timezone=True))
    
    # Pre-filtering scores (Stage 2)
    title_similarity_score = Column(Float)
    keyword_overlap_score = Column(Float)
    recency_score = Column(Float)
    pre_filter_score = Column(Float)
    
    # Detailed analysis (Stage 3)
    detailed_analysis_completed = Column(Boolean, default=False)
    semantic_similarity_score = Column(Float)
    problem_similarity_score = Column(Float)
    context_similarity_score = Column(Float)
    impact_similarity_score = Column(Float)
    final_similarity_score = Column(Float)
    duplicate_confidence = Column(Float)
    
    analysis_notes = Column(Text)
    selected_as_duplicate = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    analyzed_at = Column(DateTime(timezone=True))
    
    # Relationships
    session = relationship("IssueSearchSession", back_populates="candidate_issues")
    
    __table_args__ = (
        Index('idx_dup_candidates_session_score', 'session_id', 'final_similarity_score'),
        Index('idx_dup_candidates_selected', 'session_id', 'selected_as_duplicate'),
    )

class IssueSearchProgress(Base):
    """Progress tracking for each stage of issue search workflow"""
    __tablename__ = "issue_search_progress"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("issue_search_sessions.id", ondelete="CASCADE"))
    
    stage = Column(SQLEnum(IssueSearchStage), nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    success = Column(Boolean)
    error_message = Column(Text)
    
    # Stage-specific metrics
    items_processed = Column(Integer, default=0)
    items_remaining = Column(Integer, default=0)
    stage_metadata = Column(JSON, default={})
    
    # Relationships
    session = relationship("IssueSearchSession", back_populates="stage_progress")
    
    __table_args__ = (
        Index('idx_dup_stages_session_stage', 'session_id', 'stage'),
        Index('idx_dup_stages_started', 'started_at'),
    )


# ============================================================================
# FEATURE RESEARCH MODELS
# ============================================================================

class FeatureResearchSession(Base):
    """Main session for feature research workflow"""
    __tablename__ = "feature_research_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    review_id = Column(UUID(as_uuid=True), ForeignKey("reviews.id", ondelete="CASCADE"))
    feature_description = Column(Text, nullable=False)
    project = Column(String(100), nullable=False)
    
    # Research configuration
    competitors_list = Column(ARRAY(String), nullable=False)
    max_search_queries = Column(Integer, default=10)
    require_citations = Column(Boolean, default=True)
    
    # Workflow status
    status = Column(String(50), nullable=False, default="pending")  # pending, completed, failed
    current_stage = Column(String(50))  # planning, research, analysis, specification
    
    # Results summary
    total_competitors_analyzed = Column(Integer, default=0)
    total_evidence_urls = Column(Integer, default=0)
    research_quality_score = Column(Float)
    
    # Final deliverables
    feature_spec_json = Column(JSON)
    competitor_matrix_json = Column(JSON)
    final_report_json = Column(JSON)
    
    # Approval workflow
    requires_pm_approval = Column(Boolean, default=True)
    approval_status = Column(String(50), default="pending")  # pending, approved, rejected
    approved_by = Column(String(100))
    approved_at = Column(DateTime(timezone=True))
    
    # Metrics
    processing_time_ms = Column(Integer)
    agent_turns_used = Column(Integer, default=0)
    web_searches_performed = Column(Integer, default=0)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Tracing
    langfuse_trace_id = Column(String(255), index=True)
    
    # Relationships
    review = relationship("Review")
    findings = relationship("WebResearchFinding", back_populates="session", cascade="all, delete-orphan")
    queries = relationship("WebSearchQuery", back_populates="session", cascade="all, delete-orphan")
    analyses = relationship("CompetitorAnalysis", back_populates="session", cascade="all, delete-orphan")
    stage_progress = relationship("FeatureResearchProgress", back_populates="session", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_feature_sessions_review_started', 'review_id', 'started_at'),
        Index('idx_feature_sessions_status', 'status'),
        Index('idx_feature_sessions_project_completed', 'project', 'completed_at'),
        Index('idx_feature_sessions_approval_status', 'approval_status'),
    )


class WebResearchFinding(Base):
    """Individual web research findings about competitors"""
    __tablename__ = "web_research_findings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("feature_research_sessions.id", ondelete="CASCADE"))
    
    # Finding details
    competitor = Column(String(100), nullable=False)
    feature = Column(String(255), nullable=False)
    claim = Column(Text, nullable=False)
    evidence_url = Column(Text, nullable=False)
    evidence_snippet = Column(Text, nullable=False)
    
    # Quality assessment
    confidence = Column(SQLEnum(ResearchConfidence), nullable=False)
    is_official_source = Column(Boolean, default=False)
    date_found = Column(String(50))
    
    # Search context
    search_query_used = Column(Text)
    found_by_agent = Column(String(100))  # which sub-agent found this
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("FeatureResearchSession", back_populates="findings")
    
    __table_args__ = (
        Index('idx_feature_findings_session_competitor', 'session_id', 'competitor'),
        Index('idx_feature_findings_confidence', 'confidence'),
        Index('idx_feature_findings_official', 'is_official_source'),
    )


class WebSearchQuery(Base):
    """Web search queries executed during feature research"""
    __tablename__ = "web_search_queries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("feature_research_sessions.id", ondelete="CASCADE"))
    
    # Query details
    query = Column(Text, nullable=False)
    search_type = Column(String(50))  # competitor_search, feature_comparison, etc.
    target_competitor = Column(String(100))
    executed_by_agent = Column(String(100))
    
    # Results
    results_count = Column(Integer, default=0)
    findings_extracted = Column(Integer, default=0)
    execution_time_ms = Column(Integer)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    
    executed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("FeatureResearchSession", back_populates="queries")
    
    __table_args__ = (
        Index('idx_feature_queries_session_executed', 'session_id', 'executed_at'),
        Index('idx_feature_queries_success', 'success'),
    )


class CompetitorAnalysis(Base):
    """Competitor analysis results for specific features"""
    __tablename__ = "competitor_analysis"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("feature_research_sessions.id", ondelete="CASCADE"))
    
    # Competitor details
    competitor = Column(String(100), nullable=False)
    feature = Column(String(255), nullable=False)
    has_feature = Column(Boolean, nullable=False)
    
    # Implementation details
    implementation_details = Column(Text)
    pricing_tier = Column(String(100))
    limitations = Column(ARRAY(String))
    strengths = Column(ARRAY(String))
    last_updated = Column(String(50))
    
    # Supporting evidence
    proof_urls = Column(ARRAY(String), nullable=False)
    analysis_notes = Column(Text)
    confidence_score = Column(Float)
    
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("FeatureResearchSession", back_populates="analyses")
    
    __table_args__ = (
        Index('idx_feature_analysis_session_competitor', 'session_id', 'competitor'),
        Index('idx_feature_analysis_has_feature', 'has_feature'),
        UniqueConstraint('session_id', 'competitor', 'feature', name='uq_session_competitor_feature'),
    )


class FeatureResearchProgress(Base):
    """Progress tracking for feature research workflow stages"""
    __tablename__ = "feature_research_progress"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("feature_research_sessions.id", ondelete="CASCADE"))
    
    # Stage details
    stage = Column(SQLEnum(FeatureResearchStage), nullable=False)
    agent_name = Column(String(100), nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Status
    success = Column(Boolean)
    error_message = Column(Text)
    
    # Stage metrics
    items_processed = Column(Integer, default=0)
    output_size_tokens = Column(Integer)
    stage_metadata = Column(JSON, default={})
    
    # Relationships
    session = relationship("FeatureResearchSession", back_populates="stage_progress")
    
    __table_args__ = (
        Index('idx_feature_stages_session_stage', 'session_id', 'stage'),
        Index('idx_feature_stages_started', 'started_at'),
    )