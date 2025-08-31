"""
Basic A2A PM Agents Implementation.

Implements Product Management agents using Google's A2A protocol
for standardized agent-to-agent communication.
"""

import asyncio
import json
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum

from dotenv import load_dotenv
load_dotenv()

from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

# Initialize AI clients
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
anthropic_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


class PMAction(Enum):
    """Standard PM actions across agents"""
    ANALYZE_MARKET = "analyze_market"
    CREATE_USER_STORY = "create_user_story"
    ESTIMATE_EFFORT = "estimate_effort"
    PRIORITIZE_FEATURES = "prioritize_features"
    ASSESS_TECHNICAL_FEASIBILITY = "assess_technical_feasibility"
    GENERATE_PRD = "generate_prd"
    REVIEW_METRICS = "review_metrics"
    PLAN_SPRINT = "plan_sprint"


@dataclass
class PMRequest:
    """Standard request format for PM agents"""
    action: PMAction
    context: Dict[str, Any]
    priority: str = "normal"  # urgent, high, normal, low
    requester: Optional[str] = None
    correlation_id: Optional[str] = None


@dataclass
class PMResponse:
    """Standard response format for PM agents"""
    success: bool
    action: PMAction
    result: Dict[str, Any]
    confidence: float = 0.8
    processing_time: float = 0.0
    agent_name: str = ""
    recommendations: List[str] = field(default_factory=list)


