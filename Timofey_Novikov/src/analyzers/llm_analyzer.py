"""
LLM Analyzer using OpenAI API
Handles probabilistic analysis of app reviews with contextual insights
"""

import os
import time
import json
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
import openai
from openai import OpenAI

# Load environment variables
load_dotenv()

# Constants
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "1000"))
TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

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
    Analyze review using OpenAI LLM with improved Russian support
    
    Args:
        review_text: The review text to analyze
        
    Returns:
        Dict containing analysis results and metadata
    """
    start_time = time.time()
    
    try:
        # Create a more specific prompt for sentiment analysis
        prompt = f"""
        Проанализируй этот отзыв о приложении Skyeng и определи настроение пользователя.

        Отзыв: "{review_text}"

        Дай анализ в формате JSON:
        {{
            "sentiment": "Positive/Negative/Neutral",
            "confidence": 0.8,
            "reasoning": "краткое объяснение",
            "key_points": ["основная проблема/достоинство"],
            "issues": ["конкретные проблемы"] или [],
            "positive_aspects": ["позитивные аспекты"] или []
        }}

        Отвечай ТОЛЬКО в JSON формате без дополнительного текста.
        """
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Ты эксперт по анализу отзывов на русском языке. Отвечай только в JSON формате."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.1
        )
        
        # Extract response
        analysis_text = response.choices[0].message.content.strip()
        processing_time = time.time() - start_time
        
        # Try to parse JSON response
        try:
            analysis_json = json.loads(analysis_text)
            sentiment = analysis_json.get('sentiment', 'Mixed')
            confidence = analysis_json.get('confidence', 0.5)
            issues = analysis_json.get('issues', [])
            positive_aspects = analysis_json.get('positive_aspects', [])
            reasoning = analysis_json.get('reasoning', 'No reasoning provided')
        except json.JSONDecodeError:
            # Fallback sentiment extraction if JSON parsing fails
            sentiment = _extract_sentiment_fallback(analysis_text, review_text)
            confidence = 0.3
            issues = []
            positive_aspects = []
            reasoning = "JSON parsing failed, used fallback method"
        
        result = {
            "sentiment": sentiment,
            "confidence": confidence,
            "analysis": analysis_text,
            "reasoning": reasoning,
            "issues": issues,
            "positive_aspects": positive_aspects,
            "processing_time": round(processing_time, 2),
            "model_used": OPENAI_MODEL,
            "tokens_used": response.usage.total_tokens if response.usage else 0,
            "method": "llm_openai_improved"
        }
        
        return result
        
    except Exception as e:
        # Use fallback sentiment analysis when API fails
        fallback_sentiment = _analyze_review_sentiment_directly(review_text)
        return {
            "error": str(e),
            "sentiment": fallback_sentiment,
            "processing_time": time.time() - start_time,
            "model_used": OPENAI_MODEL,
            "method": "llm_fallback_keywords",
            "reasoning": "API failed, used keyword-based fallback"
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


def _extract_sentiment_fallback(analysis: str, review_text: str) -> str:
    """Fallback sentiment extraction when JSON parsing fails"""
    
    # Try to extract from analysis first
    analysis_lower = analysis.lower()
    
    # Russian and English sentiment indicators
    positive_indicators = ['positive', 'позитив', 'хорош', 'отлич', 'класс', 'супер', 'good', 'great', 'excellent']
    negative_indicators = ['negative', 'негатив', 'плох', 'ужас', 'отстой', 'bad', 'terrible', 'awful']
    
    pos_count = sum(1 for word in positive_indicators if word in analysis_lower)
    neg_count = sum(1 for word in negative_indicators if word in analysis_lower)
    
    if pos_count > neg_count:
        return "Positive"
    elif neg_count > pos_count:
        return "Negative"
    
    # If analysis doesn't help, analyze the review text directly
    return _analyze_review_sentiment_directly(review_text)


def _analyze_review_sentiment_directly(review_text: str) -> str:
    """Direct sentiment analysis of review text"""
    text_lower = review_text.lower()
    
    # Russian sentiment keywords
    positive_words = ['отлично', 'хорошо', 'прекрасно', 'удобно', 'нравится', 'люблю', 'классно', 'супер', 'замечательно', 'благодарность', 'спасибо', 'рекомендую']
    negative_words = ['плохо', 'ужасно', 'отстой', 'проблема', 'ошибка', 'вылетает', 'тормозит', 'косячный', 'невозможно', 'разочарован', 'жалоба', 'навязчиво', 'думайте', 'неделями']
    
    pos_count = sum(1 for word in positive_words if word in text_lower)
    neg_count = sum(1 for word in negative_words if word in text_lower)
    
    if pos_count > neg_count:
        return "Positive"
    elif neg_count > pos_count:
        return "Negative"
    else:
        return "Neutral"


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


def generate_llm_summary(reviews: List[str]) -> Dict[str, Any]:
    """Generate LLM-based summary of all reviews"""
    
    if not reviews:
        return {'error': 'No reviews provided'}
    
    start_time = time.time()
    
    try:
        # Prepare reviews text (limit to prevent token overflow)
        reviews_text = "\n---\n".join(reviews[:15])  # Limit to 15 reviews
        
        prompt = f"""
        Проанализируй все отзывы о приложении Skyeng и создай подробное резюме:

        ОТЗЫВЫ:
        {reviews_text}

        Создай структурированный анализ в JSON формате:
        {{
            "general_sentiment": "общее настроение (positive/negative/mixed)",
            "sentiment_distribution": {{
                "positive_count": число,
                "negative_count": число,
                "neutral_count": число
            }},
            "main_themes": ["тема1", "тема2", "тема3"],
            "top_issues": ["проблема1", "проблема2", "проблема3"],
            "positive_highlights": ["плюс1", "плюс2", "плюс3"],
            "key_insights": ["инсайт1", "инсайт2", "инсайт3"],
            "summary_text": "подробное текстовое резюме на русском языке"
        }}

        Отвечай только в JSON формате без дополнительного текста.
        """
        
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Ты эксперт по анализу отзывов мобильных приложений. Отвечай только в JSON формате на русском языке."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1500
        )
        
        response_content = response.choices[0].message.content
        
        try:
            analysis_result = json.loads(response_content)
        except json.JSONDecodeError:
            # Fallback parsing
            analysis_result = {
                'general_sentiment': 'mixed',
                'sentiment_distribution': {'positive_count': 0, 'negative_count': 0, 'neutral_count': len(reviews)},
                'main_themes': ['интерфейс', 'производительность', 'функциональность'],
                'top_issues': ['технические проблемы'],
                'positive_highlights': ['удобство использования'],
                'key_insights': ['необходимо улучшение'],
                'summary_text': 'Анализ завершен с ошибкой парсинга JSON',
                'raw_response': response_content
            }
        
        processing_time = time.time() - start_time
        
        analysis_result.update({
            'method': 'llm_summary',
            'total_reviews_analyzed': len(reviews),
            'processing_time': round(processing_time, 2),
            'model_used': OPENAI_MODEL,
            'tokens_used': response.usage.total_tokens if hasattr(response, 'usage') else 0
        })
        
        return analysis_result
        
    except Exception as e:
        return {
            'error': str(e),
            'processing_time': time.time() - start_time,
            'method': 'llm_summary'
        }


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