import os
import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    import openai
except ImportError:
    openai = None

try:
    import anthropic
except ImportError:
    anthropic = None

from ..models.feedback import (
    FeedbackItem, AnalysisResult, FeedbackCategory, 
    Sentiment, Priority
)


@dataclass
class AnalyzerConfig:
    model_provider: str = "openai"  # "openai" or "anthropic"
    model_name: str = "gpt-4"
    api_key: Optional[str] = None
    max_tokens: int = 1000
    temperature: float = 0.1


class FeedbackAnalyzer:
    """Analyzer for processing feedback using LLM APIs."""
    
    def __init__(self, config: AnalyzerConfig):
        self.config = config
        self._client = None
        self._setup_client()
    
    def _setup_client(self):
        """Setup the LLM client based on configuration."""
        if self.config.model_provider == "openai":
            if not openai:
                raise ImportError("OpenAI library not installed. Run: pip install openai")
            
            api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key not found")
            
            self._client = openai.OpenAI(api_key=api_key)
            
        elif self.config.model_provider == "anthropic":
            if not anthropic:
                raise ImportError("Anthropic library not installed. Run: pip install anthropic")
            
            api_key = self.config.api_key or os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("Anthropic API key not found")
            
            self._client = anthropic.Anthropic(api_key=api_key)
        else:
            raise ValueError(f"Unsupported model provider: {self.config.model_provider}")
    
    def analyze_feedback(self, feedback_item: FeedbackItem) -> AnalysisResult:
        """Analyze a single feedback item using LLM."""
        prompt = self._create_analysis_prompt(feedback_item.text)
        
        try:
            response = self._call_llm(prompt)
            analysis_data = self._parse_llm_response(response)
            
            return AnalysisResult(
                feedback_item=feedback_item,
                category=FeedbackCategory(analysis_data["category"]),
                sentiment=Sentiment(analysis_data["sentiment"]),
                priority=Priority(analysis_data["priority"]),
                confidence_score=analysis_data["confidence_score"],
                key_phrases=analysis_data["key_phrases"],
                summary=analysis_data["summary"],
                actionable_items=analysis_data["actionable_items"]
            )
        except Exception as e:
            # Fallback analysis if LLM fails
            return self._fallback_analysis(feedback_item, str(e))
    
    def analyze_batch(self, feedback_items: List[FeedbackItem]) -> List[AnalysisResult]:
        """Analyze multiple feedback items."""
        results = []
        for item in feedback_items:
            try:
                result = self.analyze_feedback(item)
                results.append(result)
            except Exception as e:
                print(f"Error analyzing feedback item {item.id}: {e}")
                # Add fallback result
                fallback_result = self._fallback_analysis(item, str(e))
                results.append(fallback_result)
        
        return results
    
    def _create_analysis_prompt(self, feedback_text: str) -> str:
        """Create a prompt for analyzing feedback."""
        return f"""
Analyze the following user feedback and provide structured output in JSON format.

Feedback text: "{feedback_text}"

Please analyze this feedback and return a JSON object with the following structure:
{{
    "category": "one of: functionality, ux_ui, performance, bugs, feature_request, general",
    "sentiment": "one of: positive, negative, neutral",
    "priority": "one of: high, medium, low",
    "confidence_score": "float between 0.0 and 1.0",
    "key_phrases": ["list", "of", "important", "phrases"],
    "summary": "brief summary of the feedback in 1-2 sentences",
    "actionable_items": ["list", "of", "specific", "actions", "to", "take"]
}}

Guidelines for analysis:
- Category: Choose the most relevant category based on the main topic
- Sentiment: Determine the overall emotional tone
- Priority: High for critical issues/bugs, Medium for improvements, Low for nice-to-haves
- Key phrases: Extract 3-5 most important words or short phrases
- Summary: Concise explanation of what the user is saying
- Actionable items: Specific steps the product team could take

Return ONLY the JSON object, no additional text.
        """.strip()
    
    def _call_llm(self, prompt: str) -> str:
        """Call the configured LLM with the prompt."""
        if self.config.model_provider == "openai":
            response = self._client.chat.completions.create(
                model=self.config.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing user feedback for product teams. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )
            return response.choices[0].message.content
            
        elif self.config.model_provider == "anthropic":
            response = self._client.messages.create(
                model=self.config.model_name,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse and validate LLM response."""
        try:
            # Clean up response - extract JSON if wrapped in other text
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
            else:
                json_str = response
            
            data = json.loads(json_str)
            
            # Validate required fields
            required_fields = ["category", "sentiment", "priority", "confidence_score", "summary"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate enum values
            valid_categories = [cat.value for cat in FeedbackCategory]
            if data["category"] not in valid_categories:
                data["category"] = "general"
            
            valid_sentiments = [sent.value for sent in Sentiment]
            if data["sentiment"] not in valid_sentiments:
                data["sentiment"] = "neutral"
            
            valid_priorities = [pri.value for pri in Priority]
            if data["priority"] not in valid_priorities:
                data["priority"] = "medium"
            
            # Ensure confidence score is valid
            confidence = float(data["confidence_score"])
            data["confidence_score"] = max(0.0, min(1.0, confidence))
            
            # Ensure lists exist
            data["key_phrases"] = data.get("key_phrases", [])
            data["actionable_items"] = data.get("actionable_items", [])
            
            return data
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            raise ValueError(f"Failed to parse LLM response: {e}")
    
    def _fallback_analysis(self, feedback_item: FeedbackItem, error: str) -> AnalysisResult:
        """Provide basic analysis when LLM fails."""
        text = feedback_item.text.lower()
        
        # Simple keyword-based category detection
        category = FeedbackCategory.GENERAL
        if any(word in text for word in ["bug", "error", "broken", "crash", "fail"]):
            category = FeedbackCategory.BUGS
        elif any(word in text for word in ["slow", "fast", "speed", "performance"]):
            category = FeedbackCategory.PERFORMANCE
        elif any(word in text for word in ["ui", "interface", "design", "layout", "button"]):
            category = FeedbackCategory.UX_UI
        elif any(word in text for word in ["feature", "add", "want", "need", "request"]):
            category = FeedbackCategory.FEATURE_REQUEST
        elif any(word in text for word in ["function", "work", "does", "should"]):
            category = FeedbackCategory.FUNCTIONALITY
        
        # Simple sentiment detection
        sentiment = Sentiment.NEUTRAL
        positive_words = ["good", "great", "love", "like", "awesome", "excellent"]
        negative_words = ["bad", "hate", "terrible", "awful", "horrible", "worst"]
        
        if any(word in text for word in positive_words):
            sentiment = Sentiment.POSITIVE
        elif any(word in text for word in negative_words):
            sentiment = Sentiment.NEGATIVE
        
        # Simple priority detection
        priority = Priority.MEDIUM
        if any(word in text for word in ["urgent", "critical", "important", "crash", "broken"]):
            priority = Priority.HIGH
        elif any(word in text for word in ["minor", "small", "nice", "would be nice"]):
            priority = Priority.LOW
        
        return AnalysisResult(
            feedback_item=feedback_item,
            category=category,
            sentiment=sentiment,
            priority=priority,
            confidence_score=0.5,  # Low confidence for fallback
            key_phrases=[],
            summary=f"Automated analysis failed: {error}. Basic categorization applied.",
            actionable_items=["Review feedback manually", "Check LLM configuration"]
        )