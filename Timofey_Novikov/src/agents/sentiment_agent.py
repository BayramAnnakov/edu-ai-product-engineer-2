"""
Simple Sentiment Analysis Agent
Mock implementation for TDD
"""

from typing import Dict, Any


class SentimentAgent:
    """Mock sentiment analysis agent"""
    
    def __init__(self):
        """Initialize sentiment agent"""
        self.model = "gpt-4.1"
        self.temperature = 0.1
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text using basic keyword analysis
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment analysis results
        """
        
        # Basic sentiment analysis using keywords
        text_lower = text.lower()
        
        # Russian and English sentiment keywords
        positive_words = [
            # English
            'good', 'great', 'excellent', 'amazing', 'love', 'like', 'best', 'awesome', 'fantastic', 'wonderful',
            'perfect', 'brilliant', 'outstanding', 'superb', 'marvelous', 'incredible', 'fabulous', 'terrific',
            # Russian
            'отлично', 'хорошо', 'прекрасно', 'удобно', 'нравится', 'люблю', 'классно', 'супер', 'замечательно', 
            'великолепно', 'благодарность', 'спасибо', 'лучший', 'интересно', 'полезно', 'рекомендую'
        ]
        
        negative_words = [
            # English  
            'bad', 'terrible', 'awful', 'horrible', 'hate', 'worst', 'crash', 'bug', 'problem', 'issue',
            'slow', 'broken', 'useless', 'disappointing', 'frustrating', 'annoying', 'poor', 'fail',
            # Russian (expanded)
            'плохо', 'ужасно', 'отстой', 'проблема', 'ошибка', 'баг', 'глюк', 'вылетает', 'тормозит', 
            'косячный', 'косяк', 'невозможно', 'отвратительно', 'кошмар', 'разочарован', 'жалоба', 'навязчиво',
            'думайте', 'неделями', 'напоминать', 'впарит', 'претензией', 'отвечает', 'ответим'
        ]
        
        # Count sentiment words
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        # Determine sentiment
        if positive_count > negative_count:
            sentiment = 'POSITIVE'
            confidence = min(0.9, 0.6 + (positive_count * 0.1))
            emotions = ['joy', 'satisfaction']
            intensity = 'high' if positive_count > 2 else 'medium'
        elif negative_count > positive_count:
            sentiment = 'NEGATIVE'
            confidence = min(0.9, 0.6 + (negative_count * 0.1))
            emotions = ['frustration', 'disappointment']
            intensity = 'high' if negative_count > 2 else 'medium'
        else:
            sentiment = 'NEUTRAL'
            confidence = 0.5
            emotions = ['neutral']
            intensity = 'low'
        
        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'emotions': emotions, 
            'intensity': intensity,
            'positive_words_found': positive_count,
            'negative_words_found': negative_count
        }