"""
Pydantic schemas for review classification structured output
"""
from typing import List, Literal
from pydantic import BaseModel, Field

from src.constants import ReviewCategory

class SingleReviewClassification(BaseModel):
    """Schema for a single classified review"""
    id: str = Field(description="Unique identifier for the review")
    text: str = Field(description="The original review text")
    category: ReviewCategory = Field(description="Classification category: BUG, FEATURE, or OTHER")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    reasoning: str = Field(description="Brief explanation for the classification based on keywords and context")

class ReviewClassificationBatch(BaseModel):
    """Schema for batch review classification results"""
    reviews: List[SingleReviewClassification] = Field(description="List of classified reviews")
    summary: 'ClassificationSummary' = Field(description="Summary statistics of the classification")

class ClassificationSummary(BaseModel):
    """Summary statistics for a classification batch"""
    total_reviews: int = Field(description="Total number of reviews processed")
    bug_count: int = Field(description="Number of bug reports identified")
    feature_count: int = Field(description="Number of feature requests identified") 
    other_count: int = Field(description="Number of other/general feedback items")
    average_confidence: float = Field(ge=0.0, le=1.0, description="Average confidence across all classifications")

# Update forward reference
ReviewClassificationBatch.model_rebuild()

def get_classification_schema() -> dict:
    """Get the JSON schema for single review classification"""
    return SingleReviewClassification.model_json_schema()

def get_batch_classification_schema() -> dict:
    """Get the JSON schema for batch review classification"""
    return ReviewClassificationBatch.model_json_schema()