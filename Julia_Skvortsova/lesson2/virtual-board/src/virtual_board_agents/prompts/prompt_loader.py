"""
Markdown-based prompt loader for Virtual Board agents
"""
import json
from typing import Dict, Any
from pathlib import Path


class MarkdownPromptLoader:
    """Load prompts from markdown files with template variable substitution"""
    
    def __init__(self):
        self.prompts_dir = Path(__file__).parent
        self.agents_dir = self.prompts_dir / "agents"
        self.analysis_dir = self.prompts_dir / "analysis"
    
    def _load_markdown_file(self, file_path: Path) -> str:
        """Load content from a markdown file"""
        if not file_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _substitute_variables(self, template: str, variables: Dict[str, Any]) -> str:
        """Substitute template variables in the format {{variable_name}}"""
        result = template
        
        for key, value in variables.items():
            # Handle different value types
            if isinstance(value, (list, dict)):
                # Convert to JSON for complex types
                value_str = json.dumps(value, default=str)
            else:
                value_str = str(value)
            
            # Replace {{key}} with value
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, value_str)
        
        return result
    
    def load_agent_instructions(self, agent_type: str, **kwargs) -> str:
        """Load agent instructions from markdown file"""
        file_path = self.agents_dir / f"{agent_type}.md"
        template = self._load_markdown_file(file_path)
        return self._substitute_variables(template, kwargs)
    
    def load_analysis_prompt(self, prompt_type: str, **kwargs) -> str:
        """Load analysis prompt from markdown file"""
        file_path = self.analysis_dir / f"{prompt_type}.md"
        template = self._load_markdown_file(file_path)
        return self._substitute_variables(template, kwargs)


# Global instance
_loader = MarkdownPromptLoader()


# Convenience functions
def load_agent_instructions(agent_type: str, **kwargs) -> str:
    """Load agent instructions from markdown"""
    return _loader.load_agent_instructions(agent_type, **kwargs)


def load_analysis_prompt(prompt_type: str, **kwargs) -> str:
    """Load analysis prompt from markdown"""
    return _loader.load_analysis_prompt(prompt_type, **kwargs)