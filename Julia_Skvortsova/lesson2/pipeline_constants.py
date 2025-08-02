"""Constants for the pipeline agents system"""
from enum import Enum


class PipelineAgentType(Enum):
    """Pipeline agent type constants"""
    REVIEW_SUMMARIZER = "review_summarizer"
    FEATURE_EXTRACTOR = "feature_extractor"
    PERSONA_EXTRACTOR = "persona_extractor"
    PERSONA_MATCHER = "persona_matcher"
    RICE_ANALYST = "rice_analyst"
    PRODUCT_CONCEPTOR = "product_conceptor"
    MARKET_RESEARCHER = "market_researcher"
    RESEARCH_DESIGNER = "research_designer"


class PipelineStep(Enum):
    """Pipeline step constants for logging and tracking"""
    LOAD_REVIEWS = "load_reviews"
    SUMMARIZE_REVIEWS = "summarize_reviews"
    EXTRACT_FEATURES = "extract_features"
    EXTRACT_PERSONAS = "extract_personas"
    MATCH_PERSONAS = "match_personas"
    SCORE_FEATURES = "score_features"
    GENERATE_CONCEPT = "generate_concept"
    GENERATE_RESEARCH = "generate_research"
    DESIGN_QUESTIONS = "design_questions"
    GENERATE_CONFIG = "generate_config"
    RUN_VIRTUAL_BOARD = "run_virtual_board"