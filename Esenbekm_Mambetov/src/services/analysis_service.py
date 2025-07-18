"""Main analysis service that orchestrates the entire review analysis process."""

from typing import Optional

from ..models.review import ReviewsData
from ..models.summary import ComparisonResult
from ..services.scraper_service import ScraperService
from ..services.summarization_service import ExtractiveService, AbstractiveService, ComparisonService
from ..services.data_service import DataService
from ..config.settings import AppConfig
from ..utils.logger import Logger


class AnalysisService:
    """Main service for orchestrating the review analysis process."""
    
    def __init__(self, openai_api_key: str):
        """
        Initialize analysis service.
        
        Args:
            openai_api_key: OpenAI API key for abstractive summarization
        """
        self.openai_api_key = openai_api_key
        self.extractive_service = ExtractiveService()
        self.abstractive_service = AbstractiveService(openai_api_key)
        self.comparison_service = ComparisonService()
        self.data_service = DataService()
        self.logger = Logger.get_logger()
    
    def analyze_app_reviews(
        self,
        app_id: str,
        review_count: int = AppConfig.DEFAULT_REVIEW_COUNT,
        save_reviews: bool = True,
        reviews_file: str = AppConfig.DEFAULT_REVIEWS_FILE,
        results_file: str = AppConfig.DEFAULT_RESULTS_FILE
    ) -> ComparisonResult:
        """
        Complete analysis workflow for app reviews.
        
        Args:
            app_id: Google Play Store app ID
            review_count: Number of reviews to analyze
            save_reviews: Whether to save scraped reviews
            reviews_file: File path to save reviews
            results_file: File path to save results
            
        Returns:
            ComparisonResult object
        """
        self.logger.info(f"Starting complete analysis workflow for app: {app_id}")
        self.logger.info(f"Parameters: review_count={review_count}, save_reviews={save_reviews}")
        
        # Step 1: Scrape reviews
        self.logger.info("Step 1/6: Scraping reviews from Google Play Store")
        scraper = ScraperService(app_id)
        reviews_data = scraper.scrape_reviews(count=review_count)
        
        if not reviews_data.reviews:
            self.logger.error("No reviews found for the specified app")
            raise ValueError("No reviews found for the specified app")
        
        self.logger.info(f"Successfully scraped {len(reviews_data.reviews)} reviews")
        
        # Step 2: Save reviews if requested
        if save_reviews:
            self.logger.info(f"Step 2/6: Saving reviews to {reviews_file}")
            success = self.data_service.save_reviews_data(reviews_data, reviews_file)
            if success:
                self.logger.info("Reviews saved successfully")
            else:
                self.logger.warning("Failed to save reviews")
        else:
            self.logger.info("Step 2/6: Skipping review save")
        
        # Step 3: Generate summaries
        self.logger.info("Step 3/6: Generating extractive summary")
        extractive_summary = self.extractive_service.summarize(reviews_data.reviews)
        self.logger.info(f"Extractive summary generated: {extractive_summary.word_count} words, {extractive_summary.processing_time:.2f}s")
        
        self.logger.info("Step 4/6: Generating abstractive summary with GPT-4")
        abstractive_summary = self.abstractive_service.summarize(reviews_data.reviews)
        self.logger.info(f"Abstractive summary generated: {abstractive_summary.word_count} words, {abstractive_summary.processing_time:.2f}s")
        
        # Step 4: Evaluate summaries
        self.logger.info("Step 5/6: Evaluating and comparing summaries")
        evaluation_report = self.abstractive_service.evaluate_summaries(
            extractive_summary, abstractive_summary
        )
        
        # Step 5: Create comparison result
        self.logger.info("Creating comparison metrics")
        comparison_result = self.comparison_service.create_comparison_result(
            extractive_summary, abstractive_summary, evaluation_report
        )
        
        self.logger.info("Comparison metrics calculated:")
        self.logger.info(f"  - Content overlap: {comparison_result.comparison_metrics.content_overlap:.3f}")
        self.logger.info(f"  - Length ratio: {comparison_result.comparison_metrics.length_ratio:.3f}")
        self.logger.info(f"  - Readability score: {comparison_result.comparison_metrics.readability_score:.3f}")
        
        # Step 6: Save results
        self.logger.info(f"Step 6/6: Saving results to {results_file}")
        success = self.data_service.save_results_data(comparison_result, results_file)
        if success:
            self.logger.info("Results saved successfully")
        else:
            self.logger.warning("Failed to save results")
        
        self.logger.info("Analysis workflow completed successfully")
        return comparison_result
    
    def analyze_existing_reviews(
        self,
        reviews_data: ReviewsData,
        results_file: str = AppConfig.DEFAULT_RESULTS_FILE
    ) -> ComparisonResult:
        """
        Analyze already scraped reviews.
        
        Args:
            reviews_data: ReviewsData object with reviews
            results_file: File path to save results
            
        Returns:
            ComparisonResult object
        """
        if not reviews_data.reviews:
            raise ValueError("No reviews provided for analysis")
        
        # Generate summaries
        extractive_summary = self.extractive_service.summarize(reviews_data.reviews)
        abstractive_summary = self.abstractive_service.summarize(reviews_data.reviews)
        
        # Evaluate summaries
        evaluation_report = self.abstractive_service.evaluate_summaries(
            extractive_summary, abstractive_summary
        )
        
        # Create comparison result
        comparison_result = self.comparison_service.create_comparison_result(
            extractive_summary, abstractive_summary, evaluation_report
        )
        
        # Save results
        self.data_service.save_results_data(comparison_result, results_file)
        
        return comparison_result
    
    def validate_setup(self) -> bool:
        """
        Validate that the service is properly configured.
        
        Returns:
            True if setup is valid, False otherwise
        """
        try:
            # Test OpenAI connection
            test_reviews = []
            self.abstractive_service.summarize(test_reviews)
            return True
        except Exception:
            return False
    
    @staticmethod
    def load_existing_data(
        reviews_file: str = AppConfig.DEFAULT_REVIEWS_FILE,
        results_file: str = AppConfig.DEFAULT_RESULTS_FILE
    ) -> tuple[Optional[ReviewsData], Optional[ComparisonResult]]:
        """
        Load existing data files.
        
        Args:
            reviews_file: Path to reviews file
            results_file: Path to results file
            
        Returns:
            Tuple of (ReviewsData, ComparisonResult) or (None, None)
        """
        data_service = DataService()
        
        reviews_data = None
        results_data = None
        
        if data_service.file_exists(reviews_file):
            reviews_data = data_service.load_reviews_data(reviews_file)
        
        if data_service.file_exists(results_file):
            results_data = data_service.load_results_data(results_file)
        
        return reviews_data, results_data
    
    def get_analysis_summary(self, comparison_result: ComparisonResult) -> dict:
        """
        Get a summary of analysis results.
        
        Args:
            comparison_result: ComparisonResult object
            
        Returns:
            Dictionary with analysis summary
        """
        return {
            'extractive_word_count': comparison_result.extractive_summary.word_count,
            'abstractive_word_count': comparison_result.abstractive_summary.word_count,
            'extractive_processing_time': comparison_result.extractive_summary.processing_time,
            'abstractive_processing_time': comparison_result.abstractive_summary.processing_time,
            'content_overlap': comparison_result.comparison_metrics.content_overlap,
            'length_ratio': comparison_result.comparison_metrics.length_ratio,
            'readability_score': comparison_result.comparison_metrics.readability_score,
            'preferred_summary': comparison_result.evaluation_report.get_preferred_summary(),
            'evaluation_reasoning': comparison_result.evaluation_report.get_reasoning()
        }