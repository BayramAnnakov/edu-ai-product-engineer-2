"""Data models for review analysis system."""

from dataclasses import dataclass
from typing import Dict, List, Any


@dataclass
class Review:
    """Structure for storing app review data."""
    id: str
    rating: int
    text: str
    author: str
    date: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert review to dictionary."""
        return {
            'id': self.id,
            'rating': self.rating,
            'text': self.text,
            'author': self.author,
            'date': self.date
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Review':
        """Create review from dictionary."""
        return cls(
            id=data.get('id', ''),
            rating=data.get('rating', 0),
            text=data.get('text', ''),
            author=data.get('author', ''),
            date=data.get('date', '')
        )


@dataclass
class ReviewsMetadata:
    """Metadata for scraped reviews."""
    app_id: str
    language: str
    country: str
    scraped_at: str
    total_reviews: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            'app_id': self.app_id,
            'language': self.language,
            'country': self.country,
            'scraped_at': self.scraped_at,
            'total_reviews': self.total_reviews
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReviewsMetadata':
        """Create metadata from dictionary."""
        return cls(
            app_id=data.get('app_id', ''),
            language=data.get('language', ''),
            country=data.get('country', ''),
            scraped_at=data.get('scraped_at', ''),
            total_reviews=data.get('total_reviews', 0)
        )


@dataclass
class ReviewsData:
    """Container for reviews and metadata."""
    reviews: List[Review]
    metadata: ReviewsMetadata
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert reviews data to dictionary."""
        return {
            'reviews': [review.to_dict() for review in self.reviews],
            'metadata': self.metadata.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReviewsData':
        """Create reviews data from dictionary."""
        reviews = [Review.from_dict(r) for r in data.get('reviews', [])]
        metadata = ReviewsMetadata.from_dict(data.get('metadata', {}))
        return cls(reviews=reviews, metadata=metadata)
    
    def get_reviews_by_rating(self, rating: int) -> List[Review]:
        """Filter reviews by rating."""
        return [review for review in self.reviews if review.rating == rating]
    
    def get_average_rating(self) -> float:
        """Calculate average rating."""
        if not self.reviews:
            return 0.0
        return sum(review.rating for review in self.reviews) / len(self.reviews)