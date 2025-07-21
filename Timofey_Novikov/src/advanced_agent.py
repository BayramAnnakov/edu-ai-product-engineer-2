"""
Advanced Review Analysis Agent with Tool Calling and Agent Loop
Next evolution of the review analysis system
"""

import time
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import openai
from dotenv import load_dotenv
import os

# Import our existing modules
from analyzers.deterministic import deterministic_analyze
from analyzers.llm_analyzer import llm_analyze
from reports.report_generator import generate_pm_report

load_dotenv()

class AnalysisComplexity(Enum):
    """Complexity levels for review analysis"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"

@dataclass
class QualityMetrics:
    """Quality metrics for analysis results"""
    sentiment_confidence: float
    keyword_relevance: float
    issue_detection_quality: float
    overall_score: float
    needs_refinement: bool

class ToolRegistry:
    """Registry of available analysis tools with OpenAI function calling support"""
    
    def __init__(self):
        self.tools = self._initialize_tools()
    
    def _initialize_tools(self):
        """Initialize tool definitions for OpenAI function calling"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "analyze_sentiment_deterministic",
                    "description": "Fast sentiment analysis using NLTK VADER - returns precise sentiment scores",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string", "description": "Text to analyze for sentiment"}
                        },
                        "required": ["text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "extract_keywords_tfidf",
                    "description": "Extract important keywords using TF-IDF analysis",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string", "description": "Text to extract keywords from"},
                            "max_keywords": {"type": "integer", "description": "Maximum number of keywords to extract", "default": 10}
                        },
                        "required": ["text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "detect_issues_deterministic",
                    "description": "Identify specific issues mentioned in the review using pattern matching",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string", "description": "Text to analyze for issues"}
                        },
                        "required": ["text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "categorize_features",
                    "description": "Categorize mentioned features into predefined categories",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string", "description": "Text to categorize features from"}
                        },
                        "required": ["text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "validate_analysis_quality",
                    "description": "Validate the quality of analysis results and suggest improvements",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "analysis_results": {"type": "string", "description": "JSON string of analysis results to validate"}
                        },
                        "required": ["analysis_results"]
                    }
                }
            }
        ]
    
    def get_tool_function(self, tool_name: str):
        """Get the actual function for a tool"""
        tool_functions = {
            "analyze_sentiment_deterministic": self._analyze_sentiment_deterministic,
            "extract_keywords_tfidf": self._extract_keywords_tfidf,
            "detect_issues_deterministic": self._detect_issues_deterministic,
            "categorize_features": self._categorize_features,
            "validate_analysis_quality": self._validate_analysis_quality
        }
        return tool_functions.get(tool_name)
    
    def _analyze_sentiment_deterministic(self, text: str) -> Dict[str, Any]:
        """Wrapper for deterministic sentiment analysis"""
        results = deterministic_analyze(text)
        return {
            "sentiment": results.get("sentiment", "neutral"),
            "confidence": abs(results.get("sentiment_scores", {}).get("compound", 0)),
            "scores": results.get("sentiment_scores", {}),
            "processing_time": results.get("processing_time", 0)
        }
    
    def _extract_keywords_tfidf(self, text: str, max_keywords: int = 10) -> Dict[str, Any]:
        """Wrapper for keyword extraction"""
        results = deterministic_analyze(text)
        keywords = results.get("keywords", [])[:max_keywords]
        return {
            "keywords": keywords,
            "count": len(keywords),
            "processing_time": results.get("processing_time", 0)
        }
    
    def _detect_issues_deterministic(self, text: str) -> Dict[str, Any]:
        """Wrapper for issue detection"""
        results = deterministic_analyze(text)
        return {
            "issues": results.get("issues_found", []),
            "issue_count": results.get("issue_count", 0),
            "processing_time": results.get("processing_time", 0)
        }
    
    def _categorize_features(self, text: str) -> Dict[str, Any]:
        """Wrapper for feature categorization"""
        results = deterministic_analyze(text)
        return {
            "categories": results.get("feature_categories", {}),
            "top_features": results.get("top_features", []),
            "processing_time": results.get("processing_time", 0)
        }
    
    def _validate_analysis_quality(self, analysis_results: str) -> Dict[str, Any]:
        """Validate analysis quality and suggest improvements"""
        try:
            results = json.loads(analysis_results)
            
            # Calculate quality metrics
            sentiment_conf = results.get("sentiment_confidence", 0)
            keyword_count = len(results.get("keywords", []))
            issue_count = results.get("issue_count", 0)
            
            # Quality scoring
            quality_score = (sentiment_conf + min(keyword_count/10, 1.0) + min(issue_count/5, 1.0)) / 3
            
            return {
                "quality_score": quality_score,
                "needs_refinement": quality_score < 0.7,
                "suggestions": self._generate_quality_suggestions(results, quality_score)
            }
        except Exception as e:
            return {
                "quality_score": 0.0,
                "needs_refinement": True,
                "suggestions": [f"Error validating results: {e}"]
            }
    
    def _generate_quality_suggestions(self, results: Dict[str, Any], quality_score: float) -> List[str]:
        """Generate suggestions for quality improvement"""
        suggestions = []
        
        if quality_score < 0.5:
            suggestions.append("Consider using LLM analysis for better insights")
        
        if len(results.get("keywords", [])) < 3:
            suggestions.append("Need more comprehensive keyword extraction")
        
        if results.get("issue_count", 0) == 0 and "negative" in str(results.get("sentiment", "")):
            suggestions.append("Negative sentiment detected but no issues found - review issue detection")
        
        return suggestions


