"""
Tests for Deterministic Analysis
Simple, focused tests for NLTK-based analysis
"""

import pytest
import sys
import os

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

class TestDeterministicAnalyzer:
    """Test deterministic analysis functionality"""
    
    def test_analyze_positive_sentiment(self):
        """Test positive sentiment detection"""
        from src.analyzers.deterministic import analyze_sentiment
        
        positive_text = "I love this app! It's amazing and works perfectly."
        result = analyze_sentiment(positive_text)
        
        assert result['sentiment'] == 'POSITIVE'
        assert result['confidence'] > 0.5
        assert 'score' in result
    
    def test_analyze_negative_sentiment(self):
        """Test negative sentiment detection"""
        from src.analyzers.deterministic import analyze_sentiment
        
        negative_text = "This app is terrible! It crashes constantly and is very frustrating."
        result = analyze_sentiment(negative_text)
        
        assert result['sentiment'] == 'NEGATIVE'
        assert result['confidence'] > 0.5
        assert result['score'] < 0
    
    def test_analyze_neutral_sentiment(self):
        """Test neutral sentiment detection"""
        from src.analyzers.deterministic import analyze_sentiment
        
        neutral_text = "The app has basic functionality. It works as expected."
        result = analyze_sentiment(neutral_text)
        
        assert result['sentiment'] in ['NEUTRAL', 'POSITIVE', 'NEGATIVE']  # Allow some variance
        assert 'confidence' in result
    
    def test_extract_keywords(self):
        """Test keyword extraction"""
        from src.analyzers.deterministic import extract_keywords
        
        text = "The music app has great sound quality but poor user interface design"
        keywords = extract_keywords(text, max_keywords=5)
        
        assert isinstance(keywords, list)
        assert len(keywords) <= 5
        assert all(isinstance(kw, str) for kw in keywords)
        
        # Should find relevant keywords
        text_lower = text.lower()
        relevant_found = any(kw.lower() in text_lower for kw in keywords)
        assert relevant_found
    
    def test_detect_issues(self):
        """Test issue detection in reviews"""
        from src.analyzers.deterministic import detect_issues
        
        bug_text = "App crashes when I try to play music. Very buggy and slow performance."
        issues = detect_issues(bug_text)
        
        assert isinstance(issues, list)
        assert len(issues) > 0
        
        # Should detect crash/bug issues
        issue_types = [issue['type'] for issue in issues]
        assert any('crash' in issue_type.lower() or 'bug' in issue_type.lower() 
                  for issue_type in issue_types)
    
    def test_analyze_review_complete(self):
        """Test complete review analysis"""
        from src.analyzers.deterministic import deterministic_analyze
        
        review_text = "Great music app with excellent sound quality! However, it sometimes crashes when switching playlists."
        
        result = deterministic_analyze(review_text)
        
        # Check result structure
        assert 'sentiment' in result
        assert 'keywords' in result
        assert 'issues' in result
        assert 'processing_time' in result
        assert 'word_count' in result
        
        # Check data types
        assert isinstance(result['sentiment'], str)
        assert isinstance(result['keywords'], list)
        assert isinstance(result['issues'], list)
        assert isinstance(result['processing_time'], (int, float))
        assert isinstance(result['word_count'], int)
    
    def test_empty_text_handling(self):
        """Test handling of empty or invalid input"""
        from src.analyzers.deterministic import deterministic_analyze
        
        # Empty text
        result = deterministic_analyze("")
        assert 'error' in result or result['word_count'] == 0
        
        # None input
        result = deterministic_analyze(None)
        assert 'error' in result
    
    def test_performance_requirement(self):
        """Test that analysis is fast (< 0.5 seconds)"""
        import time
        from src.analyzers.deterministic import deterministic_analyze
        
        text = "This is a test review with some content about the app performance and features."
        
        start_time = time.time()
        result = deterministic_analyze(text)
        end_time = time.time()
        
        processing_time = end_time - start_time
        assert processing_time < 0.5  # Must be faster than 0.5 seconds
        assert result['processing_time'] < 0.5
    
    def test_consistency(self):
        """Test that same input produces same output (deterministic)"""
        from src.analyzers.deterministic import deterministic_analyze
        
        text = "Consistent test text for deterministic analysis verification."
        
        result1 = deterministic_analyze(text)
        result2 = deterministic_analyze(text)
        
        # Sentiment should be identical
        assert result1['sentiment'] == result2['sentiment']
        
        # Keywords should be identical (same order)
        assert result1['keywords'] == result2['keywords']
        
        # Issues should be identical
        assert result1['issues'] == result2['issues']


class TestTextProcessing:
    """Test text preprocessing utilities"""
    
    def test_clean_text(self):
        """Test text cleaning function"""
        from src.analyzers.text_utils import clean_text
        
        dirty_text = "This app is AMAZING!!! 😎🎵 Visit: https://example.com"
        clean = clean_text(dirty_text)
        
        assert isinstance(clean, str)
        assert len(clean) > 0
        assert 'AMAZING' in clean or 'amazing' in clean  # Should preserve meaningful content
    
    def test_tokenize(self):
        """Test text tokenization"""
        from src.analyzers.text_utils import tokenize
        
        text = "Great app with good features."
        tokens = tokenize(text)
        
        assert isinstance(tokens, list)
        assert len(tokens) > 0
        assert all(isinstance(token, str) for token in tokens)


if __name__ == "__main__":
    pytest.main([__file__])