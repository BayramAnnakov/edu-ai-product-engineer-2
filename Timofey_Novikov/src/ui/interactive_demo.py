#!/usr/bin/env python3
"""
Interactive Demo for Review Analysis Agent
Simple command-line interface to test the agent
"""

import sys
import time
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from main import ReviewAnalysisAgent

def print_banner():
    """Print welcome banner"""
    print("\n" + "="*60)
    print("🤖 REVIEW ANALYSIS AGENT - INTERACTIVE DEMO")
    print("AI Product Engineer Season 2 - Lesson 1")
    print("="*60)
    print("📊 Comparing Deterministic vs Probabilistic Analysis")
    print("⚡ Speed: Deterministic ~0.016s vs LLM ~8-11s")
    print("="*60)

def get_sample_reviews():
    """Get sample reviews for testing"""
    return {
        "1": {
            "title": "Positive Review",
            "text": "This app is amazing! The interface is so intuitive and easy to use. Great customer support too. Highly recommend!"
        },
        "2": {
            "title": "Negative Review", 
            "text": "Terrible experience. App crashes constantly when I try to upload files. Very frustrating and needs fixing immediately."
        },
        "3": {
            "title": "Mixed Review",
            "text": "Good app with nice design, but performance is slow sometimes. The features are useful but needs optimization."
        },
        "4": {
            "title": "Detailed Review",
            "text": "I love the clean interface and the app works great most of the time. However, I've noticed that it crashes sometimes when I try to upload large files. The customer support is responsive though. Overall good but the stability issues need to be addressed."
        }
    }

def display_results(results):
    """Display analysis results in a formatted way"""
    
    if "error" in results:
        print(f"❌ Error: {results['error']}")
        return
    
    print("\n" + "="*60)
    print("📊 ANALYSIS RESULTS")
    print("="*60)
    
    # Performance metrics
    perf = results['performance']
    print(f"⏱️  Total Processing Time: {perf['total_processing_time']}s")
    print(f"⚡ Speed Advantage: {perf['speed_advantage']}")
    
    # Sentiment comparison
    det_sentiment = results['deterministic_results'].get('sentiment', 'unknown')
    llm_sentiment = results['llm_results'].get('sentiment', 'unknown')
    
    print(f"\n🎯 SENTIMENT ANALYSIS:")
    print(f"   Deterministic: {det_sentiment.upper()}")
    print(f"   LLM: {llm_sentiment.upper()}")
    
    # Detailed metrics
    det_results = results['deterministic_results']
    llm_results = results['llm_results']
    
    print(f"\n📈 DETAILED METRICS:")
    print(f"   Deterministic Time: {det_results.get('processing_time', 0):.3f}s")
    print(f"   LLM Time: {llm_results.get('processing_time', 0):.1f}s")
    print(f"   Model Used: {llm_results.get('model_used', 'unknown')}")
    print(f"   Tokens Used: {llm_results.get('tokens_used', 0)}")
    
    # Keywords and insights
    keywords = det_results.get('top_keywords', [])
    insights = llm_results.get('insights', 'No insights available')
    
    print(f"\n🔍 KEY FINDINGS:")
    print(f"   Top Keywords: {', '.join(keywords[:5])}")
    print(f"   Issues Found: {det_results.get('issue_count', 0)}")
    print(f"   LLM Insights: {insights}")
    
    # Recommendations
    recommendations = llm_results.get('recommendations', 'No recommendations')
    print(f"   Recommendations: {recommendations}")

