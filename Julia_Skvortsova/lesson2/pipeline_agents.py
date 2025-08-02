"""Pipeline agents using OpenAI Agents SDK"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from agents import Agent, Runner, set_default_openai_key

from pipeline_constants import PipelineAgentType
from pipeline_prompts import PromptManager
from pipeline_models import (
    PipelineConfig, FeatureExtractionOutput, PersonaExtractionOutput, 
    PersonaMatchingOutput, RICEScoringOutput, ProductConceptOutput, 
    ResearchQuestionsOutput
)
from pipeline_utils import logger


class PipelineAgents:
    """Manages pipeline agents for review analysis and product development"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.prompt_manager = PromptManager(config.prompts_dir)
        self.agents: Dict[str, Agent] = {}
        
        # Set OpenAI API key for agents
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        set_default_openai_key(api_key)
        
        self._initialize_agents()
    
    def _initialize_agents(self) -> None:
        """Initialize all pipeline agents with their instructions"""
        
        # Review Summarizer Agent
        self.agents[PipelineAgentType.REVIEW_SUMMARIZER.value] = Agent(
            name="Review Summarizer",
            instructions=self._load_instructions(PipelineAgentType.REVIEW_SUMMARIZER),
            model=self.config.reasoning_model
        )
        
        # Feature Extractor Agent
        self.agents[PipelineAgentType.FEATURE_EXTRACTOR.value] = Agent(
            name="Feature Extractor",
            instructions=self._load_instructions(PipelineAgentType.FEATURE_EXTRACTOR),
            model=self.config.reasoning_model,
            output_type=FeatureExtractionOutput
        )
        
        # Persona Extractor Agent
        self.agents[PipelineAgentType.PERSONA_EXTRACTOR.value] = Agent(
            name="Persona Extractor",
            instructions=self._load_instructions(PipelineAgentType.PERSONA_EXTRACTOR),
            model=self.config.reasoning_model,
            output_type=PersonaExtractionOutput
        )
        
        # Persona Matcher Agent
        self.agents[PipelineAgentType.PERSONA_MATCHER.value] = Agent(
            name="Persona Matcher",
            instructions=self._load_instructions(PipelineAgentType.PERSONA_MATCHER),
            model=self.config.reasoning_model,
            output_type=PersonaMatchingOutput
        )
        
        # RICE Analyst Agent
        self.agents[PipelineAgentType.RICE_ANALYST.value] = Agent(
            name="RICE Analyst",
            instructions=self._load_instructions(PipelineAgentType.RICE_ANALYST),
            model=self.config.reasoning_model,
            output_type=RICEScoringOutput
        )
        
        # Product Conceptor Agent
        self.agents[PipelineAgentType.PRODUCT_CONCEPTOR.value] = Agent(
            name="Product Conceptor",
            instructions=self._load_instructions(PipelineAgentType.PRODUCT_CONCEPTOR),
            model=self.config.reasoning_model,
            output_type=ProductConceptOutput
        )
        
        # Market Researcher Agent
        self.agents[PipelineAgentType.MARKET_RESEARCHER.value] = Agent(
            name="Market Researcher",
            instructions=self._load_instructions(PipelineAgentType.MARKET_RESEARCHER),
            model=self.config.reasoning_model
        )
        
        # Research Designer Agent
        self.agents[PipelineAgentType.RESEARCH_DESIGNER.value] = Agent(
            name="Research Designer",
            instructions=self._load_instructions(PipelineAgentType.RESEARCH_DESIGNER),
            model=self.config.reasoning_model,
            output_type=ResearchQuestionsOutput
        )
        
        logger.info(f"Initialized {len(self.agents)} pipeline agents")
    
    def _load_instructions(self, agent_type: PipelineAgentType) -> str:
        """Load agent instructions from file"""
        instructions_file = f"agents/{agent_type.value}.md"
        
        try:
            return self.prompt_manager.load_prompt(instructions_file)
        except FileNotFoundError:
            logger.warning(f"Instructions not found for {agent_type.name}, using generic instructions")
            return f"You are a {agent_type.name.replace('_', ' ').title()} agent. Follow the user's instructions carefully."
    
    async def run_agent(
        self,
        agent_type: PipelineAgentType,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None
    ) -> str:
        """Run an agent with the given prompt and parameters"""
        
        if agent_type.value not in self.agents:
            raise ValueError(f"Agent {agent_type.name} not found")
        
        agent = self.agents[agent_type.value]
        
        logger.debug(f"Running {agent_type.name} agent with prompt length: {len(prompt)}")
        
        try:
            # Run agent using Runner (OpenAI Agents SDK)
            result = await Runner.run(agent, prompt)
            
            # For agents with structured output, return the final_output directly
            if hasattr(result, 'final_output') and result.final_output is not None:
                logger.debug(f"Agent returned structured output: {type(result.final_output)}")
                return result.final_output
            elif hasattr(result, 'content'):
                logger.debug(f"Agent returned content: {result.content[:100]}...")
                return result.content
            else:
                logger.debug(f"Agent returned raw result: {str(result)[:100]}...")
                return str(result)
                    
        except Exception as e:
            logger.error(f"Error running {agent_type.name} agent: {e}")
            raise
    
    def get_agent(self, agent_type: PipelineAgentType) -> Agent:
        """Get a specific agent by type"""
        if agent_type.value not in self.agents:
            raise ValueError(f"Agent {agent_type.name} not found")
        return self.agents[agent_type.value]
    
    def list_agents(self) -> list[str]:
        """List all available agent types"""
        return list(self.agents.keys())