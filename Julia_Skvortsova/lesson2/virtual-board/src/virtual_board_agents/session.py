"""
Session management for Virtual Board using OpenAI Agents SDK Sessions
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from agents import Runner
from ..models import (
    BoardState, Answer, Analysis, ClusterReport,
    FollowUpQuestion, BiasCheck, ThemeCluster, PersonaDriftCheck
)
from ..config import BoardConfig
from ..constants import Phase, AgentType
from .agents import VirtualBoardAgents
from .memory import MemoryManager
from .production import Guardrails, ExecutionTracer, ErrorHandler, with_production_features
from .prompts.prompt_loader import load_analysis_prompt


class VirtualBoardSession:
    """Manages a virtual board session with proper state management and agent coordination"""
    
    def __init__(self, config: BoardConfig):
        self.config = config
        self.state = BoardState()
        self.agents = VirtualBoardAgents(config, self.state)
        self.memory_manager = MemoryManager()  # Shared memory for all agents
        
        # Production features
        self.guardrails = Guardrails()
        self.tracer = ExecutionTracer()
        self.error_handler = ErrorHandler()
        
        self.start_time = datetime.now()
        
        # Initialize hypothesis coverage
        for hypothesis in config.hypotheses:
            self.state.hypothesis_coverage[hypothesis.id] = 0.0
    
    async def ask_persona(
        self, 
        persona_id: str, 
        question: str, 
        context: Optional[str] = None
    ) -> str:
        """Ask a persona a question with session context"""
        agent = self.agents.get_agent(persona_id)
        
        # Build memory context
        memory_context = self.memory_manager.build_persona_context(persona_id)
        
        # Combine memory context with provided context (which includes product info)
        contexts = [memory_context]
        if context:
            contexts.append(context)
        
        full_context = "\n\n".join(contexts)
        prompt = f"{full_context}\n\nQuestion: {question}"
        
        # Store the question in memory
        self.memory_manager.memory.store_question(
            question=question,
            target_personas=[persona_id],
            metadata={"phase": self.state.phase.value}
        )
        
        # Run agent
        result = await Runner.run(
            agent,
            prompt
        )
        
        answer = result.final_output
        self.save_answer(persona_id, question, answer)

        return answer
    
    async def ask_all_personas(
        self,
        question: str,
        context: Optional[str] = None
    ) -> Dict[str, str]:
        """Ask all personas the same question in parallel"""
        persona_agents = self.agents.get_persona_agents()
        
        # Create tasks for parallel execution
        tasks = []
        for persona_id, agent in persona_agents.items():
            prompt = f"{context}\n\nQuestion: {question}" if context else question
            task = Runner.run(
                agent,
                prompt
            )
            tasks.append((persona_id, task))
        
        # Execute in parallel and collect results
        import asyncio
        print(f"🤔 Asking {len(tasks)} personas...", flush=True)
        results = {}
        responses = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
        
        for (persona_id, _), response in zip(tasks, responses):
            if isinstance(response, Exception):
                results[persona_id] = f"Error: {str(response)}"
                print(f"❌ {persona_id}: Error - {str(response)}", flush=True)
            else:
                try:
                    answer = getattr(response, 'final_output', str(response))
                    results[persona_id] = answer
                    print(f"✅ {persona_id}: {answer[:100]}{'...' if len(answer) > 100 else ''}", flush=True)
                    self.save_answer(persona_id, question, answer)
                    print(f"💾 Saved answer for {persona_id}", flush=True)
                except Exception as e:
                    results[persona_id] = f"Error processing response: {str(e)}"
                    print(f"❌ {persona_id}: Processing error - {str(e)}", flush=True)
        return results
    
    async def analyze_response(
        self,
        persona_id: str,
        response: str,
        question: str
    ) -> Analysis:
        """Analyze a persona's response using the analyst agent with structured output"""
        analyst = self.agents.get_agent(AgentType.ANALYST)
        
        # Build analysis context from memory
        analysis_context = self.memory_manager.build_analysis_context()
        
        # Prepare context for analysis
        hypotheses_list = [
            {"id": h.id, "description": h.description}
            for h in self.config.hypotheses
        ]
        
        persona = next(p for p in self.config.personas if p.id == persona_id)
        
        # Use analyst with structured output (ResponseAnalysis)
        prompt = load_analysis_prompt(
            "response_analysis",
            response=response,
            question=question,
            hypotheses=hypotheses_list,
            persona_name=persona.name,
            persona_background=persona.background,
            analysis_context=analysis_context
        )
        
        result = await Runner.run(analyst, prompt)
        
        # With structured output, result.final_output should be a ResponseAnalysis object
        analysis_data = result.final_output

        analysis = Analysis(
            persona_id=persona_id,
            question=question,
            themes=analysis_data.themes,
            sentiment=analysis_data.sentiment,
            hypotheses_hit=analysis_data.hypotheses_hit,
            key_quotes=analysis_data.key_quotes,
            confidence=analysis_data.confidence
        )

        # Save analysis to state and memory
        self.save_analysis(analysis)

        return analysis
    
    async def check_question_bias(self, question: str, context: Optional[str] = None) -> BiasCheck:
        """Check a question for bias using the specialized bias moderator"""
        bias_moderator = self.agents.get_agent(AgentType.MODERATOR_BIAS)
        
        prompt = load_analysis_prompt(
            "bias_check",
            question=question,
            context=context or 'Product validation discussion'
        )
        
        result = await Runner.run(bias_moderator, prompt)
        
        # With structured output, result.final_output should be a BiasCheck object
        return result.final_output
    
    async def generate_followup(
        self,
        persona_id: str,
        response: str,
        analysis: Analysis
    ) -> Optional[FollowUpQuestion]:
        """Generate a follow-up question using the specialized follow-up facilitator"""
        # TODO: check should_generate_followup

        followup_facilitator = self.agents.get_agent(AgentType.FACILITATOR_FOLLOWUP)
        
        # Find uncovered hypotheses
        uncovered = [
            h_id for h_id, coverage in self.state.hypothesis_coverage.items()
            if coverage < 0.5
        ]
        
        prompt = load_analysis_prompt(
            "followup",
            response=response,
            analysis_data=analysis.model_dump(),
            uncovered_hypotheses=uncovered,
            phase=self.state.phase.value
        )
        
        result = await Runner.run(followup_facilitator, prompt)
        
        # With structured output, result.final_output should be a FollowUpQuestion object
        followup = result.final_output
        
        # Only return if follow-up is actually needed
        if followup.is_needed and followup.question != 'none':
            return followup
        
        return None

    
    async def cluster_themes_for_phase(self, phase: Phase) -> List[ThemeCluster]:
        """Cluster themes for a specific phase using specialized theme analyst"""
        theme_analyst = self.agents.get_agent(AgentType.ANALYST_THEMES)
        
        # Get analyses for the phase
        phase_analyses = [
            a for a in self.state.analyses
            if any(ans.phase == phase for ans in self.state.answers if ans.persona_id == a.persona_id)
        ]
        
        analyses_data = [a.model_dump() for a in phase_analyses]
        
        prompt = load_analysis_prompt(
            "theme_clustering",
            analyses_data=analyses_data
        )
        
        result = await Runner.run(theme_analyst, prompt)
        
        # With structured output, result.final_output should be a list of ThemeCluster objects
        return result.final_output if result.final_output else []
    
    async def check_persona_drift(self, persona_id: str, response: str) -> bool:
        """Check if a persona's response shows drift from their background"""
        moderator = self.agents.get_agent(AgentType.MODERATOR)
        
        # Get persona's background
        persona = next(p for p in self.config.personas if p.id == persona_id)
        
        # Get previous responses
        previous_responses = [
            {"question": ans.question, "response": ans.response}
            for ans in self.state.answers 
            if ans.persona_id == persona_id
        ][-5:]  # Last 5 responses
        
        persona_drift_schema = json.dumps(
            PersonaDriftCheck.model_json_schema(), indent=2
        )

        prompt = load_analysis_prompt(
            "persona_drift",
            response=response,
            persona_background=persona.background,
            previous_responses=previous_responses,
            persona_drift_schema=persona_drift_schema
        )
        
        result = await Runner.run(moderator, prompt)
        
        # Parse response
        if isinstance(result.final_output, str) and '{' in result.final_output:
            try:
                json_start = result.final_output.find('{')
                json_end = result.final_output.rfind('}') + 1
                json_str = result.final_output[json_start:json_end]
                drift_data = json.loads(json_str)
                
                if drift_data.get('is_drift_detected', False):
                    print(f"⚠️ Persona drift detected for {persona.name}: {drift_data['explanation']}")
                    return True
            except Exception as e:
                print(f"Failed to parse drift check: {e}")
        
        return False
    
    async def synthesize_session_insights(self) -> Dict[str, Any]:
        """Synthesize insights from the entire session"""
        facilitator = self.agents.get_agent(AgentType.FACILITATOR)
        
        # Prepare data
        analyses_data = [a.model_dump() for a in self.state.analyses]
        clusters_data = [c.model_dump() for c in self.state.cluster_reports]
        
        prompt = load_analysis_prompt(
            "insight_synthesis",
            analyses_data=analyses_data,
            clusters_data=clusters_data
        )
        
        result = await Runner.run(
            facilitator,
            prompt
        )
        
        return result.final_output
    
    def save_answer(self, persona_id: str, question: str, response: str) -> None:
        """Save an answer to the state and memory"""
        answer = Answer(
            persona_id=persona_id,
            question=question,
            response=response,
            phase=self.state.phase,
            timestamp=datetime.now()
        )
        self.state.answers.append(answer)
        
        # Also store in shared memory for cross-agent access
        self.memory_manager.memory.store_response(
            persona_id=persona_id,
            question=question,
            response=response,
            phase=str(self.state.phase.value) if hasattr(self.state.phase, 'value') else str(self.state.phase)
        )
    
    def save_analysis(self, analysis: Analysis) -> None:
        """Save an analysis to the state and memory"""
        self.state.analyses.append(analysis)
        
        # Also store in shared memory for cross-agent access
        analysis_dict = {
            "themes": analysis.themes,
            "sentiment": analysis.sentiment,
            "hypotheses_hit": analysis.hypotheses_hit,
            "confidence": analysis.confidence,
            "question": getattr(analysis, 'question', ''),
            "response": getattr(analysis, 'response', '')
        }
        self.memory_manager.memory.store_analysis(
            analysis=analysis_dict,
            persona_id=analysis.persona_id
        )
        
        # Update hypothesis coverage
        for h_id in analysis.hypotheses_hit:
            if h_id in self.state.hypothesis_coverage:
                # Increase coverage (max 1.0)
                self.state.hypothesis_coverage[h_id] = min(
                    1.0,
                    self.state.hypothesis_coverage[h_id] + 0.2
                )
    
    def transition_phase(self, new_phase: Phase) -> None:
        """Transition to a new phase"""
        self.state.phase = new_phase
        print(f"\n🔄 Transitioning to {new_phase.value} phase")
    
    def get_session_metadata(self) -> Dict[str, Any]:
        """Get session metadata for reporting"""
        return {
            "session_id": str(id(self)),  # Use object ID as session identifier
            "start_time": self.start_time.isoformat(),
            "current_phase": self.state.phase.value,
            "coverage": self.state.coverage_percentage(),
            "total_answers": len(self.state.answers),
            "total_analyses": len(self.state.analyses),
            "hypothesis_coverage": self.state.hypothesis_coverage
        }