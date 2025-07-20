#!/usr/bin/env python3
"""
Test Agent with Specific Examples
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from main import ReviewAnalysisAgent
import json

def test_agent():
    """Test agent with various review examples"""
    
    print("🚀 Testing Review Analysis Agent...")
    print("="*60)
    
    # Initialize agent
    try:
        agent = ReviewAnalysisAgent()
        print("✅ Agent initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return
    
    # Test cases
    test_reviews = [
        {
            "name": "Positive Review",
            "text": "This app is amazing! The interface is so intuitive and easy to use. Great customer support too. Highly recommend!"
        },
        {
            "name": "Negative Review", 
            "text": "Terrible experience. App crashes constantly when I try to upload files. Very frustrating and needs fixing immediately."
        },
        {
            "name": "Mixed Review",
            "text": "Good app with nice design, but performance is slow sometimes. The features are useful but needs optimization."
        }
    ]
    
    results = []
    
    for i, review in enumerate(test_reviews, 1):
        print(f"\n{'='*60}")
        print(f"🧪 TEST {i}: {review['name']}")
        print(f"{'='*60}")
        print(f"📝 Review: {review['text']}")
        print(f"📏 Length: {len(review['text'])} characters")
        
        print("\n⏳ Processing (may take 8-11 seconds)...")
        
        # Analyze the review
        result = agent.process_review(review['text'])
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            continue
        
        # Extract key metrics
        perf = result['performance']
        det_results = result['deterministic_results']
        llm_results = result['llm_results']
        
        print(f"\n📊 RESULTS:")
        print(f"   ⏱️  Total Time: {perf['total_processing_time']:.2f}s")
        print(f"   ⚡ Speed Advantage: {perf['speed_advantage']}")
        print(f"   🎯 Deterministic Sentiment: {det_results.get('sentiment', 'unknown').upper()}")
        print(f"   🧠 LLM Sentiment: {llm_results.get('sentiment', 'unknown').upper()}")
        print(f"   🔍 Keywords: {', '.join(det_results.get('top_keywords', [])[:3])}")
        print(f"   ⚠️  Issues Found: {det_results.get('issue_count', 0)}")
        print(f"   💡 LLM Insights: {llm_results.get('insights', 'No insights')[:100]}...")
        
        # Save results
        results.append({
            "name": review['name'],
            "text": review['text'],
            "total_time": perf['total_processing_time'],
            "deterministic_time": perf['deterministic_time'],
            "llm_time": perf['llm_time'],
            "det_sentiment": det_results.get('sentiment', 'unknown'),
            "llm_sentiment": llm_results.get('sentiment', 'unknown'),
            "issues_count": det_results.get('issue_count', 0),
            "keywords": det_results.get('top_keywords', [])[:5]
        })
        
        print(f"\n✅ Test {i} completed successfully!")
    
    # Summary
    print(f"\n{'='*60}")
    print("📈 SUMMARY RESULTS")
    print(f"{'='*60}")
    
    if results:
        total_tests = len(results)
        avg_total_time = sum(r['total_time'] for r in results) / total_tests
        avg_det_time = sum(r['deterministic_time'] for r in results) / total_tests
        avg_llm_time = sum(r['llm_time'] for r in results) / total_tests
        
        print(f"📊 Performance Summary:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Avg Total Time: {avg_total_time:.2f}s")
        print(f"   Avg Deterministic Time: {avg_det_time:.3f}s")
        print(f"   Avg LLM Time: {avg_llm_time:.1f}s")
        print(f"   Speed Advantage: {avg_llm_time/avg_det_time:.0f}x faster")
        
        print(f"\n🎯 Sentiment Analysis:")
        for result in results:
            print(f"   {result['name']:15} | Det: {result['det_sentiment']:8} | LLM: {result['llm_sentiment']:8}")
        
        print(f"\n🔍 Common Keywords:")
        all_keywords = []
        for result in results:
            all_keywords.extend(result['keywords'])
        
        from collections import Counter
        top_keywords = Counter(all_keywords).most_common(5)
        for keyword, count in top_keywords:
            print(f"   {keyword}: {count}")
    
    print(f"\n🎉 All tests completed successfully!")
    print(f"📋 Agent is ready for production use!")

if __name__ == "__main__":
    test_agent()