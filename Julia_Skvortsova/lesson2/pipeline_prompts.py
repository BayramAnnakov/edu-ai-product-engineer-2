"""Prompt management for the pipeline"""
from pathlib import Path
from typing import Any
import re


class PromptManager:
    """Manages prompt templates and parameter substitution"""
    
    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = Path(prompts_dir)
        
    def load_prompt(self, filename: str) -> str:
        """Load a prompt template from file"""
        filepath = self.prompts_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Prompt file not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    
    def format_prompt(self, template: str, **params: Any) -> str:
        """Replace {{PARAM}} placeholders in template"""
        formatted = template
        
        for key, value in params.items():
            # Handle different value types
            if isinstance(value, (list, dict)):
                value_str = str(value)
            elif value is None:
                value_str = ""
            else:
                value_str = str(value)
            
            # Replace all occurrences of {{KEY}}
            pattern = f"{{{{{key}}}}}"
            formatted = formatted.replace(pattern, value_str)
        
        # Check for any remaining placeholders
        remaining = re.findall(r'\{\{(\w+)\}\}', formatted)
        if remaining:
            raise ValueError(f"Unsubstituted parameters in prompt: {remaining}")
        
        return formatted
    
    def get_prompt(self, filename: str, **params: Any) -> str:
        """Load and format a prompt in one step"""
        template = self.load_prompt(filename)
        return self.format_prompt(template, **params)