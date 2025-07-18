#!/usr/bin/env python3
"""
Main entry point for MBank Reviews Analysis System.
Command-line interface for running analysis without the dashboard.
"""

import argparse
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.config.settings import AppConfig
from src.services.analysis_service import AnalysisService
from src.services.data_service import DataService
from src.utils.logger import Logger


def run_analysis(args):
    """Run complete analysis workflow."""
    logger = Logger.setup_logger()
    
    if not args.openai_key:
        logger.error("OpenAI API key is required")
        sys.exit("Error: OpenAI API key is required. Use --openai-key or set OPENAI_API_KEY environment variable.")
    
    try:
        logger.info(f"Starting analysis for app: {args.app_id}")
        
        # Initialize analysis service
        analysis_service = AnalysisService(args.openai_key)
        
        # Run analysis
        results = analysis_service.analyze_app_reviews(
            app_id=args.app_id,
            review_count=args.count,
            save_reviews=True,
            reviews_file=args.reviews_output,
            results_file=args.results_output
        )
        
        # Display summary
        summary = analysis_service.get_analysis_summary(results)
        
        print("\n" + "="*60)
        print("📊 ANALYSIS COMPLETE")
        print("="*60)
        print(f"📱 App ID: {args.app_id}")
        print(f"📊 Reviews analyzed: {args.count}")
        print(f"💾 Reviews saved to: {args.reviews_output}")
        print(f"💾 Results saved to: {args.results_output}")
        print()
        print("📝 SUMMARY COMPARISON:")
        print(f"  • Extractive summary: {summary['extractive_word_count']} words")
        print(f"  • Abstractive summary: {summary['abstractive_word_count']} words")
        print(f"  • Content overlap: {summary['content_overlap']:.3f}")
        print(f"  • Length ratio: {summary['length_ratio']:.3f}")
        print(f"  • Readability score: {summary['readability_score']:.3f}")
        print(f"  • Preferred summary: {summary['preferred_summary']}")
        print()
        print("⏱️ PROCESSING TIME:")
        print(f"  • Extractive: {summary['extractive_processing_time']:.2f}s")
        print(f"  • Abstractive: {summary['abstractive_processing_time']:.2f}s")
        print("="*60)
        
        logger.info("Analysis completed successfully")
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        sys.exit(f"Error: Analysis failed - {e}")


def analyze_existing(args):
    """Analyze existing reviews data."""
    logger = Logger.setup_logger()
    
    if not args.openai_key:
        logger.error("OpenAI API key is required")
        sys.exit("Error: OpenAI API key is required")
    
    if not Path(args.reviews_file).exists():
        logger.error(f"Reviews file not found: {args.reviews_file}")
        sys.exit(f"Error: Reviews file not found: {args.reviews_file}")
    
    try:
        logger.info(f"Analyzing existing reviews from: {args.reviews_file}")
        
        # Load reviews data
        data_service = DataService()
        reviews_data = data_service.load_reviews_data(args.reviews_file)
        
        if not reviews_data:
            sys.exit("Error: Failed to load reviews data")
        
        # Initialize analysis service
        analysis_service = AnalysisService(args.openai_key)
        
        # Run analysis
        analysis_service.analyze_existing_reviews(
            reviews_data=reviews_data,
            results_file=args.results_output
        )
        
        print(f"\n✅ Analysis complete! Results saved to: {args.results_output}")
        logger.info("Analysis completed successfully")
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        sys.exit(f"Error: Analysis failed - {e}")


def validate_setup(args):
    """Validate system setup."""
    if not args.openai_key:
        print("❌ OpenAI API key not provided")
        return False
    
    try:
        analysis_service = AnalysisService(args.openai_key)
        if analysis_service.validate_setup():
            print("✅ System setup is valid")
            return True
        else:
            print("❌ System setup validation failed")
            return False
    except Exception as e:
        print(f"❌ Setup validation error: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="MBank Reviews Analysis System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full analysis
  python main_refactored.py analyze --app-id com.example.app --count 100 --openai-key your_key

  # Analyze existing reviews
  python main_refactored.py analyze-existing --reviews-file reviews.json --openai-key your_key

  # Validate setup
  python main_refactored.py validate --openai-key your_key
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Run complete analysis')
    analyze_parser.add_argument(
        '--app-id', 
        default=AppConfig.DEFAULT_APP_ID,
        help=f'Google Play Store app ID (default: {AppConfig.DEFAULT_APP_ID})'
    )
    analyze_parser.add_argument(
        '--count', 
        type=int, 
        default=AppConfig.DEFAULT_REVIEW_COUNT,
        help=f'Number of reviews to analyze (default: {AppConfig.DEFAULT_REVIEW_COUNT})'
    )
    analyze_parser.add_argument(
        '--openai-key',
        default=os.getenv('OPENAI_API_KEY'),
        help='OpenAI API key (or set OPENAI_API_KEY env var)'
    )
    analyze_parser.add_argument(
        '--reviews-output',
        default=AppConfig.DEFAULT_REVIEWS_FILE,
        help=f'Output file for reviews (default: {AppConfig.DEFAULT_REVIEWS_FILE})'
    )
    analyze_parser.add_argument(
        '--results-output',
        default=AppConfig.DEFAULT_RESULTS_FILE,
        help=f'Output file for results (default: {AppConfig.DEFAULT_RESULTS_FILE})'
    )
    
    # Analyze existing command
    existing_parser = subparsers.add_parser('analyze-existing', help='Analyze existing reviews')
    existing_parser.add_argument(
        '--reviews-file',
        required=True,
        help='Path to existing reviews JSON file'
    )
    existing_parser.add_argument(
        '--openai-key',
        default=os.getenv('OPENAI_API_KEY'),
        help='OpenAI API key (or set OPENAI_API_KEY env var)'
    )
    existing_parser.add_argument(
        '--results-output',
        default=AppConfig.DEFAULT_RESULTS_FILE,
        help=f'Output file for results (default: {AppConfig.DEFAULT_RESULTS_FILE})'
    )
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate system setup')
    validate_parser.add_argument(
        '--openai-key',
        default=os.getenv('OPENAI_API_KEY'),
        help='OpenAI API key (or set OPENAI_API_KEY env var)'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    if args.command == 'analyze':
        run_analysis(args)
    elif args.command == 'analyze-existing':
        analyze_existing(args)
    elif args.command == 'validate':
        validate_setup(args)


if __name__ == "__main__":
    main()