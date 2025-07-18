"""Data loading and saving services."""

import json
import tempfile
import os
from typing import Dict, Any, Optional
from pathlib import Path

from ..models.review import ReviewsData
from ..models.summary import ComparisonResult
from ..config.settings import AppConfig


class DataService:
    """Service for loading and saving application data."""
    
    @staticmethod
    def ensure_results_dir():
        """Ensure the results directory exists."""
        results_dir = Path(AppConfig.RESULTS_DIR)
        results_dir.mkdir(exist_ok=True)
    
    @staticmethod
    def load_reviews_data(file_path: str) -> Optional[ReviewsData]:
        """
        Load reviews data from JSON file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            ReviewsData object or None if error
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return ReviewsData.from_dict(data)
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return None
    
    @staticmethod
    def save_reviews_data(reviews_data: ReviewsData, file_path: str) -> bool:
        """
        Save reviews data to JSON file.
        
        Args:
            reviews_data: ReviewsData object to save
            file_path: Path to save the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure results directory exists
            DataService.ensure_results_dir()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(reviews_data.to_dict(), f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    
    @staticmethod
    def load_results_data(file_path: str) -> Optional[ComparisonResult]:
        """
        Load analysis results from JSON file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            ComparisonResult object or None if error
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return ComparisonResult.from_dict(data)
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return None
    
    @staticmethod
    def save_results_data(results: ComparisonResult, file_path: str) -> bool:
        """
        Save analysis results to JSON file.
        
        Args:
            results: ComparisonResult object to save
            file_path: Path to save the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure results directory exists
            DataService.ensure_results_dir()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(results.to_dict(), f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    
    @staticmethod
    def load_from_uploaded_file(uploaded_file) -> Optional[Dict[str, Any]]:
        """
        Load data from Streamlit uploaded file.
        
        Args:
            uploaded_file: Streamlit UploadedFile object
            
        Returns:
            Parsed JSON data or None if error
        """
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                f.write(uploaded_file.getvalue().decode())
                temp_path = f.name
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            os.unlink(temp_path)
            return data
        except Exception:
            return None
    
    @staticmethod
    def file_exists(file_path: str) -> bool:
        """Check if file exists."""
        return Path(file_path).exists()
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """Get file size in bytes."""
        try:
            return Path(file_path).stat().st_size
        except (FileNotFoundError, OSError):
            return 0