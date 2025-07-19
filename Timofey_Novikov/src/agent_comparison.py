#!/usr/bin/env python3
"""
Comparison between Basic and Advanced Review Analysis Agents
Demonstrates evolution from simple parallel processing to intelligent agent loop
"""

import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from main import ReviewAnalysisAgent as BasicAgent
from src.advanced_agent import AdvancedReviewAgent

def compare_agents():
    """Compare basic vs advanced agent performance"""
    
    print("🆚 AGENT COMPARISON: Basic vs Advanced")
    print("="*60)
    
    # Initialize both agents
    try:
        basic_agent = BasicAgent()
        advanced_agent = AdvancedReviewAgent()
        print("✅ Both agents initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize agents: {e}")
        return
    
    # Test cases with different complexity levels
    test_cases = [
        {
            "name": "Simple Positive Review",
            "text": "Great app! Love it.",
            "expected_complexity": "simple"
        },
        {
            "name": "Moderate Mixed Review",
            "text": "Good app with nice design, but performance is slow sometimes. The features are useful but needs optimization.",
            "expected_complexity": "moderate"
        },
        {
            "name": "Complex Detailed Review",
            "text": """I've been using this app for 3 months now and overall it's pretty good. The interface is clean and intuitive - I love how everything is organized. The main features work well most of the time. 
            
            However, there are some issues that really need attention:
            - The app crashes about once a week, usually when I'm trying to sync large files
            - Loading times can be slow during peak hours
            - The search function doesn't always return accurate results
            
            The customer support team is responsive and helpful when I've contacted them. They usually get back to me within 24 hours.
            
            I'd give it 4/5 stars. It's a solid app with great potential, but the stability issues and performance problems hold it back from being excellent.""",
            "expected_complexity": "complex"
        }
    ]
    
    comparison_results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"🧪 TEST CASE {i}: {test_case['name']}")
        print(f"{'='*60}")
        print(f"📝 Review length: {len(test_case['text'])} characters")
        print(f"🎯 Expected complexity: {test_case['expected_complexity']}")
        
        # Test Basic Agent
        print(f"\n🔵 BASIC AGENT:")
        basic_start = time.time()
        basic_results = basic_agent.process_review(test_case['text'])
        basic_end = time.time()
        basic_time = basic_end - basic_start
        
        print(f"   ⏱️  Processing time: {basic_time:.2f}s")
        print(f"   🎯 Deterministic sentiment: {basic_results['deterministic_results'].get('sentiment', 'unknown')}")
        print(f"   🧠 LLM sentiment: {basic_results['llm_results'].get('sentiment', 'unknown')}")
        print(f"   ⚡ Speed advantage: {basic_results['performance']['speed_advantage']}")
        
        # Test Advanced Agent
        print(f"\n🟢 ADVANCED AGENT:")
        advanced_start = time.time()
        advanced_results = advanced_agent.analyze_review_with_loop(test_case['text'])
        advanced_end = time.time()
        advanced_time = advanced_end - advanced_start
        
        print(f"   ⏱️  Processing time: {advanced_time:.2f}s")
        print(f"   📊 Detected complexity: {advanced_results['complexity']}")
        print(f"   🔄 Iterations used: {advanced_results['total_iterations']}")
        print(f"   📈 Final quality score: {advanced_results['performance']['final_quality_score']:.3f}")
        
        # Quality evolution
        print(f"   📊 Quality evolution:")
        for hist in advanced_results['analysis_history']:
            tools_used = ', '.join(hist['tools_used'])
            print(f"      Iteration {hist['iteration']}: {hist['quality_score']:.3f} (tools: {tools_used})")
        
        # Store comparison results
        comparison_results.append({
            "test_case": test_case['name'],
            "text_length": len(test_case['text']),
            "basic_time": basic_time,
            "advanced_time": advanced_time,
            "basic_sentiment": basic_results['deterministic_results'].get('sentiment', 'unknown'),
            "advanced_complexity": advanced_results['complexity'],
            "advanced_iterations": advanced_results['total_iterations'],
            "advanced_quality": advanced_results['performance']['final_quality_score'],
            "time_difference": advanced_time - basic_time
        })
    
    # Summary comparison
    print(f"\n{'='*60}")
    print("📊 COMPARISON SUMMARY")
    print(f"{'='*60}")
    
    total_basic_time = sum(r['basic_time'] for r in comparison_results)
    total_advanced_time = sum(r['advanced_time'] for r in comparison_results)
    avg_quality = sum(r['advanced_quality'] for r in comparison_results) / len(comparison_results)
    
    print(f"📈 Performance Summary:")
    print(f"   Total Basic Time: {total_basic_time:.2f}s")
    print(f"   Total Advanced Time: {total_advanced_time:.2f}s")
    print(f"   Time Overhead: {total_advanced_time - total_basic_time:.2f}s ({((total_advanced_time/total_basic_time - 1) * 100):.1f}%)")
    print(f"   Average Quality Score: {avg_quality:.3f}")
    
    print(f"\n🎯 Key Differences:")
    print(f"   Basic Agent:")
    print(f"   ✅ Faster processing (simple parallel execution)")
    print(f"   ✅ Predictable performance")
    print(f"   ❌ No quality control")
    print(f"   ❌ No adaptation to complexity")
    
    print(f"\n   Advanced Agent:")
    print(f"   ✅ Intelligent tool selection")
    print(f"   ✅ Quality-driven iterations")
    print(f"   ✅ Complexity-aware processing")
    print(f"   ✅ Self-improvement capabilities")
    print(f"   ❌ Higher computational overhead")
    
    print(f"\n🏆 Best Use Cases:")
    print(f"   Basic Agent: High-volume, simple reviews, cost-sensitive scenarios")
    print(f"   Advanced Agent: Complex analysis, quality-critical applications, adaptive requirements")
    
    # Detailed comparison table
    print(f"\n📋 Detailed Comparison:")
    print(f"{'Test Case':<25} | {'Basic Time':<10} | {'Adv Time':<10} | {'Quality':<8} | {'Iterations':<10}")
    print("-" * 75)
    
    for result in comparison_results:
        print(f"{result['test_case']:<25} | {result['basic_time']:<10.2f} | {result['advanced_time']:<10.2f} | {result['advanced_quality']:<8.3f} | {result['advanced_iterations']:<10}")
    
    print(f"\n🚀 Evolution Complete!")
    print(f"From parallel processing to intelligent agent loop with quality control! 🎉")


if __name__ == "__main__":
    compare_agents()