def main():
    """Main interactive demo"""
    
    print_banner()
    
    # Initialize agent
    try:
        agent = ReviewAnalysisAgent()
        print("✅ Agent initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        print("Please check your .env file and ensure OPENAI_API_KEY is set")
        return
    
    samples = get_sample_reviews()
    
    while True:
        print("\n" + "-"*40)
        print("🎮 DEMO OPTIONS:")
        print("-"*40)
        print("1-4: Analyze sample reviews")
        print("5: Enter custom review")
        print("6: Batch process all samples")
        print("7: Performance comparison")
        print("8: Generate full PM report")
        print("0: Exit")
        print("-"*40)
        
        choice = input("👆 Choose an option (0-8): ").strip()
        
        if choice == "0":
            print("👋 Thanks for using Review Analysis Agent!")
            break
        
        elif choice in ["1", "2", "3", "4"]:
            sample = samples[choice]
            print(f"\n📝 Analyzing: {sample['title']}")
            print(f"Text: {sample['text']}")
            
            print("\n⏳ Processing (this may take 8-11 seconds)...")
            results = agent.process_review(sample['text'])
            display_results(results)
        
        elif choice == "5":
            print("\n📝 Enter your custom review:")
            custom_text = input("Review text: ").strip()
            
            if not custom_text:
                print("❌ Empty review text!")
                continue
            
            print("\n⏳ Processing (this may take 8-11 seconds)...")
            results = agent.process_review(custom_text)
            display_results(results)
        
        elif choice == "6":
            print("\n🔄 Batch processing all sample reviews...")
            sample_texts = [sample['text'] for sample in samples.values()]
            
            print("⏳ This will take about 30-40 seconds...")
            batch_results = agent.batch_process(sample_texts)
            
            if batch_results:
                print(f"\n📊 BATCH RESULTS:")
                print(f"   Total Reviews: {batch_results['batch_info']['total_reviews']}")
                print(f"   Successful: {batch_results['batch_info']['successful']}")
                print(f"   Failed: {batch_results['batch_info']['failed']}")
                print(f"   Total Time: {batch_results['performance']['total_batch_time']:.1f}s")
                print(f"   Avg Det Time: {batch_results['performance']['avg_deterministic_time']:.3f}s")
                print(f"   Avg LLM Time: {batch_results['performance']['avg_llm_time']:.1f}s")
        
        elif choice == "7":
            print("\n⚡ PERFORMANCE COMPARISON:")
            print("   Deterministic Analysis:")
            print("   ✅ Speed: ~0.016s")
            print("   ✅ Reproducible: 100%")
            print("   ✅ Cost: Free")
            print("   ❌ Limited insights")
            print()
            print("   LLM Analysis:")
            print("   ✅ Deep insights")
            print("   ✅ Contextual understanding")
            print("   ✅ Recommendations")
            print("   ❌ Speed: ~8-11s")
            print("   ❌ Cost: ~$0.01-0.05 per review")
            print("   ❌ Variable output")
            print()
            print("   🎯 Best Approach: Hybrid (both together)")
            print("   📊 Speed advantage: ~685x faster for deterministic")
        
        elif choice == "8":
            print("\n📋 Choose a sample for full PM report:")
            for key, sample in samples.items():
                print(f"   {key}: {sample['title']}")
            
            report_choice = input("Select (1-4): ").strip()
            
            if report_choice in samples:
                sample = samples[report_choice]
                print(f"\n📝 Generating PM report for: {sample['title']}")
                print("⏳ Processing...")
                
                results = agent.process_review(sample['text'])
                
                if "error" not in results:
                    print("\n" + "="*60)
                    print("📋 FULL PM REPORT")
                    print("="*60)
                    print(results['pm_report'])
                    
                    # Ask if user wants to save
                    save = input("\n💾 Save report to file? (y/n): ").strip().lower()
                    if save == 'y':
                        filename = f"pm_report_{int(time.time())}.md"
                        with open(filename, 'w') as f:
                            f.write(results['pm_report'])
                        print(f"✅ Report saved to {filename}")
                else:
                    print("❌ Failed to generate report")
        
        else:
            print("❌ Invalid choice. Please try again.")
        
        # Wait for user to read results
        input("\n⏸️  Press Enter to continue...")

if __name__ == "__main__":
    main()