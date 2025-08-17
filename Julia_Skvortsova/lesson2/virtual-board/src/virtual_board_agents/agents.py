"""
Virtual Board agents implementation using OpenAI Agents library
"""
from typing import Dict, List, Optional, Any
from agents import Agent
from ..config import PersonaConfig, BoardConfig
from ..models import (
    BoardState, Answer, Analysis, 
    ResponseAnalysis, ThemeCluster, BiasCheck, FollowUpQuestion
)
from ..constants import AgentType, Phase
from .tools import (
    check_hypothesis_coverage,
    update_hypothesis_coverage,
    should_transition_phase
)
from .prompts.prompt_loader import load_agent_instructions


class VirtualBoardAgents:
    """Multi-agent system for Virtual Board with proper tool calling and state management"""
    
    def __init__(self, config: BoardConfig, state: BoardState):
        self.config = config
        self.state = state
        self.agents: Dict[str, Agent] = {}
        self._initialize_agents()
    
    def _initialize_agents(self) -> None:
        """Initialize all agents with their tools and instructions"""
        
        # Create Facilitator Agent for general facilitation
        self.agents[AgentType.FACILITATOR] = Agent(
            name="Facilitator",
            instructions=load_agent_instructions(AgentType.FACILITATOR.value),
            tools=[
                #should_transition_phase
            ],
            model="gpt-4.1"
        )
        
        # Create specialized Follow-up Facilitator for generating follow-up questions
        self.agents[AgentType.FACILITATOR_FOLLOWUP] = Agent(
            name="Follow-up Facilitator",
            instructions=load_agent_instructions(AgentType.FACILITATOR_FOLLOWUP.value),
            tools=[],
            output_type=FollowUpQuestion,  # Structured output for follow-up questions
            model="gpt-4.1"
        )
        
        # Create Analyst Agents - separate agents for different output types
        
        # Analyst for response analysis
        self.agents[AgentType.ANALYST_RESPONSE] = Agent(
            name="Response Analyst",
            instructions=load_agent_instructions(AgentType.ANALYST.value),
            tools=[
                #check_hypothesis_coverage,
                #update_hypothesis_coverage,
            ],
            output_type=ResponseAnalysis,
            model="gpt-4.1"
        )
        
        # Analyst for theme clustering
        self.agents[AgentType.ANALYST_THEMES] = Agent(
            name="Theme Analyst",
            instructions=load_agent_instructions(AgentType.THEME_ANALYST.value),
            tools=[],
            output_type=list[ThemeCluster],  # For clustering themes
            model="gpt-4.1"
        )
        
        # Keep generic analyst for backward compatibility
        self.agents[AgentType.ANALYST] = self.agents[AgentType.ANALYST_RESPONSE]
        
        # Create Moderator Agents - separate agents for different tasks
        
        # Moderator for bias checking
        self.agents[AgentType.MODERATOR_BIAS] = Agent(
            name="Bias Moderator",
            instructions=load_agent_instructions(AgentType.BIAS_MODERATOR.value),
            tools=[],
            output_type=BiasCheck,
            model="gpt-4.1"
        )
        
        # Generic moderator for other tasks (persona drift, etc.) - returns string
        self.agents[AgentType.MODERATOR] = Agent(
            name="Moderator",
            instructions=load_agent_instructions(AgentType.MODERATOR.value),
            tools=[],
            model="gpt-4.1"  # No output_type = returns string
        )
        
        # Create Persona Agents
        for persona in self.config.personas:
            self.agents[persona.id] = self._create_persona_agent(persona)
        
        # Create Orchestrator Agent that can call other agents
        self.agents[AgentType.ORCHESTRATOR] = Agent(
            name="Orchestrator",
            instructions=load_agent_instructions(AgentType.ORCHESTRATOR.value),
            tools=[
                # Agents as tools for orchestration
                self.agents[AgentType.FACILITATOR].as_tool(
                    tool_name="ask_facilitator",
                    tool_description="Ask the facilitator to generate questions or synthesize insights"
                ),
                self.agents[AgentType.FACILITATOR_FOLLOWUP].as_tool(
                    tool_name="ask_followup_facilitator",
                    tool_description="Ask the follow-up facilitator to generate targeted follow-up questions"
                ),
                self.agents[AgentType.ANALYST].as_tool(
                    tool_name="ask_analyst",
                    tool_description="Ask the analyst to analyze responses or check coverage"
                ),
                self.agents[AgentType.MODERATOR].as_tool(
                    tool_name="ask_moderator",
                    tool_description="Ask the moderator to check for bias or quality issues"
                ),
                # State transition tool
                should_transition_phase
            ],
            model="gpt-4.1"
        )
    
    def _create_persona_agent(self, persona: PersonaConfig) -> Agent:
        """Create a persona agent with memory of their background"""
        return Agent(
            name=persona.name,
            instructions=load_agent_instructions(
                AgentType.PERSONA.value,
                persona_name=persona.name,
                persona_background=persona.background
            ),
            model="gpt-4.1-mini"  # Use smaller model for personas
        )
    
    # Note: Agent instructions are now loaded from prompts/agent_instructions.py
    
    def get_agent(self, agent_id: str) -> Agent:
        """Get an agent by ID"""
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
        return self.agents[agent_id]
    
    def get_persona_agents(self) -> Dict[str, Agent]:
        """Get all persona agents"""
        return {
            pid: agent 
            for pid, agent in self.agents.items() 
            if pid in [p.id for p in self.config.personas]
        }