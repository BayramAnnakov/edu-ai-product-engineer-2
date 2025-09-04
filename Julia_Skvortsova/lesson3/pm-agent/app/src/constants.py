"""
Centralized constants and enums for PM Agent

This module contains all enum definitions used across the application
to avoid duplication and ensure consistency.

"""
import enum


# ============================================================================
# REVIEW AND CLASSIFICATION ENUMS
# ============================================================================

class ReviewCategory(enum.Enum):
    """Review classification categories"""
    BUG = "bug"
    FEATURE = "feature"
    OTHER = "other"


# ============================================================================
# APPROVAL AND WORKFLOW ENUMS
# ============================================================================

class ApprovalStatus(enum.Enum):
    """Status of approval requests and workflows"""
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"
    EXECUTED = "executed"
    EXPIRED = "expired"


class RiskLevel(enum.Enum):
    """Risk assessment levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SystemActionType(enum.Enum):
    """Types of system actions that can be executed"""
    CREATE_YOUTRACK_ISSUE = "create_youtrack_issue"
    ADD_YOUTRACK_COMMENT = "add_youtrack_comment"
    POST_SLACK = "post_slack"
    CREATE_PR = "create_pr"
    SEARCH_CODE = "search_code"


# ============================================================================
# ISSUE SEARCH ENUMS
# ============================================================================

class IssueSearchStage(enum.Enum):
    """Stages of the YouTrack issue search process"""
    MULTI_QUERY_SEARCH = "multi_query_search"
    PRE_FILTERING = "pre_filtering"
    DETAILED_ANALYSIS = "detailed_analysis"
    FINAL_DECISION = "final_decision"


class SimilarityType(enum.Enum):
    """Types of similarity analysis for issue duplicate detection"""
    TITLE_SIMILARITY = "title_similarity"
    DESCRIPTION_SIMILARITY = "description_similarity"
    KEYWORD_OVERLAP = "keyword_overlap"
    SEMANTIC_SIMILARITY = "semantic_similarity"
    TEMPORAL_PROXIMITY = "temporal_proximity"


# ============================================================================
# FEATURE RESEARCH ENUMS
# ============================================================================

class FeatureResearchStage(enum.Enum):
    """Stages of the feature research workflow"""
    PLANNING = "planning"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    SPECIFICATION = "specification"


class ResearchConfidence(enum.Enum):
    """Confidence levels for research findings"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SearchType(enum.Enum):
    """Types of searches performed during feature research"""
    COMPETITOR_SEARCH = "competitor_search"
    FEATURE_COMPARISON = "feature_comparison"
    OFFICIAL_DOCS = "official_docs"
    PRICING_INFO = "pricing_info"
    USER_REVIEWS = "user_reviews"


class FeaturePriority(enum.Enum):
    """Priority levels for features"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================================
# BUG PROCESSING ENUMS
# ============================================================================

class BugProcessingOutcome(enum.Enum):
    """Possible outcomes of bug processing workflow"""
    CREATED_ISSUE = "created_issue"
    COMMENTED_ON_DUPLICATE = "commented_on_duplicate"
    SKIPPED = "skipped"
    ERROR = "error"


class BugPriorityLevel(enum.Enum):
    """Priority levels for bugs"""
    CRITICAL = "Critical"
    MAJOR = "Major"
    NORMAL = "Normal"
    MINOR = "Minor"


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_enum_values(enum_class: type[enum.Enum]) -> list[str]:
    """Get all values from an enum as a list of strings"""
    return [member.value for member in enum_class]


def get_enum_names(enum_class: type[enum.Enum]) -> list[str]:
    """Get all names from an enum as a list of strings"""
    return [member.name for member in enum_class]


def validate_enum_value(enum_class: type[enum.Enum], value: str) -> bool:
    """Check if a value is valid for the given enum"""
    return value in get_enum_values(enum_class)


# ============================================================================
# CONSTANTS FOR CONVENIENCE
# ============================================================================

# Review categories
REVIEW_CATEGORIES = get_enum_values(ReviewCategory)

# Risk levels
RISK_LEVELS = get_enum_values(RiskLevel)

# Approval statuses
APPROVAL_STATUSES = get_enum_values(ApprovalStatus)

# Feature research stages
FEATURE_RESEARCH_STAGES = get_enum_values(FeatureResearchStage)

# Issue search stages
ISSUE_SEARCH_STAGES = get_enum_values(IssueSearchStage)

# Research confidence levels
RESEARCH_CONFIDENCE_LEVELS = get_enum_values(ResearchConfidence)

# Bug processing outcomes
BUG_PROCESSING_OUTCOMES = get_enum_values(BugProcessingOutcome)

# System action types
SYSTEM_ACTION_TYPES = get_enum_values(SystemActionType)