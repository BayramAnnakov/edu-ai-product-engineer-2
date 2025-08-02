"""
Test individual agent functionality without expensive API calls

This test suite verifies that all agents can be created and configured properly,
but uses mocking to avoid OpenAI API costs. Each agent type is tested individually.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.virtual_board_agents.agents import VirtualBoardAgents
from src.config import BoardConfig, ProductConfig, PersonaConfig, HypothesisConfig, QuestionsConfig
from src.models import BoardState, ResponseAnalysis, BiasCheck, FollowUpQuestion, ThemeCluster
from src.constants import AgentType, Phase
from agents import Agent


@pytest.fixture
def mock_config():
    """Create a mock board configuration"""
    return BoardConfig(
        product=ProductConfig(
            name="Test Product",
            description="A product for testing"
        ),
        hypotheses=[
            HypothesisConfig(id="H1", description="Users want simplicity"),
            HypothesisConfig(id="H2", description="Price matters")
        ],
        questions=QuestionsConfig(),
        personas=[
            PersonaConfig(
                id="p1",
                name="Sarah",
                background="Tech professional, values efficiency"
            ),
            PersonaConfig(
                id="p2", 
                name="Mike",
                background="Student, budget-conscious"
            )
        ]
    )


@pytest.fixture
def mock_state():
    """Create a mock board state"""
    state = BoardState()
    state.hypothesis_coverage = {"H1": 0.2, "H2": 0.3}
    return state


@pytest.fixture
def agents_system(mock_config, mock_state):
    """Create a mocked VirtualBoardAgents system"""
    with patch('src.virtual_board_agents.agents.Agent') as mock_agent_class:
        # Create mock agent instances
        mock_agent = MagicMock()
        mock_agent.as_tool.return_value = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        agents = VirtualBoardAgents(mock_config, mock_state)
        return agents


class TestAgentCreation:
    """Test that all agent types can be created and configured"""
    
    def test_facilitator_agent_creation(self, agents_system):
        """Test that facilitator agent is created correctly"""
        assert AgentType.FACILITATOR in agents_system.agents
        agent = agents_system.agents[AgentType.FACILITATOR]
        assert agent is not None
        
    def test_facilitator_followup_agent_creation(self, agents_system):
        """Test that follow-up facilitator agent is created correctly"""
        assert AgentType.FACILITATOR_FOLLOWUP in agents_system.agents
        agent = agents_system.agents[AgentType.FACILITATOR_FOLLOWUP]
        assert agent is not None
        
    def test_analyst_response_agent_creation(self, agents_system):
        """Test that response analyst agent is created correctly"""
        assert AgentType.ANALYST_RESPONSE in agents_system.agents
        agent = agents_system.agents[AgentType.ANALYST_RESPONSE]
        assert agent is not None
        
    def test_analyst_themes_agent_creation(self, agents_system):
        """Test that theme analyst agent is created correctly"""
        assert AgentType.ANALYST_THEMES in agents_system.agents
        agent = agents_system.agents[AgentType.ANALYST_THEMES]
        assert agent is not None
        
    def test_moderator_bias_agent_creation(self, agents_system):
        """Test that bias moderator agent is created correctly"""
        assert AgentType.MODERATOR_BIAS in agents_system.agents
        agent = agents_system.agents[AgentType.MODERATOR_BIAS]
        assert agent is not None
        
    def test_moderator_agent_creation(self, agents_system):
        """Test that general moderator agent is created correctly"""
        assert AgentType.MODERATOR in agents_system.agents
        agent = agents_system.agents[AgentType.MODERATOR]
        assert agent is not None
        
    def test_orchestrator_agent_creation(self, agents_system):
        """Test that orchestrator agent is created correctly"""
        assert AgentType.ORCHESTRATOR in agents_system.agents
        agent = agents_system.agents[AgentType.ORCHESTRATOR]
        assert agent is not None
        
    def test_persona_agents_creation(self, agents_system):
        """Test that persona agents are created correctly"""
        assert "p1" in agents_system.agents
        assert "p2" in agents_system.agents
        assert agents_system.agents["p1"] is not None
        assert agents_system.agents["p2"] is not None
        
    def test_agent_count(self, agents_system):
        """Test that correct number of agents are created"""
        # Expected agents: FACILITATOR, FACILITATOR_FOLLOWUP, ANALYST_RESPONSE, 
        # ANALYST_THEMES, ANALYST (alias), MODERATOR_BIAS, MODERATOR, 
        # ORCHESTRATOR, p1, p2
        assert len(agents_system.agents) == 10


class TestAgentConfigurationMocking:
    """Test agent configuration with proper mocking (without API calls)"""
    
    @patch('src.virtual_board_agents.agents.load_agent_instructions')
    @patch('src.virtual_board_agents.agents.Agent')
    def test_facilitator_configuration(self, mock_agent_class, mock_load_instructions, mock_config, mock_state):
        """Test facilitator agent configuration"""
        mock_load_instructions.return_value = "Facilitator instructions"
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        agents = VirtualBoardAgents(mock_config, mock_state)
        
        # Verify facilitator was configured correctly
        mock_agent_class.assert_any_call(
            name="Facilitator",
            instructions="Facilitator instructions",
            tools=[],  # Tools list may be empty in current implementation
            model="gpt-4.1"
        )
        mock_load_instructions.assert_any_call(AgentType.FACILITATOR.value)
        
    @patch('src.virtual_board_agents.agents.load_agent_instructions')
    @patch('src.virtual_board_agents.agents.Agent')
    def test_analyst_response_configuration(self, mock_agent_class, mock_load_instructions, mock_config, mock_state):
        """Test response analyst agent configuration"""
        mock_load_instructions.return_value = "Analyst instructions"
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        agents = VirtualBoardAgents(mock_config, mock_state)
        
        # Verify response analyst was configured with structured output
        mock_agent_class.assert_any_call(
            name="Response Analyst",
            instructions="Analyst instructions",
            tools=[],  # Tools might be commented out
            output_type=ResponseAnalysis,
            model="gpt-4.1"
        )
        
    @patch('src.virtual_board_agents.agents.load_agent_instructions')
    @patch('src.virtual_board_agents.agents.Agent')
    def test_bias_moderator_configuration(self, mock_agent_class, mock_load_instructions, mock_config, mock_state):
        """Test bias moderator agent configuration"""
        mock_load_instructions.return_value = "Bias moderator instructions"
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        agents = VirtualBoardAgents(mock_config, mock_state)
        
        # Verify bias moderator was configured with structured output
        mock_agent_class.assert_any_call(
            name="Bias Moderator",
            instructions="Bias moderator instructions",
            tools=[],
            output_type=BiasCheck,
            model="gpt-4.1"
        )


class TestAgentGetterMethods:
    """Test agent retrieval methods"""
    
    def test_get_agent_by_type(self, agents_system):
        """Test getting agents by AgentType"""
        facilitator = agents_system.get_agent(AgentType.FACILITATOR)
        assert facilitator is not None
        
        analyst = agents_system.get_agent(AgentType.ANALYST_RESPONSE)
        assert analyst is not None
        
        moderator = agents_system.get_agent(AgentType.MODERATOR_BIAS)
        assert moderator is not None
        
    def test_get_agent_by_persona_id(self, agents_system):
        """Test getting persona agents by ID"""
        persona1 = agents_system.get_agent("p1")
        assert persona1 is not None
        
        persona2 = agents_system.get_agent("p2")
        assert persona2 is not None
        
    def test_get_nonexistent_agent(self, agents_system):
        """Test getting non-existent agent raises ValueError"""
        with pytest.raises(ValueError, match="Agent nonexistent not found"):
            agents_system.get_agent("nonexistent")


class TestAgentPromptLoading:
    """Test that agent prompts can be loaded correctly"""
    
    @patch('src.virtual_board_agents.agents.load_agent_instructions')
    def test_all_agent_types_have_prompts(self, mock_load_instructions, mock_config, mock_state):
        """Test that all agent types can load their instructions"""
        mock_load_instructions.return_value = "Mock instructions"
        
        with patch('src.virtual_board_agents.agents.Agent'):
            agents = VirtualBoardAgents(mock_config, mock_state)
            
            # Verify that instructions were loaded for all expected agent types
            expected_calls = [
                AgentType.FACILITATOR.value,
                AgentType.FACILITATOR_FOLLOWUP.value,
                AgentType.ANALYST.value,  # For ANALYST_RESPONSE
                AgentType.THEME_ANALYST.value,  # For ANALYST_THEMES
                AgentType.BIAS_MODERATOR.value,  # For MODERATOR_BIAS
                AgentType.MODERATOR.value,
                AgentType.ORCHESTRATOR.value,
            ]
            
            for expected_call in expected_calls:
                mock_load_instructions.assert_any_call(expected_call)
                
            # Verify persona agents were created (with additional parameters)
            # Persona agents call load_agent_instructions with persona_name and persona_background
            # Check that persona instruction loading was called
            persona_calls = [call for call in mock_load_instructions.call_args_list 
                           if call[0][0] == AgentType.PERSONA.value]
            assert len(persona_calls) == 2  # Two personas


class TestAgentInteractions:
    """Test agent interactions without API calls"""
    
    @patch('agents.Runner')
    @patch('src.virtual_board_agents.agents.Agent')
    def test_agent_can_be_called_with_runner(self, mock_agent_class, mock_runner, mock_config, mock_state):
        """Test that agents can be called with Runner (mocked)"""
        # Setup mocks
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_result = MagicMock()
        mock_result.final_output = "Test response"
        mock_runner.run = AsyncMock(return_value=mock_result)
        
        agents = VirtualBoardAgents(mock_config, mock_state)
        facilitator = agents.get_agent(AgentType.FACILITATOR)
        
        # This would be how we'd call the agent in real use
        # result = await Runner.run(facilitator, "Test prompt")
        # But we just verify the agent exists and is configured
        assert facilitator is not None
        
    def test_agent_as_tool_functionality(self, agents_system):
        """Test that agents can be used as tools"""
        facilitator = agents_system.get_agent(AgentType.FACILITATOR)
        
        # Verify that as_tool method exists (it's mocked)
        assert hasattr(facilitator, 'as_tool')
        tool = facilitator.as_tool()
        assert tool is not None


class TestAgentErrorHandling:
    """Test agent error handling scenarios"""
    
    @patch('src.virtual_board_agents.agents.load_agent_instructions')
    @patch('src.virtual_board_agents.agents.Agent')
    def test_agent_creation_with_missing_instructions(self, mock_agent_class, mock_load_instructions, mock_config, mock_state):
        """Test agent creation when instructions loading fails"""
        mock_load_instructions.side_effect = FileNotFoundError("Instructions not found")
        
        # Agent creation should still work (instructions loading is internal)
        # The error would be caught and handled appropriately
        with pytest.raises(FileNotFoundError):
            VirtualBoardAgents(mock_config, mock_state)
            
    def test_agent_system_with_empty_personas(self, mock_state):
        """Test agent system creation with no personas"""
        config_no_personas = BoardConfig(
            product=ProductConfig(name="Test", description="Test"),
            hypotheses=[HypothesisConfig(id="H1", description="Test")],
            questions=QuestionsConfig(),
            personas=[]  # Empty personas list
        )
        
        with patch('src.virtual_board_agents.agents.Agent'):
            agents = VirtualBoardAgents(config_no_personas, mock_state)
            
            # Should still create system agents but no persona agents
            assert AgentType.FACILITATOR in agents.agents
            assert AgentType.ORCHESTRATOR in agents.agents
            # No persona agents should exist
            assert len([k for k in agents.agents.keys() if k.startswith('p')]) == 0


class TestStructuredOutputAgents:
    """Test agents that return structured outputs"""
    
    @patch('src.virtual_board_agents.agents.Agent')
    def test_response_analyst_structured_output(self, mock_agent_class, mock_config, mock_state):
        """Test that response analyst is configured for ResponseAnalysis output"""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        agents = VirtualBoardAgents(mock_config, mock_state)
        
        # Verify the response analyst was created with correct output type
        calls = mock_agent_class.call_args_list
        response_analyst_call = None
        for call in calls:
            if call[1].get('name') == 'Response Analyst':
                response_analyst_call = call
                break
                
        assert response_analyst_call is not None
        assert response_analyst_call[1]['output_type'] == ResponseAnalysis
        
    @patch('src.virtual_board_agents.agents.Agent')
    def test_bias_moderator_structured_output(self, mock_agent_class, mock_config, mock_state):
        """Test that bias moderator is configured for BiasCheck output"""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        agents = VirtualBoardAgents(mock_config, mock_state)
        
        # Verify the bias moderator was created with correct output type
        calls = mock_agent_class.call_args_list
        bias_moderator_call = None
        for call in calls:
            if call[1].get('name') == 'Bias Moderator':
                bias_moderator_call = call
                break
                
        assert bias_moderator_call is not None
        assert bias_moderator_call[1]['output_type'] == BiasCheck
        
    @patch('src.virtual_board_agents.agents.Agent')
    def test_followup_facilitator_structured_output(self, mock_agent_class, mock_config, mock_state):
        """Test that follow-up facilitator is configured for FollowUpQuestion output"""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        agents = VirtualBoardAgents(mock_config, mock_state)
        
        # Verify the follow-up facilitator was created with correct output type
        calls = mock_agent_class.call_args_list
        followup_call = None
        for call in calls:
            if call[1].get('name') == 'Follow-up Facilitator':
                followup_call = call
                break
                
        assert followup_call is not None
        assert followup_call[1]['output_type'] == FollowUpQuestion