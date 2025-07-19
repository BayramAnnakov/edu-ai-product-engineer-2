from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ReportPayload(BaseModel):
    version: str
    share_percentage: float = Field(..., ge=0, le=100)
    extractive_summary: str
    abstractive_summary: str
    extractive_themes: List[Dict[str, Any]]
    abstractive_themes: List[Dict[str, Any]]
    extractive_theme_distribution: Dict[str, float] = {}
    abstractive_theme_distribution: Dict[str, float] = {}
    rouge_l_extractive: float
    rouge_l_abstractive: float
    latency_ms: float
    cost_usd: float
    mini_summaries: Optional[List[str]] = None
