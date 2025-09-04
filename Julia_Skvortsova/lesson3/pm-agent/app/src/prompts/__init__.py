"""
Prompt management system for PM Agent
"""
import os
from pathlib import Path
from typing import Dict
import structlog
from jinja2 import Environment, FileSystemLoader, Template

logger = structlog.get_logger()

class PromptLoader:
    """Utility for loading and managing prompt templates from markdown files"""
    
    def __init__(self, prompts_dir: Path = None):
        if prompts_dir is None:
            prompts_dir = Path(__file__).parent
        self.prompts_dir = prompts_dir
        self._cache: Dict[str, str] = {}
        
        # Initialize Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(prompts_dir)),
            # Use double braces for variables, preserving single braces for literal text
            variable_start_string='{{',
            variable_end_string='}}',
            # Don't auto-escape since we're working with markdown/text
            autoescape=False,
            # Keep trailing newlines
            keep_trailing_newline=True
        )
    
    def load_prompt(self, filename: str) -> str:
        """Load a prompt from a markdown file"""
        if filename in self._cache:
            return self._cache[filename]
        
        # Add .md extension if not provided
        if not filename.endswith('.md'):
            filename += '.md'
        
        prompt_path = self.prompts_dir / filename
        
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # Cache the prompt
            self._cache[filename] = content
            
            logger.debug("Loaded prompt", filename=filename, length=len(content))
            return content
            
        except Exception as e:
            logger.exception("Failed to load prompt", filename=filename, error=str(e))
            raise
    
    def format_prompt(self, filename: str, **kwargs) -> str:
        """Load and format a prompt template with variables using Jinja2"""
        # Add .md extension if not provided
        if not filename.endswith('.md'):
            filename += '.md'
        
        try:
            # Use Jinja2 to render the template
            template = self.jinja_env.get_template(filename)
            return template.render(**kwargs)
            
        except Exception as e:
            logger.error("Failed to render template", 
                        filename=filename, 
                        error=str(e),
                        available_vars=list(kwargs.keys()))
            raise
    
    
    def clear_cache(self):
        """Clear the prompt cache"""
        self._cache.clear()
        # Clear Jinja2 cache as well
        self.jinja_env.cache.clear()
        logger.debug("Prompt cache cleared")
    
    def list_prompts(self) -> list[str]:
        """List all available prompt files"""
        return [f.name for f in self.prompts_dir.glob('*.md')]
    
    def reload_prompt(self, filename: str) -> str:
        """Force reload a prompt from disk (bypassing cache)"""
        if not filename.endswith('.md'):
            filename += '.md'
        
        if filename in self._cache:
            del self._cache[filename]
        
        # Clear Jinja2 cache for this template
        self.jinja_env.cache.clear()
        
        return self.load_prompt(filename)

# Global prompt loader instance
_prompt_loader = None

def get_prompt_loader() -> PromptLoader:
    """Get the global prompt loader instance"""
    global _prompt_loader
    if _prompt_loader is None:
        _prompt_loader = PromptLoader()
    return _prompt_loader

def load_prompt(filename: str) -> str:
    """Convenience function to load a prompt"""
    return get_prompt_loader().load_prompt(filename)

def format_prompt(filename: str, **kwargs) -> str:
    """Convenience function to load and format a prompt"""
    return get_prompt_loader().format_prompt(filename, **kwargs)

# Prompt constants for easy importing
class ReviewClassifierPrompts:
    """Constants for review classifier prompt filenames"""
    INSTRUCTIONS = "instructions_review_classifier"
    WORKFLOW = "workflow_classification" 
    SINGLE_REVIEW = "task_classify_single_review"

class BugBotPrompts:
    """Constants for bug bot prompt filenames"""
    INSTRUCTIONS = "instructions_bug_bot"
    WORKFLOW = "workflow_bug_processing"
    STAGED_WORKFLOW = "workflow_staged_bug_processing"
    BUG_REPORT_TEMPLATE = "template_bug_report"
    DUPLICATE_CHECK = "task_check_issue_duplicate"
    DUPLICATE_COMMENT_TEMPLATE = "template_duplicate_issue_comment"

class BugApprovalJudgePrompts:
    """Constants for bug approval judge prompt filenames"""
    INSTRUCTIONS = "instructions_bug_approval_judge"
    ASSESSMENT_TASK = "task_assess_bug_submission"

class FeatureResearchBotPrompts:
    """Constants for feature research bot prompt filenames"""
    ORCHESTRATOR_INSTRUCTIONS = "instructions_feature_research_orchestrator"
    PLANNER_INSTRUCTIONS = "instructions_feature_research_planner"
    RESEARCHER_INSTRUCTIONS = "instructions_feature_web_researcher"
    ANALYST_INSTRUCTIONS = "instructions_feature_competitor_analyst"
    REPORTER_INSTRUCTIONS = "instructions_feature_spec_writer"
    RESEARCH_WORKFLOW = "workflow_feature_research"