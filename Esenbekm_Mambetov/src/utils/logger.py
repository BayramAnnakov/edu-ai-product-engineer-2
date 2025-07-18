"""Logging configuration for the application."""

import logging
import sys
from typing import Optional


class Logger:
    """Centralized logging configuration."""
    
    @staticmethod
    def setup_logger(
        name: str = "mbank_analysis",
        level: int = logging.INFO,
        log_file: Optional[str] = None
    ) -> logging.Logger:
        """
        Set up application logger.
        
        Args:
            name: Logger name
            level: Logging level
            log_file: Optional log file path
            
        Returns:
            Configured logger
        """
        logger = logging.getLogger(name)
        
        # Avoid duplicate handlers
        if logger.handlers:
            return logger
        
        logger.setLevel(level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler (optional)
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    @staticmethod
    def get_logger(name: str = "mbank_analysis") -> logging.Logger:
        """Get existing logger or create new one."""
        return logging.getLogger(name)
    
    @staticmethod
    def log_analysis_start(app_id: str, review_count: int):
        """Log analysis start."""
        logger = Logger.get_logger()
        logger.info(f"Starting analysis for app: {app_id}, reviews: {review_count}")
    
    @staticmethod
    def log_analysis_complete(app_id: str, processing_time: float):
        """Log analysis completion."""
        logger = Logger.get_logger()
        logger.info(f"Analysis completed for app: {app_id}, time: {processing_time:.2f}s")
    
    @staticmethod
    def log_error(message: str, error: Exception):
        """Log error with exception details."""
        logger = Logger.get_logger()
        logger.error(f"{message}: {str(error)}", exc_info=True)
    
    @staticmethod
    def log_scraping_progress(current: int, total: int):
        """Log scraping progress."""
        logger = Logger.get_logger()
        logger.info(f"Scraping progress: {current}/{total} reviews")
    
    @staticmethod
    def log_file_operation(operation: str, file_path: str, success: bool):
        """Log file operation."""
        logger = Logger.get_logger()
        status = "success" if success else "failed"
        logger.info(f"File {operation} {status}: {file_path}")


# Initialize default logger
default_logger = Logger.setup_logger()