class BasePMAgent:
    """
    Base class for PM agents implementing A2A communication.
    Provides common functionality for all PM agent types.
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.agent_type = "pm_agent"
        self.version = "1.0.0"
        self.created_at = datetime.now()
        
        # Performance tracking
        self.request_count = 0
        self.success_count = 0
        self.average_processing_time = 0.0
        
        # Note: A2A client would be initialized here for actual agent-to-agent communication
        # For this demo, we're using direct method calls between agents
    
    async def handle_request(self, request: PMRequest) -> PMResponse:
        """Handle incoming requests"""
        
        start_time = datetime.now()
        self.request_count += 1
        
        try:
            # Route to appropriate handler
            result = await self._route_action(request)
            
            # Build response
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_metrics(processing_time, success=True)
            
            pm_response = PMResponse(
                success=True,
                action=request.action,
                result=result,
                processing_time=processing_time,
                agent_name=self.name
            )
            
            return pm_response
            
        except Exception as e:
            self._update_metrics(0, success=False)
            
            return PMResponse(
                success=False,
                action=request.action,
                result={"error": str(e)},
                agent_name=self.name
            )
    
    async def _route_action(self, request: PMRequest) -> Dict[str, Any]:
        """Route request to appropriate action handler"""
        raise NotImplementedError(f"Agent {self.name} doesn't handle action {request.action}")
    
    def _update_metrics(self, processing_time: float, success: bool):
        """Update agent performance metrics"""
        
        if success:
            self.success_count += 1
        
        # Update moving average of processing time
        self.average_processing_time = (
            (self.average_processing_time * (self.request_count - 1) + processing_time) 
            / self.request_count
        )
    
    async def get_status(self) -> Dict[str, Any]:
        """Get agent status and metrics"""
        
        return {
            "name": self.name,
            "type": self.agent_type,
            "version": self.version,
            "status": "healthy",
            "uptime": (datetime.now() - self.created_at).total_seconds(),
            "metrics": {
                "requests": self.request_count,
                "success_rate": self.success_count / max(1, self.request_count),
                "avg_processing_time": self.average_processing_time
            }
        }


class MarketResearchAgent(BasePMAgent):
    """
    Agent specialized in market research and competitive analysis.
    """
    
    def __init__(self):
        super().__init__(
            name="market_research_agent",
            description="Analyzes market trends, opportunities, and competitors"
        )
        self.agent_type = "market_research"
    
    async def analyze_market(self, request: PMRequest) -> Dict[str, Any]:
        """Perform market analysis"""
        
        context = request.context
        
        prompt = f"""
        Conduct market analysis for:
        Product: {context.get('product', 'Unknown')}
        Market: {context.get('market', 'General')}
        
        Provide:
        1. Market size and growth
        2. Key trends
        3. Customer segments
        4. Opportunities
        5. Threats
        
        Format as structured JSON.
        """
        
        response = await openai_client.chat.completions.create(
            model="gpt-4o",  # Using available model instead of gpt-5
            messages=[
                {"role": "system", "content": "You are a market research expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def _route_action(self, request: PMRequest) -> Dict[str, Any]:
        """Route market research actions"""
        
        if request.action == PMAction.ANALYZE_MARKET:
            return await self.analyze_market(request)
        else:
            raise NotImplementedError(f"Market research agent doesn't handle {request.action}")


class UserStoryAgent(BasePMAgent):
    """
    Agent specialized in creating and managing user stories.
    """
    
    def __init__(self):
        super().__init__(
            name="user_story_agent",
            description="Creates user stories and estimates effort"
        )
        self.agent_type = "user_story"
    
    async def create_user_story(self, request: PMRequest) -> Dict[str, Any]:
        """Create a user story"""
        
        context = request.context
        
        prompt = f"""
        Create a user story for:
        Feature: {context.get('feature', '')}
        User Persona: {context.get('persona', '')}
        Context: {json.dumps(context.get('additional_context', {}))}
        
        Include:
        1. Story in standard format (As a... I want... So that...)
        2. Acceptance criteria (Given/When/Then)
        3. Priority and effort estimate
        4. Dependencies
        5. Success metrics
        
        Format as structured JSON.
        """
        
        response = await anthropic_client.messages.create(
            model="claude-3-5-sonnet-latest",  # Using latest sonnet model
            max_tokens=1500,
            system="You are an expert in writing user stories.",
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Extract JSON from Claude's response
        content = response.content[0].text
        # Try to parse JSON from the response
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # If not pure JSON, create structured response
            return {
                "story": content,
                "format": "text",
                "needs_parsing": True
            }
    
    async def estimate_effort(self, request: PMRequest) -> Dict[str, Any]:
        """Estimate effort for a user story"""
        
        story = request.context.get('story', {})
        
        prompt = f"""
        Estimate effort for this user story:
        {json.dumps(story, indent=2)}
        
        Consider:
        1. Technical complexity
        2. Dependencies
        3. Testing requirements
        4. Documentation needs
        
        Provide:
        - Story points (fibonacci: 1,2,3,5,8,13,21)
        - Reasoning
        - Risks
        
        Format as JSON.
        """
        
        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an experienced scrum master."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def _route_action(self, request: PMRequest) -> Dict[str, Any]:
        """Route user story actions"""
        
        if request.action == PMAction.CREATE_USER_STORY:
            return await self.create_user_story(request)
        elif request.action == PMAction.ESTIMATE_EFFORT:
            return await self.estimate_effort(request)
        else:
            raise NotImplementedError(f"User story agent doesn't handle {request.action}")


class TechnicalAnalysisAgent(BasePMAgent):
    """
    Agent specialized in technical feasibility and architecture analysis.
    """
    
    def __init__(self):
        super().__init__(
            name="technical_analysis_agent",
            description="Assesses technical feasibility and architecture"
        )
        self.agent_type = "technical_analysis"
    
    async def assess_feasibility(self, request: PMRequest) -> Dict[str, Any]:
        """Assess technical feasibility"""
        
        requirements = request.context.get('requirements', [])
        constraints = request.context.get('constraints', {})
        
        prompt = f"""
        Assess technical feasibility for:
        Requirements: {json.dumps(requirements, indent=2)}
        Constraints: {json.dumps(constraints, indent=2)}
        
        Evaluate:
        1. Technical complexity
        2. Resource requirements
        3. Technology stack needs
        4. Integration challenges
        5. Performance implications
        6. Security considerations
        7. Scalability concerns
        
        Provide feasibility score (0-100) and detailed analysis.
        Format as JSON.
        """
        
        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a technical architect."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def _route_action(self, request: PMRequest) -> Dict[str, Any]:
        """Route technical analysis actions"""
        
        if request.action == PMAction.ASSESS_TECHNICAL_FEASIBILITY:
            return await self.assess_feasibility(request)
        else:
            raise NotImplementedError(f"Technical analysis agent doesn't handle {request.action}")


class ProductDevelopmentOrchestrator:
    """
    Orchestrator for coordinating multiple PM agents.
    """
    
    def __init__(self):
        # Initialize agents
        self.market_research_agent = MarketResearchAgent()
        self.user_story_agent = UserStoryAgent()
        self.technical_agent = TechnicalAnalysisAgent()
        
        # Workflow state
        self.current_workflow = None
        self.workflow_results = {}
    
    async def execute_product_development_workflow(self,
                                                  product_idea: str,
                                                  context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute complete product development workflow using multiple agents.
        """
        
        workflow_id = f"workflow_{datetime.now().timestamp()}"
        self.current_workflow = workflow_id
        results = {}
        
        print(f"🚀 Starting Product Development Workflow: {workflow_id}")
        print(f"   Product: {product_idea}")
        print("="*60)
        
        # Phase 1: Market Research
        print("\n📊 Phase 1: Market Research")
        market_request = PMRequest(
            action=PMAction.ANALYZE_MARKET,
            context={
                "product": product_idea,
                "market": context.get("market", "General"),
                "competitors": context.get("competitors", [])
            }
        )
        
        market_response = await self.market_research_agent.handle_request(market_request)
        results["market_research"] = asdict(market_response)
        print(f"   ✅ Market analysis complete")
        
        # Phase 2: User Stories (parallel)
        print("\n📝 Phase 2: User Story Creation")
        
        # Extract personas from market research or use defaults
        personas = ["Product Manager", "Software Developer", "Scrum Master"]
        
        # Create user stories in parallel
        story_tasks = []
        for persona in personas:
            story_request = PMRequest(
                action=PMAction.CREATE_USER_STORY,
                context={
                    "feature": product_idea,
                    "persona": persona,
                    "market_insights": results["market_research"]
                }
            )
            story_tasks.append(self.user_story_agent.handle_request(story_request))
        
        story_responses = await asyncio.gather(*story_tasks)
        results["user_stories"] = [asdict(resp) for resp in story_responses]
        print(f"   ✅ Created {len(story_responses)} user stories")
        
        # Phase 3: Technical Feasibility
        print("\n🔧 Phase 3: Technical Feasibility Assessment")
        
        # Extract requirements from user stories
        requirements = []
        for story_response in story_responses:
            if story_response.success:
                requirements.append(story_response.result)
        
        tech_request = PMRequest(
            action=PMAction.ASSESS_TECHNICAL_FEASIBILITY,
            context={
                "requirements": requirements,
                "constraints": context.get("constraints", {})
            }
        )
        
        tech_response = await self.technical_agent.handle_request(tech_request)
        results["technical_analysis"] = asdict(tech_response)
        print(f"   ✅ Technical feasibility assessed")
        
        # Phase 4: Effort Estimation
        print("\n⏱️  Phase 4: Effort Estimation")
        
        estimation_tasks = []
        for story_response in story_responses:
            if story_response.success:
                estimate_request = PMRequest(
                    action=PMAction.ESTIMATE_EFFORT,
                    context={
                        "story": story_response.result
                    }
                )
                estimation_tasks.append(self.user_story_agent.handle_request(estimate_request))
        
        estimate_responses = await asyncio.gather(*estimation_tasks)
        results["effort_estimates"] = [asdict(resp) for resp in estimate_responses]
        print(f"   ✅ Estimated effort for all stories")
        
        # Compile final results
        self.workflow_results[workflow_id] = results
        
        return self._compile_workflow_summary(results)
    
    def _compile_workflow_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Compile workflow results into summary"""
        
        # Extract key insights
        market_insights = results.get("market_research", {}).get("result", {})
        stories = results.get("user_stories", [])
        tech_analysis = results.get("technical_analysis", {}).get("result", {})
        estimates = results.get("effort_estimates", [])
        
        # Calculate total effort
        total_points = 0
        for est in estimates:
            if est.get("success") and est.get("result"):
                # Try to extract story points from result
                result = est.get("result", {})
                if isinstance(result, dict):
                    points = result.get("story_points", 0)
                    if points:
                        total_points += points
        
        return {
            "workflow_id": self.current_workflow,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "market_opportunity": market_insights.get("opportunities", []),
                "user_stories_created": len(stories),
                "total_effort_points": total_points,
                "feasibility_score": tech_analysis.get("feasibility_score", 0),
                "key_risks": tech_analysis.get("risks", []),
                "next_steps": [
                    "Review and prioritize user stories",
                    "Address identified technical risks",
                    "Plan first sprint with highest priority stories"
                ]
            },
            "detailed_results": results
        }


# Example usage
async def main():
    """Example demonstrating PM agents workflow"""
    
    print("🤖 PM Agents Workflow Demo")
    print("="*60)
    
    # Initialize orchestrator
    orchestrator = ProductDevelopmentOrchestrator()
    
    # Define product idea
    product_idea = "AI-Powered Sprint Planning Assistant"
    context = {
        "market": "Agile Software Development Tools",
        "competitors": ["Jira", "Azure DevOps", "Linear"],
        "constraints": {
            "budget": "$200k",
            "timeline": "3 months",
            "team_size": 5
        }
    }
    
    # Execute workflow
    try:
        results = await orchestrator.execute_product_development_workflow(
            product_idea=product_idea,
            context=context
        )
        
        print("\n" + "="*60)
        print("📋 Workflow Summary")
        print("="*60)
        print(json.dumps(results["summary"], indent=2))
        
        # Show agent metrics
        print("\n" + "="*60)
        print("📊 Agent Metrics")
        print("="*60)
        
        agents = [
            orchestrator.market_research_agent,
            orchestrator.user_story_agent,
            orchestrator.technical_agent
        ]
        
        for agent in agents:
            status = await agent.get_status()
            print(f"\n{agent.name}:")
            print(f"  Requests: {status['metrics']['requests']}")
            print(f"  Success Rate: {status['metrics']['success_rate']:.1%}")
            print(f"  Avg Processing Time: {status['metrics']['avg_processing_time']:.2f}s")
        
    except Exception as e:
        print(f"Workflow failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())