"""
Pydantic schemas for structured output
"""
from .review_classification import (
    SingleReviewClassification,
    ReviewClassificationBatch, 
    ClassificationSummary,
    get_classification_schema,
    get_batch_classification_schema,
)

from .bug_processing import (
    BugProcessingResult,
    DuplicateAnalysisResult,
    IssueCreationData,
    DuplicateCommentData,
    BugAnalysisWorkflow,
    BugProcessingOutcome,
    BugPriorityLevel,
    ApprovalStatus,
    get_bug_processing_schema,
    get_duplicate_analysis_schema,
    get_bug_workflow_schema
)

from .issue_search import (
    IssueSearchSession,
    CandidateIssue,
    SearchQuery,
    StageProgress,
    IssueSearchStage,
    SimilarityType,
    DuplicateSearchConfig,
    SearchStrategy,
    get_issue_search_session_schema_formatted,
    create_default_search_config,
    create_default_search_strategy
)

from .bug_submission_assessment import (
    BugSubmissionAssessment,
    get_bug_submission_assessment_schema_formatted
)

from .feature_research import (
    CompetitorResearchTask,
    FeatureResearchPlan,
    WebSearchResult,
    CompetitorFinding,
    CompetitorFeatureAnalysis,
    FeatureComparisonMatrix,
    FeatureSpecification,
    CompetitorResearchReport,
    ResearchQualityMetrics,
    get_feature_research_plan_schema_formatted,
    get_competitor_finding_schema_formatted,
    get_feature_comparison_matrix_schema_formatted,
    get_competitor_research_report_schema_formatted,
    validate_research_quality
)

def format_schema_for_prompt(schema_dict: dict) -> str:
    """Format a JSON schema for inclusion in prompts"""
    import json
    return json.dumps(schema_dict, indent=2)

# Helper functions for easy schema injection into prompts
def get_single_review_schema_formatted() -> str:
    """Get formatted single review classification schema for prompts"""
    return format_schema_for_prompt(get_classification_schema())

def get_batch_review_schema_formatted() -> str:
    """Get formatted batch review classification schema for prompts"""
    return format_schema_for_prompt(get_batch_classification_schema())

def get_bug_processing_schema_formatted() -> str:
    """Get formatted bug processing schema for prompts"""
    return format_schema_for_prompt(get_bug_processing_schema())

def get_duplicate_analysis_schema_formatted() -> str:
    """Get formatted duplicate analysis schema for prompts"""
    return format_schema_for_prompt(get_duplicate_analysis_schema())

def get_bug_workflow_schema_formatted() -> str:
    """Get formatted bug workflow schema for prompts"""
    return format_schema_for_prompt(get_bug_workflow_schema())

def get_duplicate_session_schema_formatted() -> str:
    """Get formatted duplicate analysis session schema for prompts"""
    return get_issue_search_session_schema_formatted()

def get_bug_submission_schema_formatted() -> str:
    """Get formatted bug submission assessment schema for prompts"""
    return format_schema_for_prompt(get_bug_submission_assessment_schema_formatted())

__all__ = [
    # Review classification schemas
    'SingleReviewClassification',
    'ReviewClassificationBatch',
    'ClassificationSummary', 
    'get_classification_schema',
    'get_batch_classification_schema',
    
    # Bug processing schemas
    'BugProcessingResult',
    'DuplicateAnalysisResult', 
    'IssueCreationData',
    'DuplicateCommentData',
    'BugAnalysisWorkflow',
    'BugProcessingOutcome',
    'BugPriorityLevel',
    'ApprovalStatus',
    'get_bug_processing_schema',
    'get_duplicate_analysis_schema',
    'get_bug_workflow_schema',
    
    # Issue search schemas
    'IssueSearchSession',
    'CandidateIssue',
    'SearchQuery',
    'StageProgress',
    'IssueSearchStage',
    'SimilarityType',
    'DuplicateSearchConfig',
    'SearchStrategy',
    'create_default_search_config',
    'create_default_search_strategy',
    
    # Bug submission assessment schemas
    'BugSubmissionAssessment',
    'get_bug_submission_assessment_schema_formatted',
    
    # Feature research schemas
    'CompetitorResearchTask',
    'FeatureResearchPlan',
    'WebSearchResult',
    'CompetitorFinding',
    'CompetitorFeatureAnalysis',
    'FeatureComparisonMatrix',
    'FeatureSpecification',
    'CompetitorResearchReport',
    'ResearchQualityMetrics',
    'get_feature_research_plan_schema_formatted',
    'get_competitor_finding_schema_formatted',
    'get_feature_comparison_matrix_schema_formatted',
    'get_competitor_research_report_schema_formatted',
    'validate_research_quality',
    
    # Utility functions
    'format_schema_for_prompt',
    'get_single_review_schema_formatted',
    'get_batch_review_schema_formatted',
    'get_bug_processing_schema_formatted',
    'get_duplicate_analysis_schema_formatted',
    'get_bug_workflow_schema_formatted',
    'get_duplicate_session_schema_formatted',
    'get_bug_submission_schema_formatted'
]