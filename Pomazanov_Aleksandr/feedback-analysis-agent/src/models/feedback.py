from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class FeedbackCategory(str, Enum):
    FUNCTIONALITY = "functionality"
    UX_UI = "ux_ui"
    PERFORMANCE = "performance"
    BUGS = "bugs"
    FEATURE_REQUEST = "feature_request"
    GENERAL = "general"


class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FeedbackItem(BaseModel):
    id: Optional[str] = None
    text: str = Field(..., description="Original feedback text")
    source: Optional[str] = Field(None, description="Source of feedback (file, platform, etc.)")
    timestamp: Optional[datetime] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AnalysisResult(BaseModel):
    feedback_item: FeedbackItem
    category: FeedbackCategory
    sentiment: Sentiment
    priority: Priority
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    key_phrases: List[str] = Field(default_factory=list)
    summary: str = Field(..., description="Brief summary of the feedback")
    actionable_items: List[str] = Field(default_factory=list)


class CategoryInsight(BaseModel):
    category: FeedbackCategory
    total_count: int
    sentiment_distribution: Dict[Sentiment, int]
    priority_distribution: Dict[Priority, int]
    top_issues: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class InsightReport(BaseModel):
    generated_at: datetime = Field(default_factory=datetime.now)
    total_feedback_items: int
    category_insights: List[CategoryInsight]
    overall_sentiment: Dict[Sentiment, float]
    high_priority_items: List[AnalysisResult]
    key_themes: List[str] = Field(default_factory=list)
    executive_summary: str = ""