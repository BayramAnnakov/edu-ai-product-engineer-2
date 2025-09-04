"""
Schemas for YouTrack issue search with intermediate result tracking
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

# Import centralized constants
from src.constants import IssueSearchStage, SimilarityType

class SearchQuery(BaseModel):
    """Individual search query and its results"""
    query: str = Field(description="YouTrack query string")
    search_type: str = Field(description="Type of search (keywords, error, component)")
    results_count: int = Field(description="Number of results returned")
    execution_time_ms: int = Field(description="Query execution time in milliseconds")

class CandidateIssue(BaseModel):
    """A potential duplicate issue candidate with analysis data"""
    issue_id: str = Field(description="YouTrack issue ID")
    title: str = Field(description="Issue title/summary")
    description: Optional[str] = Field(description="Issue description", default=None)
    created_date: Optional[str] = Field(description="Issue creation date", default=None)
    
    # Pre-filtering scores
    title_similarity_score: Optional[float] = Field(description="Title similarity (0-1)", default=None)
    keyword_overlap_score: Optional[float] = Field(description="Keyword overlap score (0-1)", default=None)
    recency_score: Optional[float] = Field(description="Recency score (0-1)", default=None)
    pre_filter_score: Optional[float] = Field(description="Combined pre-filter score (0-1)", default=None)
    
    # Detailed analysis results
    detailed_analysis_completed: bool = Field(description="Whether detailed analysis was performed", default=False)
    semantic_similarity_score: Optional[float] = Field(description="Deep semantic similarity (0-1)", default=None)
    final_similarity_score: Optional[float] = Field(description="Final weighted similarity score (0-1)", default=None)
    duplicate_confidence: Optional[float] = Field(description="Confidence this is a duplicate (0-1)", default=None)
    
    analysis_notes: Optional[str] = Field(description="Human-readable analysis notes", default=None)

class StageProgress(BaseModel):
    """Progress tracking for each stage of duplicate analysis"""
    stage: IssueSearchStage = Field(description="Current stage")
    started_at: datetime = Field(description="Stage start time")
    completed_at: Optional[datetime] = Field(description="Stage completion time", default=None)
    success: Optional[bool] = Field(description="Whether stage completed successfully", default=None)
    error_message: Optional[str] = Field(description="Error message if stage failed", default=None)
    
    # Stage-specific data
    items_processed: int = Field(description="Number of items processed in this stage", default=0)
    items_remaining: int = Field(description="Number of items remaining", default=0)
    metadata: Dict[str, Any] = Field(description="Stage-specific metadata", default_factory=dict)

class IssueSearchSession(BaseModel):
    """Complete duplicate analysis session with all stages and results"""
    session_id: str = Field(description="Unique session identifier")
    bug_report_text: str = Field(description="Original bug report text")
    project: str = Field(description="YouTrack project")
    
    # Search configuration
    max_candidates_to_analyze: int = Field(description="Maximum candidates for detailed analysis", default=10)
    similarity_threshold: float = Field(description="Threshold for considering duplicate", default=0.75)
    
    # Search queries executed
    search_queries: List[SearchQuery] = Field(description="All search queries executed", default_factory=list)
    
    # All candidates found
    all_candidates: List[CandidateIssue] = Field(description="All potential candidates found", default_factory=list)
    analyzed_candidates: List[CandidateIssue] = Field(description="Candidates that received detailed analysis", default_factory=list)
    
    # Stage tracking
    stages: List[StageProgress] = Field(description="Progress through each stage", default_factory=list)
    
    # Final results
    duplicate_found: bool = Field(description="Whether a duplicate was found", default=False)
    selected_duplicate: Optional[CandidateIssue] = Field(description="The selected duplicate if found", default=None)
    
    # Session metadata
    started_at: datetime = Field(description="Session start time")
    completed_at: Optional[datetime] = Field(description="Session completion time", default=None)
    total_api_calls: int = Field(description="Total API calls made", default=0)
    total_processing_time_ms: int = Field(description="Total processing time in milliseconds", default=0)

class DuplicateSearchConfig(BaseModel):
    """Configuration for duplicate search process"""
    # Search limits
    max_results_per_query: int = Field(description="Max results per individual search query", default=50)
    max_total_candidates: int = Field(description="Max total candidates to consider", default=200)
    max_detailed_analysis: int = Field(description="Max candidates for detailed analysis", default=10)
    
    # Similarity thresholds
    pre_filter_threshold: float = Field(description="Threshold for pre-filtering", default=0.3)
    duplicate_confidence_threshold: float = Field(description="Confidence threshold for duplicate", default=0.75)
    high_confidence_threshold: float = Field(description="High confidence for early termination", default=0.85)
    
    # Time limits
    max_processing_time_seconds: int = Field(description="Maximum total processing time", default=120)
    max_stage_time_seconds: int = Field(description="Maximum time per stage", default=60)
    
    # API rate limiting
    api_call_delay_ms: int = Field(description="Delay between API calls in milliseconds", default=100)
    max_concurrent_requests: int = Field(description="Maximum concurrent API requests", default=5)

class SearchStrategy(BaseModel):
    """Strategy for generating search queries from bug report"""
    extract_keywords: bool = Field(description="Extract keywords from bug text", default=True)
    search_by_error_messages: bool = Field(description="Search for error messages/stack traces", default=True)
    search_by_components: bool = Field(description="Search by identified components", default=True)
    include_recent_bias: bool = Field(description="Bias towards more recent issues", default=True)
    
    # Search query templates
    keyword_query_template: str = Field(
        description="Template for keyword-based queries", 
        default="project: {project} ({keywords})"
    )
    error_query_template: str = Field(
        description="Template for error-based queries",
        default="project: {project} summary: {error_terms}"
    )
    component_query_template: str = Field(
        description="Template for component-based queries",
        default="project: {project} #{component}"
    )

def get_issue_search_session_schema_formatted() -> str:
    """Get formatted schema for issue search session"""
    return IssueSearchSession.model_json_schema()

def create_default_search_config() -> DuplicateSearchConfig:
    """Create default search configuration"""
    return DuplicateSearchConfig()

def create_default_search_strategy() -> SearchStrategy:
    """Create default search strategy"""  
    return SearchStrategy()