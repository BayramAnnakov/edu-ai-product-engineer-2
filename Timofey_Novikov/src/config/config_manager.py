"""
Simple Configuration Manager
Loads settings from JSON config file
"""

import json
import os
from typing import Dict, Any, List


class ConfigManager:
    """Simple configuration manager for app settings"""
    
    def __init__(self, config_path: str = None):
        """Initialize config manager with path to config file"""
        if config_path is None:
            # Default to config/app_settings.json relative to project root
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            config_path = os.path.join(current_dir, "config", "app_settings.json")
        
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
    
    def get_app_id(self) -> int:
        """Get target app ID"""
        return self.config['appstore']['target_app_id']
    
    def get_app_name(self) -> str:
        """Get app name"""
        return self.config['appstore']['app_name']
    
    def get_max_reviews(self) -> int:
        """Get maximum number of reviews to fetch"""
        return self.config['appstore']['data_sources']['reviews_per_fetch']
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        return self.config['appstore']['data_sources']['supported_languages']
    
    def get_storage_path(self) -> str:
        """Get storage directory path"""
        return self.config['appstore']['storage']['data_directory']
    
    def get_openai_model(self) -> str:
        """Get OpenAI model name"""
        return self.config['analysis']['agents']['openai_model']
    
    def is_deterministic_enabled(self) -> bool:
        """Check if deterministic analysis is enabled"""
        return self.config['analysis']['deterministic']['enabled']
    
    def is_agents_enabled(self) -> bool:
        """Check if agents analysis is enabled"""
        return self.config['analysis']['agents']['enabled']