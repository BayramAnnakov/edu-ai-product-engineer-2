"""
Guardrails for feature research and competitor analysis using SDK decorator patterns
"""
import re
import json
import structlog
from typing import Any, Dict
from agents import input_guardrail, output_guardrail, Agent, Runner
from agents import GuardrailFunctionOutput, RunContextWrapper
from src.config import settings

logger = structlog.get_logger()

@input_guardrail
async def web_search_input_guardrail(
    ctx: RunContextWrapper[None],
    agent: Agent,
    input_text: str
) -> GuardrailFunctionOutput:
    """Validates web search queries and prevents harmful searches"""
    
    max_query_length = 200
    max_queries_per_task = 10
    blocked_patterns = [
        r'(?i)password',
        r'(?i)secret',
        r'(?i)api[_\s]?key',
        r'(?i)token',
        r'(?i)credential',
        r'(?i)private',
        r'(?i)confidential'
    ]
    
    try:
        # Check for blocked patterns
        for pattern in blocked_patterns:
            if re.search(pattern, input_text):
                logger.warning("Blocked sensitive information in search query", 
                             pattern=pattern, 
                             query_preview=input_text[:50])
                return GuardrailFunctionOutput(
                    output_info="Search query contains sensitive information and was blocked",
                    tripwire_triggered=True
                )
        
        # Check query length
        if len(input_text) > max_query_length:
            logger.warning("Search query too long", 
                         length=len(input_text), 
                         max_length=max_query_length)
            return GuardrailFunctionOutput(
                output_info=f"Search query exceeds maximum length of {max_query_length} characters",
                tripwire_triggered=True
            )
        
        # Allow the search to proceed
        return GuardrailFunctionOutput(
            output_info="Web search input validated",
            tripwire_triggered=False
        )
        
    except Exception as e:
        logger.error("Web search input guardrail failed", error=str(e))
        return GuardrailFunctionOutput(
            output_info=f"Guardrail error: {str(e)}",
            tripwire_triggered=False
        )

@output_guardrail
async def research_quality_guardrail(
    ctx: RunContextWrapper[None],
    agent: Agent,
    output: str
) -> GuardrailFunctionOutput:
    """Validates research output quality and completeness"""
    
    min_content_length = 100
    required_sections = ["summary", "findings", "recommendations"]
    
    try:
        # Check minimum content length
        if len(output) < min_content_length:
            logger.warning("Research output too short", 
                         length=len(output), 
                         min_length=min_content_length)
            return GuardrailFunctionOutput(
                output_info=f"Research output is too short (minimum {min_content_length} characters)",
                tripwire_triggered=True
            )
        
        # Try to parse as JSON and check for required sections
        try:
            data = json.loads(output)
            missing_sections = [section for section in required_sections if section not in data]
            if missing_sections:
                logger.warning("Research output missing required sections", 
                             missing=missing_sections)
                return GuardrailFunctionOutput(
                    output_info=f"Research output missing required sections: {', '.join(missing_sections)}",
                    tripwire_triggered=True
                )
        except json.JSONDecodeError:
            # If not JSON, check for section keywords in text
            output_lower = output.lower()
            missing_keywords = [section for section in required_sections if section not in output_lower]
            if len(missing_keywords) > 1:  # Allow some flexibility for text output
                logger.warning("Research output may be incomplete", 
                             missing_keywords=missing_keywords)
                return GuardrailFunctionOutput(
                    output_info="Research output may be incomplete - consider adding more structured content",
                    tripwire_triggered=False  # Warning, not blocking
                )
        
        return GuardrailFunctionOutput(
            output_info="Research output quality validated",
            tripwire_triggered=False
        )
        
    except Exception as e:
        logger.error("Research quality guardrail failed", error=str(e))
        return GuardrailFunctionOutput(
            output_info=f"Guardrail error: {str(e)}",
            tripwire_triggered=False
        )

@output_guardrail
async def feature_spec_output_guardrail(
    ctx: RunContextWrapper[None],
    agent: Agent,
    output: str
) -> GuardrailFunctionOutput:
    """Validates feature specification output completeness"""
    
    required_spec_elements = [
        "user story",
        "acceptance criteria", 
        "technical requirements",
        "dependencies"
    ]
    
    try:
        output_lower = output.lower()
        
        # Check for required specification elements
        missing_elements = []
        for element in required_spec_elements:
            if element not in output_lower:
                missing_elements.append(element)
        
        if missing_elements:
            logger.warning("Feature specification incomplete", 
                         missing_elements=missing_elements)
            return GuardrailFunctionOutput(
                output_info=f"Feature specification missing: {', '.join(missing_elements)}",
                tripwire_triggered=True
            )
        
        # Check minimum length for comprehensive spec
        if len(output) < 500:
            logger.warning("Feature specification may be too brief", 
                         length=len(output))
            return GuardrailFunctionOutput(
                output_info="Feature specification appears brief - consider adding more detail",
                tripwire_triggered=False  # Warning, not blocking
            )
        
        return GuardrailFunctionOutput(
            output_info="Feature specification output validated",
            tripwire_triggered=False
        )
        
    except Exception as e:
        logger.error("Feature spec output guardrail failed", error=str(e))
        return GuardrailFunctionOutput(
            output_info=f"Guardrail error: {str(e)}",
            tripwire_triggered=False
        )

@input_guardrail
async def feature_research_workflow_guardrail(
    ctx: RunContextWrapper[None],
    agent: Agent,
    input_text: str
) -> GuardrailFunctionOutput:
    """Validates feature research workflow inputs for safety and compliance"""
    
    prohibited_domains = [
        "internal.company.com",
        "admin.company.com",
        "staging.company.com"
    ]
    
    sensitive_patterns = [
        r'(?i)internal\s+api',
        r'(?i)admin\s+panel',
        r'(?i)database\s+schema',
        r'(?i)server\s+credentials'
    ]
    
    try:
        # Check for prohibited domains
        for domain in prohibited_domains:
            if domain in input_text.lower():
                logger.warning("Prohibited domain in research request", 
                             domain=domain)
                return GuardrailFunctionOutput(
                    output_info=f"Research request contains prohibited domain: {domain}",
                    tripwire_triggered=True
                )
        
        # Check for sensitive patterns
        for pattern in sensitive_patterns:
            if re.search(pattern, input_text):
                logger.warning("Sensitive pattern detected in research request", 
                             pattern=pattern)
                return GuardrailFunctionOutput(
                    output_info="Research request contains sensitive information and was blocked",
                    tripwire_triggered=True
                )
        
        return GuardrailFunctionOutput(
            output_info="Feature research workflow input validated",
            tripwire_triggered=False
        )
        
    except Exception as e:
        logger.error("Feature research workflow guardrail failed", error=str(e))
        return GuardrailFunctionOutput(
            output_info=f"Guardrail error: {str(e)}",
            tripwire_triggered=False
        )