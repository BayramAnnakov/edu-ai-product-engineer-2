"""
Bug submission approval assessment using LLM-as-a-judge
"""
import json
from typing import Dict, Any, Optional
import structlog

from agents import Agent
from langfuse_integration import create_traced_runner
from schemas import BugSubmissionAssessment, get_bug_submission_schema_formatted
from prompts import format_prompt, BugApprovalJudgePrompts
from src.config import settings

logger = structlog.get_logger()


class BugApprovalJudge:
    """LLM-powered judge for bug submission approval assessment"""
    
    def __init__(self):
        self.runner = create_traced_runner()
        
        # Create the bug approval judge agent with clean Pydantic config
        self.agent = Agent(
            name="BugApprovalJudge",
            instructions=format_prompt(BugApprovalJudgePrompts.INSTRUCTIONS),
            model=settings.models.bug_approval_judge
        )
        
        # Get timeout from config
        self.timeout_seconds = settings.agents.bug_approval_judge.timeout_seconds
        
        logger.info("BugApprovalJudge service initialized", 
                   agent_name=self.agent.name)
    
    def _parse_agent_json_output(self, output: str) -> dict:
        """Parse agent JSON output, handling potential formatting issues"""
        try:
            # Try to parse as-is first
            return json.loads(output)
        except json.JSONDecodeError:
            # Try to extract JSON from text (in case there's extra text)
            import re
            json_match = re.search(r'\{.*\}', output, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                raise ValueError(f"No valid JSON found in agent output: {output[:200]}...")
    
    def _validate_assessment_output(self, parsed_json: dict) -> BugSubmissionAssessment:
        """Validate agent output against BugSubmissionAssessment schema"""
        try:
            validated = BugSubmissionAssessment(**parsed_json)
            return validated
        except Exception as e:
            logger.error("Schema validation failed", 
                        error=str(e),
                        json_data=parsed_json)
            raise

    async def assess_bug_submission(
        self, 
        bug_text: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> BugSubmissionAssessment:
        """
        Assess a bug submission to determine if it needs human approval
        
        Args:
            bug_text: The bug report or workflow description to analyze
            context: Additional context (review info, metadata, etc.)
            
        Returns:
            Structured bug submission assessment
        """
        try:
            # Prepare context information
            context_info = ""
            if context:
                context_parts = []
                if context.get("review_id"):
                    context_parts.append(f"**Review ID:** {context['review_id']}")
                if context.get("project"):
                    context_parts.append(f"**Project:** {context['project']}")
                if context.get("confidence"):
                    context_parts.append(f"**Classification confidence:** {context['confidence']}")
                if context.get("similarity_score"):
                    context_parts.append(f"**Similarity score:** {context['similarity_score']}%")
                
                if context_parts:
                    context_info = f"**Context:**\n{chr(10).join(context_parts)}"
            
            # Create analysis prompt using the task template
            analysis_prompt = format_prompt(
                BugApprovalJudgePrompts.ASSESSMENT_TASK,
                bug_text=bug_text,
                context_info=context_info,
                uncertainty_schema=get_bug_submission_schema_formatted()
            )
            
            # Run the judge
            result = await self.runner.run(self.agent, analysis_prompt)
            final_output = result.final_output if hasattr(result, 'final_output') else str(result)
            
            # Parse and validate JSON output
            try:
                parsed_json = self._parse_agent_json_output(str(final_output))
                assessment = self._validate_assessment_output(parsed_json)
                
                logger.info(
                    "LLM bug submission assessment completed",
                    needs_approval=assessment.needs_approval,
                    confidence=assessment.confidence_score,
                    risk_level=assessment.risk_level
                )
                
                return assessment
                
            except Exception as e:
                logger.error("Failed to parse agent JSON output", error=str(e), output=str(final_output)[:500])
                return self._fallback_assessment(bug_text)
            
        except Exception as e:
            logger.error("LLM bug submission assessment failed", error=str(e))
            return self._fallback_assessment(bug_text)
    
    def _fallback_assessment(self, bug_text: str) -> BugSubmissionAssessment:
        """Fallback assessment when LLM fails"""
        return BugSubmissionAssessment(
            needs_approval=True,
            confidence_score=0.5,
            duplicate_uncertainty=True,
            critical_priority=False,
            reasoning="LLM bug submission assessment failed, requiring approval as safety measure",
            risk_level="MEDIUM",
            bug_summary=bug_text[:100] + "..." if len(bug_text) > 100 else bug_text,
            mentioned_keywords=["assessment_failure"]
        )


# Global judge instance
_bug_approval_judge = None

async def get_bug_approval_judge() -> BugApprovalJudge:
    """Get or create the bug approval judge instance"""
    global _bug_approval_judge
    if _bug_approval_judge is None:
        _bug_approval_judge = BugApprovalJudge()
    return _bug_approval_judge