class QualityController:
    """Controls and validates analysis quality"""
    
    def __init__(self):
        self.quality_thresholds = {
            "sentiment_confidence": 0.7,
            "keyword_relevance": 0.6,
            "issue_detection": 0.8,
            "overall_minimum": 0.7
        }
    
    def assess_quality(self, analysis_results: Dict[str, Any]) -> QualityMetrics:
        """Assess the quality of analysis results"""
        
        # Calculate sentiment confidence
        sentiment_conf = self._calculate_sentiment_confidence(analysis_results)
        
        # Calculate keyword relevance
        keyword_rel = self._calculate_keyword_relevance(analysis_results)
        
        # Calculate issue detection quality
        issue_quality = self._calculate_issue_detection_quality(analysis_results)
        
        # Overall score
        overall_score = (sentiment_conf + keyword_rel + issue_quality) / 3
        
        # Determine if refinement is needed
        needs_refinement = overall_score < self.quality_thresholds["overall_minimum"]
        
        return QualityMetrics(
            sentiment_confidence=sentiment_conf,
            keyword_relevance=keyword_rel,
            issue_detection_quality=issue_quality,
            overall_score=overall_score,
            needs_refinement=needs_refinement
        )
    
    def _calculate_sentiment_confidence(self, results: Dict[str, Any]) -> float:
        """Calculate sentiment confidence score"""
        det_results = results.get("deterministic_results", {})
        sentiment_scores = det_results.get("sentiment_scores", {})
        compound_score = abs(sentiment_scores.get("compound", 0))
        return min(compound_score * 1.5, 1.0)  # Normalize to 0-1
    
    def _calculate_keyword_relevance(self, results: Dict[str, Any]) -> float:
        """Calculate keyword relevance score"""
        det_results = results.get("deterministic_results", {})
        keywords = det_results.get("keywords", [])
        
        if not keywords:
            return 0.0
        
        # Score based on number and quality of keywords
        keyword_count = len(keywords)
        avg_score = sum(kw.get("score", 0) for kw in keywords) / keyword_count
        
        return min((keyword_count / 10) * avg_score, 1.0)
    
    def _calculate_issue_detection_quality(self, results: Dict[str, Any]) -> float:
        """Calculate issue detection quality score"""
        det_results = results.get("deterministic_results", {})
        sentiment = det_results.get("sentiment", "neutral")
        issue_count = det_results.get("issue_count", 0)
        
        # If sentiment is negative, we expect to find issues
        if sentiment == "negative":
            return min(issue_count / 3, 1.0)
        elif sentiment == "positive":
            return 1.0 if issue_count == 0 else 0.8
        else:  # neutral
            return 0.8
    
    def generate_improvement_suggestions(self, quality_metrics: QualityMetrics) -> List[str]:
        """Generate suggestions for improving analysis quality"""
        suggestions = []
        
        if quality_metrics.sentiment_confidence < 0.7:
            suggestions.append("Use LLM analysis for more nuanced sentiment understanding")
        
        if quality_metrics.keyword_relevance < 0.6:
            suggestions.append("Apply advanced keyword extraction techniques")
        
        if quality_metrics.issue_detection_quality < 0.8:
            suggestions.append("Enhance issue detection with contextual analysis")
        
        return suggestions


