"""
Main Agent Orchestrator
Coordinates deterministic and LLM analysis using OpenAI Agents SDK approach
"""

import asyncio
import time
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from dotenv import load_dotenv

# Import our analysis modules
from src.analyzers.deterministic import deterministic_analyze, generate_deterministic_summary
from src.analyzers.llm_analyzer import llm_analyze, generate_llm_summary
from src.analyzers.sentiment_comparison import compare_sentiment_methods
from src.reports.report_generator import generate_pm_report, export_report_json
from src.agents import AgentCoordinator
from src.data.appstore_client import AppStoreClient

# Load environment variables
load_dotenv()

class ReviewAnalysisAgent:
    """
    Main agent that orchestrates both deterministic and LLM analysis
    Following OpenAI Agents SDK pattern
    """
    
    def __init__(self):
        self.name = "ReviewAnalysisAgent"
        self.version = "1.0.0"
        self.capabilities = [
            "deterministic_analysis",
            "llm_analysis", 
            "openai_agents_coordination",
            "report_generation",
            "parallel_processing"
        ]
        
        # Initialize agent coordinator
        self.agent_coordinator = AgentCoordinator()
        
        # Validate environment
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        print(f"✅ {self.name} v{self.version} initialized")
        print(f"📋 Capabilities: {', '.join(self.capabilities)}")
        print(f"🤖 Agent Coordinator: {len(self.agent_coordinator.agents)} specialized agents")
    
    def process_review(self, review_text: str, parallel: bool = True) -> Dict[str, Any]:
        """
        Process a single review using both analysis methods
        
        Args:
            review_text: The review text to analyze
            parallel: Whether to run analyses in parallel (default: True)
            
        Returns:
            Dict containing combined analysis results
        """
        
        if not review_text or not review_text.strip():
            return {
                "error": "Empty review text provided",
                "timestamp": time.time()
            }
        
        print(f"🤖 Processing review ({len(review_text)} characters)...")
        start_time = time.time()
        
        if parallel:
            # Run analyses in parallel (including OpenAI agents)
            det_results, llm_results, agent_results = self._parallel_analysis(review_text)
        else:
            # Run analyses sequentially (including OpenAI agents)
            det_results, llm_results, agent_results = self._sequential_analysis(review_text)
        
        # Generate combined report
        try:
            pm_report = generate_pm_report(det_results, llm_results, review_text)
            json_export = export_report_json(det_results, llm_results, review_text)
        except Exception as e:
            pm_report = f"Error generating report: {e}"
            json_export = "{}"
        
        total_time = time.time() - start_time
        
        # Compile final results
        results = {
            "agent_info": {
                "name": self.name,
                "version": self.version,
                "processing_mode": "parallel" if parallel else "sequential"
            },
            "review_text": review_text,
            "deterministic_results": det_results,
            "llm_results": llm_results,
            "agent_results": agent_results,
            "pm_report": pm_report,
            "json_export": json_export,
            "performance": {
                "total_processing_time": round(total_time, 2),
                "deterministic_time": det_results.get('processing_time', 0),
                "llm_time": llm_results.get('processing_time', 0),
                "agent_time": agent_results.get('processing_time', 0),
                "speed_advantage": self._calculate_speed_advantage(det_results, llm_results)
            },
            "timestamp": time.time()
        }
        
        print(f"✅ Analysis complete in {total_time:.2f}s")
        return results
    
    def _parallel_analysis(self, review_text: str) -> tuple:
        """Run all analyses in parallel using ThreadPoolExecutor"""
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all tasks
            det_future = executor.submit(deterministic_analyze, review_text)
            llm_future = executor.submit(llm_analyze, review_text)
            agent_future = executor.submit(self.agent_coordinator.process_review, review_text)
            
            # Wait for all to complete
            det_results = det_future.result()
            llm_results = llm_future.result()
            agent_results = agent_future.result()
            
            return det_results, llm_results, agent_results
    
    def _sequential_analysis(self, review_text: str) -> tuple:
        """Run analyses sequentially"""
        
        print("📊 Running deterministic analysis...")
        det_results = deterministic_analyze(review_text)
        
        print("🧠 Running LLM analysis...")
        llm_results = llm_analyze(review_text)
        
        print("🤖 Running agent coordination...")
        agent_results = self.agent_coordinator.process_review(review_text)
        
        return det_results, llm_results, agent_results
    
    def _calculate_speed_advantage(self, det_results: Dict[str, Any], llm_results: Dict[str, Any]) -> str:
        """Calculate speed advantage of deterministic vs LLM"""
        
        det_time = det_results.get('processing_time', 0)
        llm_time = llm_results.get('processing_time', 0)
        
        if det_time > 0 and llm_time > 0:
            advantage = llm_time / det_time
            return f"Deterministic is {advantage:.1f}x faster"
        else:
            return "Unable to calculate speed advantage"
    
    def batch_process(self, reviews: list, parallel: bool = True) -> Dict[str, Any]:
        """
        Process multiple reviews
        
        Args:
            reviews: List of review texts
            parallel: Whether to use parallel processing
            
        Returns:
            Dict containing batch results
        """
        
        print(f"🔄 Processing {len(reviews)} reviews...")
        start_time = time.time()
        
        results = []
        errors = []
        
        for i, review in enumerate(reviews):
            try:
                result = self.process_review(review, parallel)
                results.append(result)
                print(f"✅ Review {i+1}/{len(reviews)} processed")
            except Exception as e:
                error_info = {
                    "review_index": i,
                    "error": str(e),
                    "review_text": review[:100] + "..." if len(review) > 100 else review
                }
                errors.append(error_info)
                print(f"❌ Review {i+1}/{len(reviews)} failed: {e}")
        
        total_time = time.time() - start_time
        
        # Aggregate statistics
        if results:
            avg_det_time = sum(r['performance']['deterministic_time'] for r in results) / len(results)
            avg_llm_time = sum(r['performance']['llm_time'] for r in results) / len(results)
            avg_agent_time = sum(r['performance']['agent_time'] for r in results) / len(results)
            total_det_time = sum(r['performance']['deterministic_time'] for r in results)
            total_llm_time = sum(r['performance']['llm_time'] for r in results)
        else:
            avg_det_time = avg_llm_time = avg_agent_time = total_det_time = total_llm_time = 0
        
        return {
            "batch_info": {
                "total_reviews": len(reviews),
                "successful": len(results),
                "failed": len(errors),
                "processing_mode": "parallel" if parallel else "sequential"
            },
            "performance": {
                "total_batch_time": round(total_time, 2),
                "avg_deterministic_time": round(avg_det_time, 3),
                "avg_llm_time": round(avg_llm_time, 2),
                "avg_agent_time": round(avg_agent_time, 2),
                "total_deterministic_time": round(total_det_time, 3),
                "total_llm_time": round(total_llm_time, 2)
            },
            "results": results,
            "errors": errors,
            "timestamp": time.time()
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status and capabilities"""
        
        return {
            "name": self.name,
            "version": self.version,
            "capabilities": self.capabilities,
            "status": "active",
            "environment": {
                "openai_api_configured": bool(os.getenv("OPENAI_API_KEY")),
                "openai_model": os.getenv("OPENAI_MODEL", "gpt-4")
            }
        }


def load_real_reviews():
    """Load real AppStore reviews for Skyeng app"""
    
    SKYENG_APP_ID = 1065290732
    
    print("🔄 Fetching real AppStore reviews for Skyeng...")
    
    try:
        # Initialize AppStore client
        client = AppStoreClient(SKYENG_APP_ID)
        
        # Fetch reviews
        print("📱 Connecting to AppStore API...")
        reviews = client.fetch_reviews(limit=20)
        
        if not reviews:
            print("⚠️  No reviews fetched from API, using sample data...")
            # Load sample reviews as fallback
            try:
                sample_reviews = client.load_reviews("data/reviews/skyeng_sample_reviews.json")
                return [review['content'] for review in sample_reviews]
            except:
                return [
                    "Great app! Easy to use and fast.",
                    "Terrible experience. App crashes all the time.",
                    "Good interface but needs more features.",
                    "Love the design but performance is slow."
                ]
        
        print(f"✅ Fetched {len(reviews)} real reviews")
        
        # Save to file with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"data/reviews/skyeng_real_reviews_{timestamp}.json"
        saved_file = client.save_reviews(reviews, output_file)
        print(f"💾 Reviews saved to: {saved_file}")
        
        # Extract review content for analysis
        review_texts = []
        for review in reviews:
            content = review.get('content', '').strip()
            if content and len(content) > 10:  # Filter out very short reviews
                review_texts.append(content)
        
        return review_texts[:15]  # Return up to 15 reviews for analysis
        
    except Exception as e:
        print(f"❌ Error fetching reviews: {e}")
        print("⚠️  Using sample data as fallback...")
        return [
            "Great app! Easy to use and fast.",
            "Terrible experience. App crashes all the time.", 
            "Good interface but needs more features.",
            "Love the design but performance is slow."
        ]


def main():
    """Main function - loads real reviews and analyzes them"""
    
    print("🚀 Starting Review Analysis Agent with Real Data...")
    
    try:
        # Initialize agent
        agent = ReviewAnalysisAgent()
        
        # Load real AppStore reviews
        print("\n" + "="*60)
        print("📱 LOADING REAL APPSTORE REVIEWS")
        print("="*60)
        
        real_reviews = load_real_reviews()
        
        if not real_reviews:
            print("❌ No reviews to analyze")
            return
        
        print(f"📊 Loaded {len(real_reviews)} reviews for analysis")
        
        # Show sample of loaded reviews
        print("\n📝 Sample reviews:")
        for i, review in enumerate(real_reviews[:3]):
            print(f"  {i+1}. {review[:100]}...")
        
        # Process all real reviews
        print("\n" + "="*60)
        print("🔄 ANALYZING REAL REVIEWS")
        print("="*60)
        
        batch_results = agent.batch_process(real_reviews, parallel=True)
        
        # Display comprehensive results
        print(f"\n📈 ANALYSIS RESULTS:")
        print(f"  - Total reviews processed: {batch_results['batch_info']['total_reviews']}")
        print(f"  - Successful: {batch_results['batch_info']['successful']}")
        print(f"  - Failed: {batch_results['batch_info']['failed']}")
        print(f"  - Total processing time: {batch_results['performance']['total_batch_time']}s")
        print(f"  - Avg deterministic time: {batch_results['performance']['avg_deterministic_time']}s")
        print(f"  - Avg LLM time: {batch_results['performance']['avg_llm_time']}s")
        
        # Generate summaries and comparisons
        print("\n" + "="*60)
        print("📋 GENERATING SUMMARIES AND COMPARISONS")
        print("="*60)
        
        # Generate deterministic summary
        print("🔢 Generating deterministic summary...")
        det_summary = generate_deterministic_summary(real_reviews)
        
        # Generate LLM summary
        print("🧠 Generating LLM summary...")
        llm_summary = generate_llm_summary(real_reviews)
        
        # Compare sentiment methods
        print("⚖️ Comparing sentiment analysis methods...")
        sentiment_comparison = compare_sentiment_methods(batch_results['results'])
        
        # Generate and save final comprehensive report
        successful_results = batch_results['results']
        if successful_results:
            # Save detailed report
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = f"reports/generated/comprehensive_analysis_{timestamp}.md"
            
            # Create reports directory if it doesn't exist
            os.makedirs("reports/generated", exist_ok=True)
            
            # Generate comprehensive report
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(f"# Skyeng AppStore Reviews - Comprehensive Analysis Report\n\n")
                f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Total Reviews Analyzed:** {len(successful_results)}\n")
                f.write(f"**Processing Time:** {batch_results['performance']['total_batch_time']}s\n\n")
                
                # Performance metrics
                f.write("## ⚡ Performance Metrics\n\n")
                f.write(f"- **Deterministic Analysis:** {batch_results['performance']['avg_deterministic_time']:.3f}s average\n")
                f.write(f"- **LLM Analysis:** {batch_results['performance']['avg_llm_time']:.2f}s average\n")
                f.write(f"- **Agent Analysis:** {batch_results['performance'].get('avg_agent_time', 0.0):.2f}s average\n")
                f.write(f"- **Speed Advantage:** Deterministic is ~{batch_results['performance']['avg_llm_time']/batch_results['performance']['avg_deterministic_time']:.0f}x faster than LLM\n\n")
                
                # Deterministic summary
                if 'error' not in det_summary:
                    f.write("## 🔢 ДЕТЕРМИНИСТИЧЕСКИЙ АНАЛИЗ\n\n")
                    f.write(f"{det_summary['summary_text']}\n\n")
                
                # LLM summary
                if 'error' not in llm_summary:
                    f.write("## 🧠 LLM АНАЛИЗ\n\n")
                    f.write(f"**Общее настроение:** {llm_summary.get('general_sentiment', 'unknown')}\n\n")
                    f.write(f"**Основные темы:** {', '.join(llm_summary.get('main_themes', []))}\n\n")
                    f.write(f"**Главные проблемы:** {', '.join(llm_summary.get('top_issues', []))}\n\n")
                    f.write(f"**Позитивные аспекты:** {', '.join(llm_summary.get('positive_highlights', []))}\n\n")
                    f.write(f"**Резюме:** {llm_summary.get('summary_text', 'Не сгенерировано')}\n\n")
                
                # Sentiment comparison
                if 'error' not in sentiment_comparison:
                    f.write("## ⚖️ СРАВНЕНИЕ МЕТОДОВ АНАЛИЗА НАСТРОЕНИЙ\n\n")
                    f.write(f"{sentiment_comparison['comparison_text']}\n\n")
                    
                    if sentiment_comparison['disagreements']:
                        f.write("### Примеры расхождений:\n\n")
                        for i, disagreement in enumerate(sentiment_comparison['disagreements'][:5]):
                            f.write(f"**Отзыв {i+1}:** {disagreement['review_preview']}\n")
                            f.write(f"- Детерминистический: {disagreement['deterministic']}\n")
                            f.write(f"- LLM: {disagreement['llm']}\n")
                            f.write(f"- Агенты: {disagreement['agent']}\n\n")
                
                # Individual review analysis (first 5)
                f.write("## 📝 Детальный анализ отзывов (первые 5)\n\n")
                for i, result in enumerate(successful_results[:5]):
                    f.write(f"### Отзыв {i+1}\n\n")
                    f.write(f"**Содержание:** {result['review_text'][:300]}...\n\n")
                    f.write(f"**Детерминистический:** {result['deterministic_results'].get('sentiment', 'unknown')}\n")
                    f.write(f"**LLM:** {result['llm_results'].get('sentiment', 'unknown')}\n")
                    f.write(f"**Агенты:** {result['agent_results'].get('sentiment_analysis', {}).get('sentiment', 'unknown')}\n\n")
                    f.write("---\n\n")
            
            print(f"✅ Comprehensive report saved to: {report_file}")
            
            # Display summary results
            print(f"\n📊 SUMMARY RESULTS:")
            if 'error' not in det_summary:
                print(f"  📈 Deterministic: {det_summary['sentiment_percentages']['positive']:.1f}% positive, {det_summary['sentiment_percentages']['negative']:.1f}% negative")
            
            if 'error' not in llm_summary:
                dist = llm_summary.get('sentiment_distribution', {})
                total = sum(dist.values()) if dist else 1
                pos_pct = (dist.get('positive_count', 0) / total) * 100 if total > 0 else 0
                neg_pct = (dist.get('negative_count', 0) / total) * 100 if total > 0 else 0
                print(f"  🧠 LLM: {pos_pct:.1f}% positive, {neg_pct:.1f}% negative")
            
            if 'error' not in sentiment_comparison:
                print(f"  ⚖️ Agreement: {sentiment_comparison['agreement_metrics']['exact_agreement_percentage']:.1f}% exact match between all methods")
            
        print(f"\n🎉 Analysis complete! Check the generated report for detailed insights.")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        print("Please check your .env file and ensure OPENAI_API_KEY is set")


if __name__ == "__main__":
    main()