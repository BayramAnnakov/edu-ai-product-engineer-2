"""
LLM Analyzer using OpenAI API
Handles probabilistic analysis of app reviews with contextual insights
"""

import os
import time
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

# Constants
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "1000"))
TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))

# Initialize OpenAI client
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Prompts for different analysis types
ANALYSIS_PROMPT = """
You are a product manager analyzing app store reviews. 
Analyze the following review and provide:

1. **Key Insights**: What are the main points this user is making?
2. **Sentiment Analysis**: Overall sentiment and emotional tone
3. **Feature Mentions**: Specific features or aspects mentioned
4. **Issues Identified**: Any problems or pain points
5. **Recommendations**: Specific actionable recommendations for the product team

Review: "{review_text}"

Please provide a structured analysis that helps product decisions.
"""

SUMMARY_PROMPT = """
You are a product manager creating an executive summary from app review analysis.
Based on the following analysis, create a concise PM-style summary:

Analysis: {analysis}

Provide:
- Executive Summary (2-3 sentences)
- Top 3 Key Insights
- Priority Recommendations (ranked by impact)
"""


def test_openai_connection() -> bool:
    """Test OpenAI API connection"""
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": "Test connection. Reply with 'Connected!'"}],
            max_tokens=10
        )
        result = response.choices[0].message.content.strip()
        print(f"✅ OpenAI connection successful: {result}")
        return True
    except Exception as e:
        print(f"❌ OpenAI connection failed: {e}")
        return False


def llm_analyze(review_text: str) -> Dict[str, Any]:
    """
    Analyze review using OpenAI LLM
    
    Args:
        review_text: The review text to analyze
        
    Returns:
        Dict containing analysis results and metadata
    """
    start_time = time.time()
    
    try:
        # Create the analysis prompt
        prompt = ANALYSIS_PROMPT.format(review_text=review_text)
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE
        )
        
        # Extract response
        analysis = response.choices[0].message.content.strip()
        processing_time = time.time() - start_time
        
        # Parse the structured response (simplified)
        result = {
            "analysis": analysis,
            "insights": _extract_insights(analysis),
            "sentiment": _extract_sentiment(analysis),
            "features": _extract_features(analysis),
            "issues": _extract_issues(analysis),
            "recommendations": _extract_recommendations(analysis),
            "processing_time": round(processing_time, 2),
            "model_used": OPENAI_MODEL,
            "tokens_used": response.usage.total_tokens if response.usage else 0
        }
        
        return result
        
    except Exception as e:
        return {
            "error": str(e),
            "processing_time": time.time() - start_time,
            "model_used": OPENAI_MODEL
        }


def _extract_insights(analysis: str) -> str:
    """Extract key insights from analysis"""
    # Simple extraction - look for insights section
    lines = analysis.split('\n')
    for i, line in enumerate(lines):
        if 'insights' in line.lower() or 'key points' in line.lower():
            # Return next few lines as insights
            insights_lines = []
            for j in range(i+1, min(i+4, len(lines))):
                if lines[j].strip():
                    insights_lines.append(lines[j].strip())
            return '\n'.join(insights_lines)
    return "No specific insights extracted"


def _extract_sentiment(analysis: str) -> str:
    """Extract sentiment from analysis"""
    sentiment_keywords = {
        'positive': ['positive', 'good', 'great', 'excellent', 'love', 'amazing'],
        'negative': ['negative', 'bad', 'terrible', 'awful', 'hate', 'worst'],
        'neutral': ['neutral', 'mixed', 'average', 'okay']
    }
    
    analysis_lower = analysis.lower()
    
    for sentiment, keywords in sentiment_keywords.items():
        if any(keyword in analysis_lower for keyword in keywords):
            return sentiment.capitalize()
    
    return "Mixed"


def _extract_features(analysis: str) -> str:
    """Extract mentioned features from analysis"""
    # Simple feature extraction
    feature_keywords = ['ui', 'interface', 'design', 'performance', 'speed', 'feature', 'functionality']
    lines = analysis.split('\n')
    
    for line in lines:
        if any(keyword in line.lower() for keyword in feature_keywords):
            return line.strip()
    
    return "No specific features mentioned"


def _extract_issues(analysis: str) -> str:
    """Extract identified issues"""
    lines = analysis.split('\n')
    for line in lines:
        if 'issue' in line.lower() or 'problem' in line.lower() or 'bug' in line.lower():
            return line.strip()
    
    return "No specific issues identified"


def _extract_recommendations(analysis: str) -> str:
    """Extract recommendations from analysis"""
    lines = analysis.split('\n')
    for i, line in enumerate(lines):
        if 'recommendation' in line.lower() or 'suggest' in line.lower():
            # Return next few lines as recommendations
            rec_lines = []
            for j in range(i+1, min(i+4, len(lines))):
                if lines[j].strip():
                    rec_lines.append(lines[j].strip())
            return '\n'.join(rec_lines)
    
    return "No specific recommendations provided"


def generate_executive_summary(analysis_results: Dict[str, Any]) -> str:
    """Generate executive summary from analysis results"""
    try:
        prompt = SUMMARY_PROMPT.format(analysis=analysis_results.get('analysis', ''))
        
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.5
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating summary: {e}"


if __name__ == "__main__":
    # Test the LLM analyzer
    print("Testing LLM Analyzer...")
    
    # Test connection
    if not test_openai_connection():
        print("Please check your OpenAI API key in .env file")
        exit(1)
    
    # Test analysis
    sample_review = """
    This app is amazing! The interface is so intuitive and easy to use. 
    However, I've noticed that it crashes sometimes when I try to upload large files. 
    The customer support is great though. Overall, I love this app but the crashing issue needs to be fixed.
    """
    
    print("\n🧠 Testing LLM Analysis...")
    results = llm_analyze(sample_review)
    
    if "error" in results:
        print(f"❌ Error: {results['error']}")
    else:
        print("✅ LLM Analysis Results:")
        print(f"Processing time: {results['processing_time']}s")
        print(f"Model used: {results['model_used']}")
        print(f"Tokens used: {results['tokens_used']}")
        print(f"\nSentiment: {results['sentiment']}")
        print(f"Insights: {results['insights']}")
        print(f"Issues: {results['issues']}")
        print(f"Recommendations: {results['recommendations']}")
        
        # Test executive summary
        print("\n📊 Testing Executive Summary...")
        summary = generate_executive_summary(results)
        print(f"Summary: {summary}")