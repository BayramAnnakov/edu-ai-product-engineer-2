"""
Smoke test for agent system - verifies real initialization without API calls

This test actually creates the VirtualBoardAgents system without mocking 
to ensure all prompts load correctly and agents are configured properly.
No API calls are made.
"""
import pytest
from src.virtual_board_agents.agents import VirtualBoardAgents
from src.config import BoardConfig, ProductConfig, PersonaConfig, HypothesisConfig, QuestionsConfig
from src.models import BoardState
from src.constants import AgentType


@pytest.fixture
def real_config():
    """Create a real board configuration"""
    return BoardConfig(
        product=ProductConfig(
            name="AI Assistant App",
            description="A mobile app that helps users with daily tasks using AI"
        ),
        hypotheses=[
            HypothesisConfig(id="H1", description="Users want voice interaction"),
            HypothesisConfig(id="H2", description="Privacy is a major concern"),
            HypothesisConfig(id="H3", description="Integration with existing apps is important")
        ],
        questions=QuestionsConfig(),
        personas=[
            PersonaConfig(
                id="tech_sarah",
                name="Sarah",
                background="Software engineer, 28, values efficiency and privacy. Uses multiple productivity apps."
            ),
            PersonaConfig(
                id="student_mike", 
                name="Mike",
                background="College student, 20, budget-conscious, heavy smartphone user, concerned about data usage."
            ),
            PersonaConfig(
                id="parent_lisa",
                name="Lisa",
                background="Working mother, 35, manages family schedule, prefers simple interfaces, worried about children's privacy."
            )
        ]
    )


@pytest.fixture
def real_state(real_config):
    """Create a real board state"""
    state = BoardState()
    # Initialize hypothesis coverage for all hypotheses
    for hypothesis in real_config.hypotheses:
        state.hypothesis_coverage[hypothesis.id] = 0.0
    return state


class TestRealAgentInitialization:
    """Test real agent system initialization without mocking"""
    
    def test_agents_system_creation(self, real_config, real_state):
        """Test that VirtualBoardAgents can be created with real config"""
        # This should work without errors - all prompts should load
        agents = VirtualBoardAgents(real_config, real_state)
        
        assert agents is not None
        assert agents.config == real_config
        assert agents.state == real_state
        
    def test_all_required_agents_exist(self, real_config, real_state):
        """Test that all required agent types are created"""
        agents = VirtualBoardAgents(real_config, real_state)
        
        # Core system agents
        assert AgentType.FACILITATOR in agents.agents
        assert AgentType.FACILITATOR_FOLLOWUP in agents.agents
        assert AgentType.ANALYST_RESPONSE in agents.agents
        assert AgentType.ANALYST_THEMES in agents.agents
        assert AgentType.MODERATOR_BIAS in agents.agents
        assert AgentType.MODERATOR in agents.agents
        assert AgentType.ORCHESTRATOR in agents.agents
        
        # Persona agents
        assert "tech_sarah" in agents.agents
        assert "student_mike" in agents.agents
        assert "parent_lisa" in agents.agents
        
    def test_agent_retrieval_works(self, real_config, real_state):
        """Test that agents can be retrieved by ID"""
        agents = VirtualBoardAgents(real_config, real_state)
        
        # Test system agents
        facilitator = agents.get_agent(AgentType.FACILITATOR)
        assert facilitator is not None
        assert hasattr(facilitator, 'name')
        assert facilitator.name == "Facilitator"
        
        analyst = agents.get_agent(AgentType.ANALYST_RESPONSE)
        assert analyst is not None
        assert analyst.name == "Response Analyst"
        
        # Test persona agents
        sarah = agents.get_agent("tech_sarah")
        assert sarah is not None
        assert sarah.name == "Sarah"
        
        mike = agents.get_agent("student_mike") 
        assert mike is not None
        assert mike.name == "Mike"
        
    def test_agent_configuration_properties(self, real_config, real_state):
        """Test that agents have correct configuration"""
        agents = VirtualBoardAgents(real_config, real_state)
        
        # Test facilitator
        facilitator = agents.get_agent(AgentType.FACILITATOR)
        assert facilitator.model == "gpt-4.1"
        assert facilitator.instructions is not None
        assert len(facilitator.instructions) > 0
        
        # Test structured output agents
        response_analyst = agents.get_agent(AgentType.ANALYST_RESPONSE)
        assert response_analyst.output_type is not None
        
        bias_moderator = agents.get_agent(AgentType.MODERATOR_BIAS)
        assert bias_moderator.output_type is not None
        
        followup_facilitator = agents.get_agent(AgentType.FACILITATOR_FOLLOWUP)
        assert followup_facilitator.output_type is not None
        
    def test_persona_agent_instructions_contain_background(self, real_config, real_state):
        """Test that persona agents have their background in instructions"""
        agents = VirtualBoardAgents(real_config, real_state)
        
        sarah = agents.get_agent("tech_sarah")
        assert "Software engineer" in sarah.instructions
        assert "efficiency" in sarah.instructions
        assert "privacy" in sarah.instructions
        
        mike = agents.get_agent("student_mike")
        assert "College student" in mike.instructions
        assert "budget-conscious" in mike.instructions
        
        lisa = agents.get_agent("parent_lisa")
        assert "Working mother" in lisa.instructions
        assert "family schedule" in lisa.instructions
        
    def test_orchestrator_has_tools(self, real_config, real_state):
        """Test that orchestrator agent has other agents as tools"""
        agents = VirtualBoardAgents(real_config, real_state)
        
        orchestrator = agents.get_agent(AgentType.ORCHESTRATOR)
        assert orchestrator.tools is not None
        assert len(orchestrator.tools) > 0
        
        # Should have phase transition tool and agent tools
        tool_names = [tool.name for tool in orchestrator.tools if hasattr(tool, 'name')]
        expected_tools = ["ask_facilitator", "ask_followup_facilitator", "ask_analyst", "ask_moderator"]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names or any(expected_tool in tool_name for tool_name in tool_names)
            
    def test_persona_agents_use_mini_model(self, real_config, real_state):
        """Test that persona agents use the smaller model"""
        agents = VirtualBoardAgents(real_config, real_state)
        
        sarah = agents.get_agent("tech_sarah")
        assert sarah.model == "gpt-4.1-mini"
        
        mike = agents.get_agent("student_mike")
        assert mike.model == "gpt-4.1-mini"
        
    def test_get_persona_agents_method(self, real_config, real_state):
        """Test the get_persona_agents helper method"""
        agents = VirtualBoardAgents(real_config, real_state)
        
        persona_agents = agents.get_persona_agents()
        assert len(persona_agents) == 3
        assert "tech_sarah" in persona_agents
        assert "student_mike" in persona_agents
        assert "parent_lisa" in persona_agents
        
        # Verify these are actual Agent objects
        for persona_id, agent in persona_agents.items():
            assert hasattr(agent, 'name')
            assert hasattr(agent, 'instructions')
            assert hasattr(agent, 'model')