class AdvancedReviewAgent:
    """Advanced agent with tool calling and quality control loop"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.tool_registry = ToolRegistry()
        self.quality_controller = QualityController()
        self.max_iterations = 3
        self.model = os.getenv("OPENAI_MODEL", "gpt-4")
        
        print("🤖 Advanced Review Agent initialized")
        print(f"📋 Available tools: {len(self.tool_registry.tools)}")
        print(f"🔄 Max iterations: {self.max_iterations}")
    
    def analyze_review_with_loop(self, review_text: str) -> Dict[str, Any]:
        """
        Analyze review with quality control loop and tool calling
        """
        print(f"\n🔍 Starting advanced analysis for review ({len(review_text)} characters)")
        
        start_time = time.time()
        iteration = 0
        analysis_history = []
        
        # Initial complexity assessment
        complexity = self._assess_complexity(review_text)
        print(f"📊 Complexity assessment: {complexity.value}")
        
        # Select initial tools based on complexity
        selected_tools = self._select_tools_for_complexity(complexity)
        print(f"🛠️  Selected tools: {[tool['function']['name'] for tool in selected_tools]}")
        
        current_results = None
        
        while iteration < self.max_iterations:
            print(f"\n🔄 Iteration {iteration + 1}/{self.max_iterations}")
            
            # Perform analysis with selected tools
            current_results = self._perform_tool_calling_analysis(review_text, selected_tools)
            
            # Assess quality
            quality_metrics = self.quality_controller.assess_quality(current_results)
            print(f"📈 Quality score: {quality_metrics.overall_score:.3f}")
            
            # Store iteration results
            analysis_history.append({
                "iteration": iteration + 1,
                "quality_score": quality_metrics.overall_score,
                "tools_used": [tool['function']['name'] for tool in selected_tools],
                "results": current_results
            })
            
            # Check if quality is acceptable
            if not quality_metrics.needs_refinement:
                print("✅ Quality threshold reached!")
                break
            
            # Generate improvement suggestions
            suggestions = self.quality_controller.generate_improvement_suggestions(quality_metrics)
            print(f"💡 Improvement suggestions: {suggestions}")
            
            # Apply improvements (select different/additional tools)
            selected_tools = self._apply_improvements(selected_tools, suggestions, complexity)
            
            iteration += 1
        
        # Final results
        total_time = time.time() - start_time
        
        final_results = {
            "review_text": review_text,
            "complexity": complexity.value,
            "total_iterations": iteration + 1,
            "final_results": current_results,
            "analysis_history": analysis_history,
            "performance": {
                "total_time": round(total_time, 2),
                "final_quality_score": quality_metrics.overall_score,
                "iterations_used": iteration + 1
            }
        }
        
        print(f"🎉 Advanced analysis complete in {total_time:.2f}s with {iteration + 1} iterations")
        return final_results
    
    def _assess_complexity(self, review_text: str) -> AnalysisComplexity:
        """Assess the complexity of the review"""
        text_length = len(review_text)
        word_count = len(review_text.split())
        
        # Simple heuristics for complexity assessment
        if text_length < 100 and word_count < 20:
            return AnalysisComplexity.SIMPLE
        elif text_length < 300 and word_count < 60:
            return AnalysisComplexity.MODERATE
        elif text_length < 600 and word_count < 120:
            return AnalysisComplexity.COMPLEX
        else:
            return AnalysisComplexity.VERY_COMPLEX
    
    def _select_tools_for_complexity(self, complexity: AnalysisComplexity) -> List[Dict[str, Any]]:
        """Select appropriate tools based on complexity"""
        all_tools = self.tool_registry.tools
        
        if complexity == AnalysisComplexity.SIMPLE:
            return [all_tools[0]]  # Just sentiment analysis
        elif complexity == AnalysisComplexity.MODERATE:
            return all_tools[:2]  # Sentiment + keywords
        elif complexity == AnalysisComplexity.COMPLEX:
            return all_tools[:3]  # Sentiment + keywords + issues
        else:  # VERY_COMPLEX
            return all_tools  # All tools
    
    def _perform_tool_calling_analysis(self, review_text: str, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform analysis using OpenAI function calling"""
        
        # Create the analysis prompt
        prompt = f"""
        Analyze the following app review using the available tools. 
        Call the appropriate functions to get detailed analysis.
        
        Review: "{review_text}"
        
        Please analyze this review systematically using the available tools.
        """
        
        try:
            # Call OpenAI with function calling
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                tools=tools,
                tool_choice="auto"
            )
            
            # Process tool calls
            tool_results = {}
            
            if response.choices[0].message.tool_calls:
                for tool_call in response.choices[0].message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    # Execute the tool function
                    tool_function = self.tool_registry.get_tool_function(function_name)
                    if tool_function:
                        result = tool_function(**function_args)
                        tool_results[function_name] = result
                        print(f"🔧 Executed tool: {function_name}")
            
            # Combine results
            combined_results = {
                "deterministic_results": self._combine_deterministic_results(tool_results),
                "llm_analysis": response.choices[0].message.content,
                "tool_calls": len(response.choices[0].message.tool_calls) if response.choices[0].message.tool_calls else 0,
                "tools_used": list(tool_results.keys())
            }
            
            return combined_results
            
        except Exception as e:
            print(f"❌ Error in tool calling analysis: {e}")
            # Fallback to original analysis
            return {
                "deterministic_results": deterministic_analyze(review_text),
                "llm_analysis": "Error in tool calling, using fallback analysis",
                "tool_calls": 0,
                "tools_used": [],
                "error": str(e)
            }
    
    def _combine_deterministic_results(self, tool_results: Dict[str, Any]) -> Dict[str, Any]:
        """Combine results from multiple deterministic tools"""
        combined = {}
        
        for tool_name, result in tool_results.items():
            if tool_name == "analyze_sentiment_deterministic":
                combined.update({
                    "sentiment": result.get("sentiment"),
                    "sentiment_scores": result.get("scores"),
                    "sentiment_confidence": result.get("confidence")
                })
            elif tool_name == "extract_keywords_tfidf":
                combined.update({
                    "keywords": result.get("keywords"),
                    "keyword_count": result.get("count")
                })
            elif tool_name == "detect_issues_deterministic":
                combined.update({
                    "issues_found": result.get("issues"),
                    "issue_count": result.get("issue_count")
                })
            elif tool_name == "categorize_features":
                combined.update({
                    "feature_categories": result.get("categories"),
                    "top_features": result.get("top_features")
                })
        
        return combined
    
    def _apply_improvements(self, current_tools: List[Dict[str, Any]], suggestions: List[str], complexity: AnalysisComplexity) -> List[Dict[str, Any]]:
        """Apply improvement suggestions by selecting different tools"""
        
        # If LLM analysis is suggested, add validation tool
        if any("LLM" in suggestion for suggestion in suggestions):
            all_tools = self.tool_registry.tools
            validation_tool = next((tool for tool in all_tools if tool['function']['name'] == 'validate_analysis_quality'), None)
            if validation_tool and validation_tool not in current_tools:
                current_tools.append(validation_tool)
        
        # For complex reviews, use all available tools
        if complexity in [AnalysisComplexity.COMPLEX, AnalysisComplexity.VERY_COMPLEX]:
            return self.tool_registry.tools
        
        return current_tools


