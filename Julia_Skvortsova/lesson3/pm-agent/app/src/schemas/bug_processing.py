"""
Pydantic schemas for bug processing structured output
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

# Import centralized constants
from src.constants import BugProcessingOutcome, BugPriorityLevel, ApprovalStatus

class DuplicateAnalysisResult(BaseModel):
    """Schema for duplicate detection analysis"""
    is_duplicate: bool = Field(description="Whether the bug report is a duplicate of an existing issue")
    duplicate_issue_id: Optional[str] = Field(default=None, description="ID of the duplicate issue if found")
    similarity_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Similarity score between 0.0 and 1.0")
    reasoning: str = Field(description="Detailed explanation of why this is or isn't a duplicate")
    similar_issues: List[str] = Field(default_factory=list, description="List of similar issue IDs for reference")

class IssueCreationData(BaseModel):
    """Schema for structured issue creation"""
    summary: str = Field(description="Clear, concise issue title")
    description: str = Field(description="Detailed issue description with steps to reproduce")
    priority: BugPriorityLevel = Field(default=BugPriorityLevel.NORMAL, description="Issue priority level")
    tags: List[str] = Field(default_factory=list, description="List of relevant tags for the issue")
    component: Optional[str] = Field(default=None, description="Component or feature area affected")

class DuplicateCommentData(BaseModel):
    """Schema for duplicate comment formatting"""
    comment_text: str = Field(description="Formatted comment text for the duplicate issue")
    impact_assessment: str = Field(description="Assessment of how this duplicate affects the original issue")
    recommendations: List[str] = Field(default_factory=list, description="List of recommendations based on the duplicate report")

class BugProcessingResult(BaseModel):
    """Schema for bug processing workflow results"""
    action: BugProcessingOutcome = Field(description="The action taken for this bug report")
    issue_id: Optional[str] = Field(default=None, description="YouTrack issue ID (e.g., 'DEMO-123')")
    url: Optional[str] = Field(default=None, description="Direct URL to the issue in YouTrack")
    summary: str = Field(description="Brief summary of what was done")
    
    # For new issues
    issue_data: Optional[IssueCreationData] = Field(default=None, description="Data used to create new issue")
    
    # For duplicates
    duplicate_analysis: Optional[DuplicateAnalysisResult] = Field(default=None, description="Duplicate detection analysis")
    duplicate_of: Optional[str] = Field(default=None, description="Original issue ID if this is a duplicate")
    comment_data: Optional[DuplicateCommentData] = Field(default=None, description="Comment added to duplicate issue")
    
    # Staged duplicate analysis tracking
    duplicate_session_id: Optional[str] = Field(default=None, description="ID of the duplicate analysis session for detailed tracking")
    total_candidates_found: Optional[int] = Field(default=None, description="Total number of duplicate candidates found")
    candidates_analyzed_in_detail: Optional[int] = Field(default=None, description="Number of candidates that received detailed analysis")
    
    # Approval tracking
    approval_status: ApprovalStatus = Field(default=ApprovalStatus.NOT_REQUIRED, description="Status of approval if required")
    approval_id: Optional[str] = Field(default=None, description="ID of the approval request if created")
    uncertainty_reason: Optional[str] = Field(default=None, description="Reason why approval was required")
    approval_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Confidence score that triggered approval")
    
    # Error handling
    error_message: Optional[str] = Field(default=None, description="Error message if action failed")
    
    # Metadata
    search_queries_used: List[str] = Field(default_factory=list, description="Search queries used to find duplicates")
    issues_examined: List[str] = Field(default_factory=list, description="List of issue IDs examined for duplicates")
    processing_time_ms: Optional[int] = Field(default=None, description="Total processing time in milliseconds")
    api_calls_made: Optional[int] = Field(default=None, description="Number of API calls made during processing")

class BugAnalysisWorkflow(BaseModel):
    """Schema for the complete bug analysis workflow"""
    review_id: str = Field(description="Original review ID being processed")
    extracted_keywords: List[str] = Field(description="Keywords extracted from the review for searching")
    error_patterns: List[str] = Field(default_factory=list, description="Error patterns or symptoms identified")
    affected_components: List[str] = Field(default_factory=list, description="Components or features that appear to be affected")
    search_strategy: str = Field(description="Description of the search strategy used")
    result: BugProcessingResult = Field(description="Final processing result")

def get_bug_processing_schema() -> dict:
    """Get the JSON schema for bug processing result"""
    return BugProcessingResult.model_json_schema()

def get_duplicate_analysis_schema() -> dict:
    """Get the JSON schema for duplicate analysis"""
    return DuplicateAnalysisResult.model_json_schema()

def get_bug_workflow_schema() -> dict:
    """Get the JSON schema for complete bug workflow"""
    return BugAnalysisWorkflow.model_json_schema()