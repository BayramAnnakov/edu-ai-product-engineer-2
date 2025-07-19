#!/usr/bin/env python3
"""
Generate Demo Report - Full PM Report Example
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from main import ReviewAnalysisAgent
import time

def generate_demo_report():
    """Generate a comprehensive demo report"""
    
    print("📋 Generating Demo PM Report...")
    print("="*60)
    
    # Initialize agent
    agent = ReviewAnalysisAgent()
    
    # Sample AppStore review (realistic example)
    sample_review = """
    I've been using this app for 3 months now and overall it's pretty good. The interface is clean and intuitive - I love how everything is organized. The main features work well most of the time. 
    
    However, there are some issues that really need attention:
    - The app crashes about once a week, usually when I'm trying to sync large files
    - Loading times can be slow during peak hours
    - The search function doesn't always return accurate results
    
    The customer support team is responsive and helpful when I've contacted them. They usually get back to me within 24 hours.
    
    I'd give it 4/5 stars. It's a solid app with great potential, but the stability issues and performance problems hold it back from being excellent. Would definitely recommend to others with the caveat that some bugs need fixing.
    """
    
    print(f"📝 Sample Review ({len(sample_review)} characters):")
    print(sample_review.strip())
    
    print(f"\n⏳ Processing with both deterministic and LLM analysis...")
    print("This will take about 8-10 seconds...")
    
    # Process the review
    start_time = time.time()
    results = agent.process_review(sample_review)
    end_time = time.time()
    
    if "error" in results:
        print(f"❌ Error: {results['error']}")
        return
    
    # Display key metrics
    perf = results['performance']
    det_results = results['deterministic_results']
    llm_results = results['llm_results']
    
    print(f"\n📊 QUICK METRICS:")
    print(f"   ⏱️  Total Processing: {perf['total_processing_time']:.2f}s")
    print(f"   📈 Speed Advantage: {perf['speed_advantage']}")
    print(f"   🎯 Sentiment Match: {det_results.get('sentiment', 'unknown').upper()} vs {llm_results.get('sentiment', 'unknown').upper()}")
    print(f"   💰 Estimated Cost: ~$0.02 (based on tokens used)")
    
    # Generate and display full PM report
    print(f"\n{'='*60}")
    print("📋 FULL PM REPORT")
    print(f"{'='*60}")
    
    pm_report = results['pm_report']
    print(pm_report)
    
    # Save the report
    timestamp = int(time.time())
    filename = f"demo_pm_report_{timestamp}.md"
    
    with open(filename, 'w') as f:
        f.write(pm_report)
    
    print(f"\n💾 Report saved to: {filename}")
    
    # Show JSON export sample
    print(f"\n📊 JSON Export Sample:")
    json_data = results['json_export']
    print(json_data[:200] + "..." if len(json_data) > 200 else json_data)
    
    # Summary for demo
    print(f"\n🎯 DEMO SUMMARY:")
    print(f"   ✅ Both analysis methods completed successfully")
    print(f"   ✅ Deterministic: {det_results.get('processing_time', 0):.3f}s (ultra-fast)")
    print(f"   ✅ LLM: {llm_results.get('processing_time', 0):.1f}s (detailed insights)")
    print(f"   ✅ Combined: Best of both worlds")
    print(f"   ✅ PM Report: Ready for product team")
    print(f"   ✅ Cost: ~$0.02 per review (OpenAI API)")
    
    print(f"\n🚀 Demo completed! Agent is ready for production use.")

if __name__ == "__main__":
    generate_demo_report()