def main():
    """Test the advanced agent"""
    
    print("🚀 Testing Advanced Review Agent with Tool Calling")
    print("="*60)
    
    # Initialize agent
    try:
        agent = AdvancedReviewAgent()
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return
    
    # Test with different complexity reviews
    test_reviews = [
        {
            "name": "Simple Review",
            "text": "Great app!"
        },
        {
            "name": "Moderate Review",
            "text": "Good app with nice interface, but sometimes slow."
        },
        {
            "name": "Complex Review",
            "text": "I've been using this app for 3 months. The interface is clean but the app crashes when uploading large files. Customer support is responsive though. Overall good but needs stability improvements."
        }
    ]
    
    for review in test_reviews:
        print(f"\n{'='*60}")
        print(f"🧪 Testing: {review['name']}")
        print(f"{'='*60}")
        
        results = agent.analyze_review_with_loop(review['text'])
        
        print(f"\n📊 Final Results:")
        print(f"   Complexity: {results['complexity']}")
        print(f"   Iterations: {results['total_iterations']}")
        print(f"   Quality Score: {results['performance']['final_quality_score']:.3f}")
        print(f"   Total Time: {results['performance']['total_time']}s")
        
        # Show evolution across iterations
        print(f"\n📈 Quality Evolution:")
        for hist in results['analysis_history']:
            print(f"   Iteration {hist['iteration']}: {hist['quality_score']:.3f} (tools: {hist['tools_used']})")


if __name__ == "__main__":
    main()