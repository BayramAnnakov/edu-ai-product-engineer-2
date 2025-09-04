"""
Feature Research Bot - Conducts competitor research and generates feature specifications
"""
import json
import uuid
import time
import structlog
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

from agents import Agent, Runner
from agents.tools import WebSearchTool

# Load environment variables
load_dotenv()

from langfuse_integration import create_traced_runner
from db.review_service import create_review_service
from db.models import Review
from db.feature_research_service import create_feature_research_service
from prompts import format_prompt, FeatureResearchBotPrompts
from schemas import (
    FeatureResearchPlan,
    CompetitorFinding,
    FeatureComparisonMatrix,
    CompetitorResearchReport,
    get_feature_research_plan_schema_formatted,
    get_competitor_finding_schema_formatted,
    get_feature_comparison_matrix_schema_formatted,
    get_competitor_research_report_schema_formatted
)
from guardrails import (
    web_search_input_guardrail,
    research_quality_guardrail,
    feature_spec_output_guardrail
)
from src.config import settings

logger = structlog.get_logger()


class FeatureResearchBot:
    """Multi-agent orchestrator for feature research and competitor analysis"""
    
    def __init__(self, project: str = None):
        self.runner = create_traced_runner()
        self.db_service = None
        self.research_service = None
        self.project = project or settings.youtrack_projects.default
        
        # Create specialized agents for the research workflow
        
        # 1. Research Planner - designs the research strategy
        self.research_planner = Agent(
            name="ResearchPlannerAgent",
            model=settings.models.feature_research_planner,
            output_type=FeatureResearchPlan,
            instructions=format_prompt(FeatureResearchBotPrompts.PLANNER_INSTRUCTIONS),
            input_guardrails=[web_search_input_guardrail]
        )
        
        # 2. Web Researcher - executes searches with WebSearchTool
        self.web_researcher = Agent(
            name="WebResearchAgent",
            model=settings.models.feature_web_researcher,
            tools=[WebSearchTool()],  # SDK's built-in web search tool
            output_type=List[CompetitorFinding],
            instructions=format_prompt(FeatureResearchBotPrompts.RESEARCHER_INSTRUCTIONS),
            input_guardrails=[web_search_input_guardrail],
            output_guardrails=[research_quality_guardrail]
        )
        
        # 3. Competitor Analyst - analyzes findings and creates comparison matrix
        self.competitor_analyst = Agent(
            name="CompetitorAnalystAgent",
            model=settings.models.feature_competitor_analyst,
            output_type=FeatureComparisonMatrix,
            instructions=format_prompt(FeatureResearchBotPrompts.ANALYST_INSTRUCTIONS)
        )
        
        # 4. Feature Spec Writer - generates final feature specification
        self.feature_spec_writer = Agent(
            name="FeatureSpecWriterAgent",
            model=settings.models.feature_spec_writer,
            output_type=CompetitorResearchReport,
            instructions=format_prompt(FeatureResearchBotPrompts.REPORTER_INSTRUCTIONS),
            output_guardrails=[feature_spec_output_guardrail]
        )
        
        # 5. Main Orchestrator - coordinates the workflow with handoffs
        self.orchestrator = Agent(
            name="FeatureResearchOrchestrator",
            model=settings.models.feature_research_bot,
            instructions=format_prompt(FeatureResearchBotPrompts.ORCHESTRATOR_INSTRUCTIONS),
            handoffs=[
                self.research_planner,
                self.web_researcher,
                self.competitor_analyst,
                self.feature_spec_writer
            ]
        )
        
        logger.info("FeatureResearchBot initialized with multi-agent orchestration",
                   agent_name=self.orchestrator.name,
                   project=self.project,
                   sub_agents=[
                       self.research_planner.name,
                       self.web_researcher.name,
                       self.competitor_analyst.name,
                       self.feature_spec_writer.name
                   ])
    
    async def _ensure_db_service(self):
        """Ensure database services are initialized"""
        if not self.db_service:
            self.db_service = await create_review_service()
        if not self.research_service:
            self.research_service = await create_feature_research_service()
    
    async def process_feature_request(
        self,
        review: Review,
        feature_description: str,
        competitors: Optional[List[str]] = None,
        langfuse_trace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a feature request through the full research workflow
        
        Args:
            review: The review containing the feature request
            feature_description: Brief description of the feature to research
            competitors: Optional list of known competitors to analyze
            langfuse_trace_id: Optional trace ID for observability
            
        Returns:
            Dict containing the research report and metadata
        """
        await self._ensure_db_service()
        
        try:
            logger.info("Starting feature research workflow",
                       review_id=str(review.id),
                       feature=feature_description[:100])
            
            # Generate session ID for tracking
            session_id = str(uuid.uuid4())
            start_time = time.time()
            
            # Prepare competitor list
            if not competitors:
                competitors = settings.competitors or ["Slack", "Teams", "Discord"]
            
            # Create research session in database
            research_session = await self.research_service.create_research_session(
                review_id=review.id,
                feature_description=feature_description,
                project=self.project,
                competitors_list=competitors,
                session_id=session_id,
                langfuse_trace_id=langfuse_trace_id
            )
            
            # Create the research request with all context
            research_request = format_prompt(
                FeatureResearchBotPrompts.RESEARCH_WORKFLOW,
                feature_description=feature_description,
                review_text=review.text,
                review_id=str(review.original_id or review.id),
                competitors=", ".join(competitors) if competitors else "",
                project=self.project,
                session_id=session_id,
                # Schema definitions for structured output
                research_plan_schema=get_feature_research_plan_schema_formatted(),
                finding_schema=get_competitor_finding_schema_formatted(),
                matrix_schema=get_feature_comparison_matrix_schema_formatted(),
                report_schema=get_competitor_research_report_schema_formatted()
            )
            
            try:
                # Run the orchestrated workflow with handoffs
                result = await self.runner.run(
                    self.orchestrator,
                    research_request,
                    context={
                        "review_id": str(review.id),
                        "langfuse_trace_id": langfuse_trace_id,
                        "project": self.project,
                        "feature": feature_description
                    },
                    max_turns=24  # Allow sufficient turns for multi-agent workflow
                )
                
                final_output = result.final_output if hasattr(result, 'final_output') else result
                
            except Exception as e:
                # Check if it's a guardrail tripwire
                if "tripwire" in str(e).lower() or "quality" in str(e).lower():
                    logger.warning(
                        "Research quality check failed",
                        review_id=str(review.id),
                        error=str(e)
                    )
                    # Return partial results with quality warning
                    processing_time_ms = int((time.time() - start_time) * 1000)
                    return {
                        "review_id": str(review.id),
                        "session_id": session_id,
                        "status": "quality_check_failed",
                        "warning": str(e),
                        "processing_time_ms": processing_time_ms,
                        "requires_human_review": True
                    }
                else:
                    raise
            
            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Parse and validate the research report
            try:
                report = self._parse_research_report(final_output)
                
                logger.info("Feature research completed successfully",
                           session_id=session_id,
                           competitors_analyzed=len(report.competitor_matrix.rows),
                           processing_time_ms=processing_time_ms)
                
                # Store research results in database
                await self.research_service.complete_research_session(
                    session_id=session_id,
                    final_report=report,
                    processing_time_ms=processing_time_ms,
                    agent_turns_used=getattr(result, 'turns_used', 0),
                    web_searches_performed=len(report.appendix_sources)
                )
                
                return {
                    "review_id": str(review.id),
                    "session_id": session_id,
                    "status": "completed",
                    "feature_spec": {
                        "name": report.feature_spec.name,
                        "problem": report.feature_spec.problem,
                        "user_stories": report.feature_spec.user_stories,
                        "acceptance_criteria": report.feature_spec.acceptance_criteria,
                        "differentiation": report.feature_spec.differentiation_notes,
                        "risks": report.feature_spec.risks
                    },
                    "competitor_analysis": {
                        "summary": report.summary,
                        "competitors_analyzed": [row.competitor for row in report.competitor_matrix.rows],
                        "has_similar_features": [
                            row.competitor for row in report.competitor_matrix.rows 
                            if row.has_feature
                        ]
                    },
                    "sources": report.appendix_sources,
                    "processing_time_ms": processing_time_ms,
                    "requires_pm_approval": True,
                    "agent_output": str(final_output)
                }
                
            except Exception as e:
                logger.error("Failed to parse research report",
                           error=str(e),
                           output=str(final_output)[:500])
                
                # Mark session as failed
                await self.research_service.fail_research_session(
                    session_id=session_id,
                    error_message=str(e),
                    processing_time_ms=processing_time_ms
                )
                
                return {
                    "review_id": str(review.id),
                    "session_id": session_id,
                    "status": "parse_error",
                    "error": str(e),
                    "processing_time_ms": processing_time_ms,
                    "agent_output": str(final_output)
                }
            
        except Exception as e:
            logger.exception("Feature research workflow failed", review_id=str(review.id))
            raise
    
    def _parse_research_report(self, agent_output: str) -> CompetitorResearchReport:
        """Parse and validate the research report from agent output"""
        try:
            # Extract JSON from agent output
            import re
            json_match = re.search(r'\{.*\}', agent_output, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in agent output")
            
            json_str = json_match.group()
            json_data = json.loads(json_str)
            
            # Validate using Pydantic schema
            validated_report = CompetitorResearchReport(**json_data)
            return validated_report
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in agent output: {e}")
        except Exception as e:
            raise ValueError(f"Schema validation failed: {e}")
    
    
    async def test_web_search_connection(self) -> Dict[str, Any]:
        """Test the web search tool connection"""
        try:
            test_prompt = "Search for 'collaborative whiteboard features' and return the first result."
            result = await self.runner.run(
                self.web_researcher,
                test_prompt,
                max_turns=1
            )
            
            return {
                "status": "connected",
                "tool": "WebSearchTool",
                "response": str(result.final_output if hasattr(result, 'final_output') else result)
            }
        except Exception as e:
            logger.error("Web search test failed", error=str(e))
            return {
                "status": "failed",
                "error": str(e),
                "tool": "WebSearchTool"
            }


# Convenience function
async def research_feature(
    review: Review,
    feature_description: str,
    competitors: Optional[List[str]] = None,
    project: Optional[str] = None
) -> Dict[str, Any]:
    """Research a feature request through competitor analysis"""
    bot = FeatureResearchBot(project=project or settings.youtrack_projects.default)
    return await bot.process_feature_request(review, feature_description, competitors)