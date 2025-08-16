"""
Jinja2 template renderer for Slack messages
"""
import json
from pathlib import Path
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader, Template
import structlog

logger = structlog.get_logger()


class TemplateRenderer:
    """Renders Jinja2 templates for Slack messages"""
    
    def __init__(self, templates_path: str = None):
        if templates_path is None:
            # Default to templates directory relative to this file
            current_dir = Path(__file__).parent
            templates_path = current_dir / "templates"
        
        self.templates_path = Path(templates_path)
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_path)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        self.env.filters['strftime'] = self._strftime_filter
        
        logger.info(
            "Template renderer initialized",
            templates_path=str(self.templates_path)
        )
    
    def _strftime_filter(self, datetime_obj, format_string):
        """Custom filter for formatting datetime objects"""
        if datetime_obj is None:
            return "N/A"
        try:
            return datetime_obj.strftime(format_string)
        except (AttributeError, ValueError):
            return str(datetime_obj)
    
    def render(self, template_name: str, **context) -> Dict[str, Any]:
        """
        Render a template with the given context
        
        Args:
            template_name: Name of the template file
            **context: Template context variables
            
        Returns:
            Parsed JSON structure for Slack blocks
        """
        try:
            template = self.env.get_template(template_name)
            rendered = template.render(**context)
            
            # Parse the JSON to validate it
            blocks_data = json.loads(rendered)
            
            logger.debug(
                "Template rendered successfully",
                template=template_name,
                context_keys=list(context.keys())
            )
            
            return blocks_data
            
        except Exception as e:
            logger.error(
                "Template rendering failed",
                template=template_name,
                error=str(e)
            )
            # Return a fallback error message
            return self._create_error_message(str(e))
    
    def render_string(self, template_string: str, **context) -> str:
        """
        Render a template string (not from file)
        
        Args:
            template_string: Template content as string
            **context: Template context variables
            
        Returns:
            Rendered string
        """
        try:
            template = Template(template_string)
            return template.render(**context)
        except Exception as e:
            logger.error("String template rendering failed", error=str(e))
            return f"Template error: {str(e)}"
    
    def _create_error_message(self, error: str) -> Dict[str, Any]:
        """Create a fallback error message in Slack format"""
        return {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"❌ *Template Error*\n```{error}```"
                    }
                }
            ]
        }
    
    def list_templates(self) -> list:
        """List available templates"""
        templates = []
        try:
            for template_file in self.templates_path.glob("*.j2"):
                templates.append(template_file.name)
        except Exception as e:
            logger.error("Failed to list templates", error=str(e))
        
        return sorted(templates)
    
    def template_exists(self, template_name: str) -> bool:
        """Check if a template exists"""
        template_path = self.templates_path / template_name
        return template_path.exists()