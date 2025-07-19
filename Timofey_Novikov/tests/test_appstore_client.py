"""
Tests for AppStore API Client
Following TDD approach - write tests first, then implement
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
import os

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

class TestAppStoreClient:
    """Test AppStore API client functionality"""
    
    def test_client_initialization(self):
        """Test that client initializes with correct app_id"""
        from src.data.appstore_client import AppStoreClient
        
        client = AppStoreClient(app_id=1065290732)
        assert client.app_id == 1065290732
        assert client.base_url == "https://itunes.apple.com/rss/customerreviews"
    
    def test_fetch_reviews_returns_list(self):
        """Test that fetch_reviews returns a list of reviews"""
        from src.data.appstore_client import AppStoreClient
        
        client = AppStoreClient(app_id=1065290732)
        
        # Mock API response
        mock_response = {
            "feed": {
                "entry": [
                    {
                        "id": {"label": "test_id_1"},
                        "author": {"name": {"label": "TestUser"}},
                        "im:rating": {"label": "5"},
                        "title": {"label": "Great app"},
                        "content": {"label": "Love this app!"},
                        "updated": {"label": "2025-01-19T10:00:00Z"}
                    }
                ]
            }
        }
        
        with patch.object(client.session, 'get') as mock_get:
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            mock_get.return_value = mock_response_obj
            
            reviews = client.fetch_reviews(limit=1)
            
            assert isinstance(reviews, list)
            assert len(reviews) == 1
            assert reviews[0]['rating'] == 5
            assert reviews[0]['content'] == "Love this app!"
    
    def test_save_reviews_to_json(self):
        """Test saving reviews to JSON file"""
        from src.data.appstore_client import AppStoreClient
        
        client = AppStoreClient(app_id=1065290732)
        
        sample_reviews = [
            {
                "id": "test_1",
                "content": "Test review",
                "rating": 4,
                "date": "2025-01-19T10:00:00Z"
            }
        ]
        
        # Test file saving
        test_file = "test_reviews.json"
        client.save_reviews(sample_reviews, test_file)
        
        # Verify file exists and has correct content
        assert os.path.exists(test_file)
        
        with open(test_file, 'r') as f:
            saved_data = json.load(f)
            assert 'metadata' in saved_data
            assert 'reviews' in saved_data
            assert len(saved_data['reviews']) == 1
            assert saved_data['reviews'][0]['content'] == "Test review"
        
        # Cleanup
        os.remove(test_file)
    
    def test_handle_api_error(self):
        """Test handling of API errors"""
        from src.data.appstore_client import AppStoreClient
        
        client = AppStoreClient(app_id=1065290732)
        
        with patch.object(client.session, 'get') as mock_get:
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 404
            mock_get.return_value = mock_response_obj
            
            reviews = client.fetch_reviews()
            assert reviews == []  # Should return empty list on error
    
    def test_parse_review_data(self):
        """Test parsing individual review from API format"""
        from src.data.appstore_client import AppStoreClient
        
        client = AppStoreClient(app_id=1065290732)
        
        api_review = {
            "id": {"label": "12345"},
            "author": {"name": {"label": "TestUser"}},
            "im:rating": {"label": "3"},
            "title": {"label": "Okay app"},
            "content": {"label": "It's decent but has issues"},
            "updated": {"label": "2025-01-19T10:00:00Z"}
        }
        
        parsed = client._parse_review(api_review)
        
        assert parsed['id'] == "12345"
        assert parsed['author'] == "TestUser"
        assert parsed['rating'] == 3
        assert parsed['title'] == "Okay app"
        assert parsed['content'] == "It's decent but has issues"
        assert isinstance(parsed['date'], str)


class TestConfigManager:
    """Test configuration management"""
    
    def test_load_config(self):
        """Test loading configuration from JSON"""
        from src.config.config_manager import ConfigManager
        
        config = ConfigManager()
        
        assert config.get_app_id() == 1065290732
        assert config.get_app_name() == "Skyeng"
        assert config.get_max_reviews() > 0
    
    def test_config_validation(self):
        """Test that config values are valid"""
        from src.config.config_manager import ConfigManager
        
        config = ConfigManager()
        
        # Test required fields exist
        assert config.get_app_id() is not None
        assert config.get_storage_path() is not None
        assert len(config.get_supported_languages()) > 0


if __name__ == "__main__":
    pytest.main([__file__])