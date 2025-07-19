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
from src.analyzers.deterministic import deterministic_analyze
from src.analyzers.llm_analyzer import llm_analyze
from src.reports.report_generator import generate_pm_report, export_report_json

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
            "report_generation",
            "parallel_processing"
        ]
        
        # Validate environment
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        print(f"✅ {self.name} v{self.version} initialized")
        print(f"📋 Capabilities: {', '.join(self.capabilities)}")
    
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
            # Run analyses in parallel
            det_results, llm_results = self._parallel_analysis(review_text)
        else:
            # Run analyses sequentially
            det_results, llm_results = self._sequential_analysis(review_text)
        
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
            "pm_report": pm_report,
            "json_export": json_export,
            "performance": {
                "total_processing_time": round(total_time, 2),
                "deterministic_time": det_results.get('processing_time', 0),
                "llm_time": llm_results.get('processing_time', 0),
                "speed_advantage": self._calculate_speed_advantage(det_results, llm_results)
            },
            "timestamp": time.time()
        }
        
        print(f"✅ Analysis complete in {total_time:.2f}s")
        return results
    
    def _parallel_analysis(self, review_text: str) -> tuple:
        """Run both analyses in parallel using ThreadPoolExecutor"""
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both tasks
            det_future = executor.submit(deterministic_analyze, review_text)
            llm_future = executor.submit(llm_analyze, review_text)
            
            # Wait for both to complete
            det_results = det_future.result()
            llm_results = llm_future.result()
            
            return det_results, llm_results
    
    def _sequential_analysis(self, review_text: str) -> tuple:
        """Run analyses sequentially"""
        
        print("📊 Running deterministic analysis...")
        det_results = deterministic_analyze(review_text)
        
        print("🧠 Running LLM analysis...")
        llm_results = llm_analyze(review_text)
        
        return det_results, llm_results
    
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
            total_det_time = sum(r['performance']['deterministic_time'] for r in results)
            total_llm_time = sum(r['performance']['llm_time'] for r in results)
        else:
            avg_det_time = avg_llm_time = total_det_time = total_llm_time = 0
        
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


def main():
    """Main function for testing the agent"""
    
    print("🚀 Starting Review Analysis Agent...")
    
    try:
        # Initialize agent
        agent = ReviewAnalysisAgent()
        
        # Test single review
        sample_review = """
        This app is amazing! The interface is so intuitive and easy to use. 
        However, I've noticed that it crashes sometimes when I try to upload large files. 
        The customer support is great though. Overall, I love this app but the crashing issue needs to be fixed.
        """
        
        print("\n" + "="*50)
        print("🧪 Testing Single Review Analysis")
        print("="*50)
        
        results = agent.process_review(sample_review)
        
        if "error" in results:
            print(f"❌ Error: {results['error']}")
            return
        
        # Display results
        print(f"📊 Processing completed in {results['performance']['total_processing_time']}s")
        print(f"⚡ Speed advantage: {results['performance']['speed_advantage']}")
        print(f"🎯 Deterministic sentiment: {results['deterministic_results'].get('sentiment', 'unknown')}")
        print(f"🧠 LLM sentiment: {results['llm_results'].get('sentiment', 'unknown')}")
        
        # Show part of the report
        print("\n📋 PM Report Preview:")
        print(results['pm_report'][:500] + "..." if len(results['pm_report']) > 500 else results['pm_report'])
        
        # Test batch processing
        print("\n" + "="*50)
        print("🔄 Testing Batch Processing")
        print("="*50)
        
        sample_reviews = [
            "Great app! Easy to use and fast.",
            "Terrible experience. App crashes all the time.",
            "Good interface but needs more features.",
            "Love the design but performance is slow."
        ]
        
        batch_results = agent.batch_process(sample_reviews, parallel=True)
        
        print(f"📈 Batch Results:")
        print(f"  - Total reviews: {batch_results['batch_info']['total_reviews']}")
        print(f"  - Successful: {batch_results['batch_info']['successful']}")
        print(f"  - Failed: {batch_results['batch_info']['failed']}")
        print(f"  - Total time: {batch_results['performance']['total_batch_time']}s")
        print(f"  - Avg deterministic time: {batch_results['performance']['avg_deterministic_time']}s")
        print(f"  - Avg LLM time: {batch_results['performance']['avg_llm_time']}s")
        
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        print("Please check your .env file and ensure OPENAI_API_KEY is set")


if __name__ == "__main__":
    main()