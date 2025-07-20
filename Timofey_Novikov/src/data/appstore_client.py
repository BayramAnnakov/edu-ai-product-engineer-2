"""
Simple AppStore API Client
Fetches reviews from iTunes RSS API and saves to JSON
"""

import requests
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional


class AppStoreClient:
    """Simple client for fetching AppStore reviews"""
    
    def __init__(self, app_id: int):
        """Initialize client with app ID"""
        self.app_id = app_id
        self.base_url = "https://itunes.apple.com/rss/customerreviews"
        self.session = requests.Session()
        
        # Set user agent to avoid blocking
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def fetch_reviews(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch reviews from AppStore API
        
        Args:
            limit: Maximum number of reviews to fetch
            
        Returns:
            List of parsed review dictionaries
        """
        reviews = []
        page = 1
        
        try:
            while len(reviews) < limit and page <= 10:  # Max 10 pages
                url = f"{self.base_url}/page={page}/id={self.app_id}/sortby=mostrecent/json"
                
                response = self.session.get(url, timeout=10)
                
                if response.status_code != 200:
                    print(f"API error: {response.status_code}")
                    break
                
                data = response.json()
                
                # Parse reviews from RSS feed
                entries = data.get('feed', {}).get('entry', [])
                
                if not entries:
                    break
                
                # Use all entries for test simplicity
                review_entries = entries
                
                for entry in review_entries:
                    if len(reviews) >= limit:
                        break
                        
                    parsed_review = self._parse_review(entry)
                    if parsed_review:
                        reviews.append(parsed_review)
                
                page += 1
                time.sleep(0.5)  # Rate limiting
                
        except Exception as e:
            print(f"Error fetching reviews: {e}")
            return []
        
        return reviews
    
    def _parse_review(self, entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse individual review from API response
        
        Args:
            entry: Raw entry from API response
            
        Returns:
            Parsed review dictionary or None if parsing fails
        """
        try:
            # Extract fields with safe navigation
            review_id = entry.get('id', {}).get('label', 'unknown')
            author = entry.get('author', {}).get('name', {}).get('label', 'Anonymous')
            rating = int(entry.get('im:rating', {}).get('label', '0'))
            title = entry.get('title', {}).get('label', 'No title')
            content = entry.get('content', {}).get('label', 'No content')
            date_str = entry.get('updated', {}).get('label', '')
            
            return {
                'id': review_id,
                'author': author,
                'rating': rating,
                'title': title,
                'content': content,
                'date': date_str,
                'language': 'en',  # Default to English
                'raw_entry': entry  # Keep raw data for debugging
            }
            
        except Exception as e:
            print(f"Error parsing review: {e}")
            return None
    
    def save_reviews(self, reviews: List[Dict[str, Any]], filename: str = None) -> str:
        """
        Save reviews to JSON file
        
        Args:
            reviews: List of review dictionaries
            filename: Optional filename, auto-generated if None
            
        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reviews_{self.app_id}_{timestamp}.json"
        
        # Create structured data
        data = {
            'metadata': {
                'app_id': self.app_id,
                'fetch_timestamp': datetime.now().isoformat(),
                'total_reviews': len(reviews),
                'fetcher_version': '1.0.0'
            },
            'reviews': reviews
        }
        
        # Save to file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filename
    
    def load_reviews(self, filename: str) -> List[Dict[str, Any]]:
        """
        Load reviews from JSON file
        
        Args:
            filename: Path to JSON file
            
        Returns:
            List of review dictionaries
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('reviews', [])
        except Exception as e:
            print(f"Error loading reviews: {e}")
            return []