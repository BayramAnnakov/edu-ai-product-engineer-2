"""Google Play Store scraping service."""

from typing import Optional
from datetime import datetime

from google_play_scraper import app, reviews, Sort

from ..models.review import Review, ReviewsData, ReviewsMetadata
from ..config.settings import AppConfig
from ..utils.logger import Logger


class ScraperService:
    """Service for scraping Google Play Store reviews."""
    
    def __init__(self, app_id: str):
        """
        Initialize scraper service.
        
        Args:
            app_id: Google Play Store app ID
        """
        self.app_id = app_id
        self.logger = Logger.get_logger()
    
    def scrape_reviews(
        self, 
        count: Optional[int] = None, 
        lang: str = AppConfig.DEFAULT_LANGUAGE,
        country: str = AppConfig.DEFAULT_COUNTRY
    ) -> ReviewsData:
        """
        Scrape reviews from Google Play Store.
        
        Args:
            count: Number of reviews to scrape (None for all available)
            lang: Language code
            country: Country code
            
        Returns:
            ReviewsData object containing reviews and metadata
        """
        try:
            self.logger.info(f"Starting review scraping for app: {self.app_id}")
            self.logger.info(f"Target count: {count}, language: {lang}, country: {country}")
            
            # Get app info first
            self.logger.info("Fetching app information...")
            app_info = app(self.app_id, lang=lang, country=country)
            app_title = app_info.get('title', 'Unknown App')
            self.logger.info(f"App found: {app_title}")
            
            all_reviews = []
            continuation_token = None
            batch_size = AppConfig.BATCH_SIZE
            
            # If count is specified and small, use single batch
            if count and count <= batch_size:
                self.logger.info(f"Using single batch mode for {count} reviews")
                result, _ = reviews(
                    self.app_id,
                    lang=lang,
                    country=country,
                    sort=Sort.NEWEST,
                    count=count
                )
                all_reviews.extend(result)
                self.logger.info(f"Fetched {len(result)} reviews in single batch")
            else:
                # Use pagination for larger counts
                target_count = count or AppConfig.MAX_REVIEWS_LIMIT
                self.logger.info(f"Using pagination mode for {target_count} reviews")
                
                batch_number = 1
                while len(all_reviews) < target_count:
                    remaining = target_count - len(all_reviews)
                    batch_count = min(batch_size, remaining)
                    
                    self.logger.info(f"Fetching batch {batch_number}: {batch_count} reviews (total so far: {len(all_reviews)})")
                    
                    result, continuation_token = reviews(
                        self.app_id,
                        lang=lang,
                        country=country,
                        sort=Sort.NEWEST,
                        count=batch_count,
                        continuation_token=continuation_token
                    )
                    
                    if not result:
                        self.logger.warning(f"No more reviews available after batch {batch_number}")
                        break
                    
                    all_reviews.extend(result)
                    self.logger.info(f"Batch {batch_number} completed: {len(result)} reviews fetched")
                    
                    if not continuation_token:
                        self.logger.info("No continuation token, reached end of available reviews")
                        break
                    
                    batch_number += 1
            
            self.logger.info(f"Scraping completed. Total reviews fetched: {len(all_reviews)}")
            self.logger.info("Starting review parsing and validation...")
            
            # Convert to Review objects with detailed logging
            review_objects = []
            processed_count = 0
            invalid_count = 0
            
            for i, review_data in enumerate(all_reviews):
                try:
                    # Parse date safely
                    review_date = review_data.get('at')
                    formatted_date = review_date.strftime('%Y-%m-%d') if review_date else ''
                    
                    # Create review object
                    review = Review(
                        id=review_data.get('reviewId', str(i)),
                        rating=review_data.get('score', 0),
                        text=review_data.get('content', ''),
                        author=review_data.get('userName', 'Anonymous'),
                        date=formatted_date
                    )
                    
                    # Validate review
                    if review.text.strip() and review.rating > 0:
                        review_objects.append(review)
                        processed_count += 1
                        
                        # Log progress every 10 reviews
                        if processed_count % 10 == 0:
                            self.logger.info(f"Processed {processed_count}/{len(all_reviews)} reviews")
                    else:
                        invalid_count += 1
                        self.logger.warning(f"Skipping invalid review {i}: empty text or invalid rating")
                        
                except Exception as e:
                    invalid_count += 1
                    self.logger.error(f"Error parsing review {i}: {e}")
            
            self.logger.info("Review parsing completed:")
            self.logger.info(f"  - Valid reviews: {len(review_objects)}")
            self.logger.info(f"  - Invalid reviews: {invalid_count}")
            self.logger.info(f"  - Success rate: {len(review_objects)/len(all_reviews)*100:.1f}%")
            
            # Create metadata
            metadata = ReviewsMetadata(
                app_id=self.app_id,
                language=lang,
                country=country,
                scraped_at=datetime.now().isoformat(),
                total_reviews=len(review_objects)
            )
            
            self.logger.info("Review scraping and parsing completed successfully")
            return ReviewsData(reviews=review_objects, metadata=metadata)
            
        except Exception as e:
            # Log error and return empty data
            self.logger.error(f"Failed to scrape reviews: {e}")
            self.logger.error(f"App ID: {self.app_id}, Count: {count}")
            
            metadata = ReviewsMetadata(
                app_id=self.app_id,
                language=lang,
                country=country,
                scraped_at=datetime.now().isoformat(),
                total_reviews=0
            )
            return ReviewsData(reviews=[], metadata=metadata)
    
    def get_app_info(self, lang: str = AppConfig.DEFAULT_LANGUAGE) -> dict:
        """
        Get app information from Google Play Store.
        
        Args:
            lang: Language code
            
        Returns:
            App information dictionary
        """
        try:
            return app(self.app_id, lang=lang)
        except Exception:
            return {}
    
    def validate_app_id(self) -> bool:
        """
        Validate if app ID exists on Google Play Store.
        
        Returns:
            True if app exists, False otherwise
        """
        try:
            app(self.app_id)
            return True
        except Exception:
            return False