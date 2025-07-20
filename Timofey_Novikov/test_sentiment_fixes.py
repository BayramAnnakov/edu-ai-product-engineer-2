#!/usr/bin/env python3
"""
Test sentiment analysis fixes with problematic reviews
"""

import sys
import os
sys.path.append('src')

from analyzers.deterministic import analyze_sentiment
from analyzers.llm_analyzer import llm_analyze
from agents.sentiment_agent import SentimentAgent

def test_problematic_reviews():
    """Test fixes on problematic reviews"""
    
    # The problematic review from the report
    problematic_review = "Даже не думайте здесь учиться, поддержка отвечает неделями, и пишет что ответим в 48 часов, каждый раз надо напоминать, платформа отстой, сделал дз оно ушло, потом снова появилось, продажник на первом уроке вам прям впарит эти уроки и на подольше, не берите на год или 6 месяцев точно, если хотите по..."
    
    test_reviews = [
        ("Отлично 👾👾👾", "POSITIVE"),  # Should be positive
        (problematic_review, "NEGATIVE"),  # Should be negative (was neutral)
        ("Приложение очень удобное. Дз можно делать где угодно!!!", "POSITIVE"),  # Should be positive
        ("ночью невозможно учить", "NEGATIVE"),  # Should be negative
        ("Проблема в том, что перевод на русский часто косячный", "NEGATIVE"),  # Should be negative
    ]
    
    agent = SentimentAgent()
    
    print("🧪 Testing Sentiment Analysis Fixes on Problematic Reviews:")
    print("=" * 80)
    
    correct_det = 0
    correct_llm = 0
    correct_agent = 0
    
    for i, (review, expected) in enumerate(test_reviews):
        print(f"\nTest {i+1}: {review[:70]}...")
        print(f"Expected: {expected}")
        
        # Deterministic analysis
        det_result = analyze_sentiment(review)
        det_sentiment = det_result['sentiment']
        det_correct = det_sentiment == expected
        if det_correct:
            correct_det += 1
        print(f"  NLTK: {det_sentiment} {'✅' if det_correct else '❌'}")
        
        # LLM analysis
        llm_result = llm_analyze(review)
        llm_sentiment = llm_result.get('sentiment', 'Unknown')
        # Normalize for comparison
        llm_sentiment_normalized = llm_sentiment.upper() if llm_sentiment else 'UNKNOWN'
        llm_correct = llm_sentiment_normalized == expected
        if llm_correct:
            correct_llm += 1
        print(f"  LLM: {llm_sentiment} {'✅' if llm_correct else '❌'}")
        
        # Agent analysis
        agent_result = agent.analyze(review)
        agent_sentiment = agent_result['sentiment']
        agent_correct = agent_sentiment == expected
        if agent_correct:
            correct_agent += 1
        print(f"  Agent: {agent_sentiment} {'✅' if agent_correct else '❌'}")
    
    print("\n" + "=" * 80)
    print(f"📊 Accuracy Results:")
    print(f"  NLTK: {correct_det}/{len(test_reviews)} ({(correct_det/len(test_reviews))*100:.1f}%)")
    print(f"  LLM: {correct_llm}/{len(test_reviews)} ({(correct_llm/len(test_reviews))*100:.1f}%)")
    print(f"  Agent: {correct_agent}/{len(test_reviews)} ({(correct_agent/len(test_reviews))*100:.1f}%)")
    
    # Special test for the problematic review
    print(f"\n🎯 Special Test - Problematic Review:")
    print(f"Review: {problematic_review[:100]}...")
    
    det_result = analyze_sentiment(problematic_review)
    llm_result = llm_analyze(problematic_review)
    agent_result = agent.analyze(problematic_review)
    
    print(f"  NLTK: {det_result['sentiment']} (was NEUTRAL)")
    print(f"  LLM: {llm_result.get('sentiment', 'Unknown')} (was unknown)")
    print(f"  Agent: {agent_result['sentiment']} (was NEUTRAL)")
    
    all_negative = all(result['sentiment'].upper() == 'NEGATIVE' for result in [det_result, {'sentiment': llm_result.get('sentiment', '')}, agent_result])
    print(f"  All methods detect as NEGATIVE: {'✅' if all_negative else '❌'}")
    
    return correct_det, correct_llm, correct_agent

if __name__ == "__main__":
    test_problematic_reviews()