class TestAgentPromptLoading:
    """Test that all agent prompts load successfully"""
    
    def test_all_prompts_load_without_error(self, real_config, real_state):
        """Test that creating agents doesn't raise any prompt loading errors"""
        try:
            agents = VirtualBoardAgents(real_config, real_state)
            # If we get here, all prompts loaded successfully
            assert True
        except FileNotFoundError as e:
            pytest.fail(f"Prompt file not found: {e}")
        except Exception as e:
            pytest.fail(f"Error loading prompts: {e}")
            
    def test_agent_instructions_are_non_empty(self, real_config, real_state):
        """Test that all agents have non-empty instructions"""
        agents = VirtualBoardAgents(real_config, real_state)
        
        for agent_id, agent in agents.agents.items():
            assert agent.instructions is not None, f"Agent {agent_id} has None instructions"
            assert len(agent.instructions.strip()) > 0, f"Agent {agent_id} has empty instructions"
            assert len(agent.instructions) > 50, f"Agent {agent_id} has suspiciously short instructions: {len(agent.instructions)} chars"


class TestAgentSystemProperties:
    """Test system-wide properties of the agent setup"""
    
    def test_no_duplicate_agent_names(self, real_config, real_state):
        """Test that all unique agents have unique names (accounting for aliases)"""
        agents = VirtualBoardAgents(real_config, real_state)
        
        # Get unique agent instances (some agent IDs point to same instance)
        unique_agents = {}
        for agent_id, agent in agents.agents.items():
            agent_instance_id = id(agent)
            if agent_instance_id not in unique_agents:
                unique_agents[agent_instance_id] = agent
        
        agent_names = [agent.name for agent in unique_agents.values()]
        assert len(agent_names) == len(set(agent_names)), f"Duplicate agent names found: {agent_names}"
        
    def test_all_agents_have_valid_models(self, real_config, real_state):
        """Test that all agents have valid model specifications"""
        agents = VirtualBoardAgents(real_config, real_state)
        
        valid_models = ["gpt-4.1", "gpt-4.1-mini"]
        
        for agent_id, agent in agents.agents.items():
            assert agent.model in valid_models, f"Agent {agent_id} has invalid model: {agent.model}"
            
    def test_structured_output_agents_configured_correctly(self, real_config, real_state):
        """Test that agents requiring structured outputs are configured correctly"""
        agents = VirtualBoardAgents(real_config, real_state)
        
        # These agents should have output_type specified
        structured_agents = [
            AgentType.ANALYST_RESPONSE,
            AgentType.ANALYST_THEMES, 
            AgentType.MODERATOR_BIAS,
            AgentType.FACILITATOR_FOLLOWUP
        ]
        
        for agent_type in structured_agents:
            agent = agents.get_agent(agent_type)
            assert agent.output_type is not None, f"Agent {agent_type} should have output_type but doesn't"
            
        # These agents should NOT have output_type (return strings)
        string_agents = [
            AgentType.FACILITATOR,
            AgentType.MODERATOR,
            AgentType.ORCHESTRATOR
        ]
        
        for agent_type in string_agents:
            agent = agents.get_agent(agent_type)
            # output_type should be None or not set for string return agents
            assert getattr(agent, 'output_type', None) is None, f"Agent {agent_type} should not have output_type"


# Test to verify system can handle edge cases
class TestAgentEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_agents_system_with_single_persona(self, real_state):
        """Test agent system with minimal configuration"""
        minimal_config = BoardConfig(
            product=ProductConfig(name="Test", description="Test product"),
            hypotheses=[HypothesisConfig(id="H1", description="Test hypothesis")],
            questions=QuestionsConfig(),
            personas=[PersonaConfig(id="p1", name="TestUser", background="Test user")]
        )
        
        agents = VirtualBoardAgents(minimal_config, real_state)
        
        # Should still create all system agents
        assert len(agents.agents) >= 8  # 7 system agents + 1 persona + 1 alias
        assert "p1" in agents.agents
        
    def test_hypothesis_coverage_initialization(self, real_config):
        """Test that hypothesis coverage is properly initialized"""
        state = BoardState()
        # Don't pre-initialize coverage
        
        agents = VirtualBoardAgents(real_config, state)
        
        # The system should work even if coverage isn't pre-initialized
        assert agents.state is state
        assert len(agents.agents) > 0