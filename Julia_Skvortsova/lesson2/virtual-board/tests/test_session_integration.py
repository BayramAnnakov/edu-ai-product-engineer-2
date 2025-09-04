"""
Integration test for Virtual Board session (mocked to avoid OpenAI costs)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.virtual_board_agents.session import VirtualBoardSession
from src.models import ResponseAnalysis, BiasCheck, FollowUpQuestion, Analysis
from src.config import BoardConfig, ProductConfig, PersonaConfig, HypothesisConfig, QuestionsConfig
from src.constants import Phase, AgentType


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
def mock_session(mock_config):
    """Create a mocked VirtualBoardSession"""
    with patch('src.virtual_board_agents.session.VirtualBoardAgents') as mock_agents, \
         patch('src.virtual_board_agents.session.MemoryManager') as mock_memory, \
         patch('src.virtual_board_agents.session.Runner') as mock_runner:
        
        # Configure memory manager mock
        mock_memory_instance = mock_memory.return_value
        mock_memory_instance.build_persona_context.return_value = "Previous conversation context"
        
        session = VirtualBoardSession(mock_config)
        return session


class TestSessionBasics:
    """Test basic session functionality with mocked agents"""
    
    def test_session_initialization(self, mock_session, mock_config):
        """Test that session initializes correctly"""
        assert mock_session.config == mock_config
        assert mock_session.state.phase == Phase.WARMUP
        assert len(mock_session.state.hypothesis_coverage) == 2
        assert mock_session.state.hypothesis_coverage["H1"] == 0.0
        assert mock_session.state.hypothesis_coverage["H2"] == 0.0
    
    @pytest.mark.asyncio
    async def test_ask_persona_basic(self, mock_session):
        """Test asking a single persona"""
        # Mock the agent and runner
        mock_agent = MagicMock()
        mock_session.agents.get_agent.return_value = mock_agent
        
        # Mock the Runner response
        with patch('src.virtual_board_agents.session.Runner') as mock_runner_class:
            mock_result = MagicMock()
            mock_result.final_output = "I think it's interesting but expensive"
            # Make run async
            mock_runner_class.run = AsyncMock(return_value=mock_result)
            
            response = await mock_session.ask_persona(
                "p1", 
                "What do you think about this product?",
                "Product: Test Product"
            )
            
            assert response == "I think it's interesting but expensive"
            mock_session.agents.get_agent.assert_called_once_with("p1")
            mock_runner_class.run.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_response_with_structured_output(self, mock_session):
        """Test response analysis with structured output"""
        # Mock the analyst agent
        mock_analyst = MagicMock()
        mock_session.agents.get_agent.return_value = mock_analyst
        
        # Mock structured output
        mock_analysis_output = ResponseAnalysis(
            themes=["price_concern", "interest"],
            sentiment=-0.2,
            hypotheses_hit=["H2"],
            key_quotes=["expensive"],
            confidence=0.8
        )
        
        with patch('src.virtual_board_agents.session.Runner') as mock_runner_class:
            mock_result = MagicMock()
            mock_result.final_output = mock_analysis_output
            # Make run async
            mock_runner_class.run = AsyncMock(return_value=mock_result)
            
            analysis = await mock_session.analyze_response(
                "p1",
                "I think it's interesting but expensive",
                "What do you think?"
            )
            
            assert isinstance(analysis, Analysis)
            assert analysis.themes == ["price_concern", "interest"]
            assert analysis.sentiment == -0.2
            assert analysis.hypotheses_hit == ["H2"]
            assert analysis.confidence == 0.8
            
            # Check that analysis was saved
            assert len(mock_session.state.analyses) == 1
    
    @pytest.mark.asyncio
    async def test_check_question_bias(self, mock_session):
        """Test bias checking functionality"""
        mock_bias_moderator = MagicMock()
        mock_session.agents.get_agent.return_value = mock_bias_moderator
        
        # Mock bias check output
        mock_bias_output = BiasCheck(
            has_bias=True,
            bias_type="leading",
            severity="medium",
            recommendation="Rephrase to be more neutral"
        )
        
        with patch('src.virtual_board_agents.session.Runner') as mock_runner_class:
            mock_result = MagicMock()
            mock_result.final_output = mock_bias_output
            # Make run async
            mock_runner_class.run = AsyncMock(return_value=mock_result)
            
            bias_check = await mock_session.check_question_bias(
                "Don't you think this is the best product ever?"
            )
            
            assert isinstance(bias_check, BiasCheck)
            assert bias_check.has_bias is True
            assert bias_check.bias_type == "leading"
            assert bias_check.severity == "medium"
            
            # Verify correct agent was called
            mock_session.agents.get_agent.assert_called_with(AgentType.MODERATOR_BIAS)
    
    @pytest.mark.asyncio
    async def test_generate_followup_needed(self, mock_session):
        """Test follow-up generation when needed"""
        mock_followup_facilitator = MagicMock()
        mock_session.agents.get_agent.return_value = mock_followup_facilitator
        
        # Mock follow-up output
        mock_followup_output = FollowUpQuestion(
            is_needed=True,
            question="Can you elaborate on what makes it expensive?",
            rationale="Response mentioned price concern but wasn't specific",
            target_hypothesis="H2"
        )
        
        with patch('src.virtual_board_agents.session.Runner') as mock_runner_class:
            mock_result = MagicMock()
            mock_result.final_output = mock_followup_output
            # Make run async
            mock_runner_class.run = AsyncMock(return_value=mock_result)
            
            # Create mock analysis
            mock_analysis = Analysis(
                persona_id="p1",
                question="What do you think?",
                themes=["price_concern"],
                sentiment=-0.3,
                hypotheses_hit=["H2"],
                key_quotes=["expensive"],
                confidence=0.6
            )
            
            followup = await mock_session.generate_followup(
                "p1",
                "It's expensive",
                mock_analysis
            )
            
            assert isinstance(followup, FollowUpQuestion)
            assert followup.is_needed is True
            assert "elaborate" in followup.question
            assert followup.target_hypothesis == "H2"
            
            # Verify correct agent was called
            mock_session.agents.get_agent.assert_called_with(AgentType.FACILITATOR_FOLLOWUP)
    
    @pytest.mark.asyncio
    async def test_generate_followup_not_needed(self, mock_session):
        """Test follow-up generation when not needed"""
        mock_followup_facilitator = MagicMock()
        mock_session.agents.get_agent.return_value = mock_followup_facilitator
        
        # Mock follow-up output indicating no follow-up needed
        mock_followup_output = FollowUpQuestion(
            is_needed=False,
            question="none",
            rationale="Response was comprehensive and detailed"
        )
        
        with patch('src.virtual_board_agents.session.Runner') as mock_runner_class:
            mock_result = MagicMock()
            mock_result.final_output = mock_followup_output
            # Make run async
            mock_runner_class.run = AsyncMock(return_value=mock_result)
            
            mock_analysis = Analysis(
                persona_id="p1",
                question="What do you think?",
                themes=["detailed_feedback", "specific_features"],
                sentiment=0.5,
                hypotheses_hit=["H1", "H2"],
                key_quotes=["I love the interface", "Price is reasonable"],
                confidence=0.9
            )
            
            followup = await mock_session.generate_followup(
                "p1",
                "Comprehensive detailed response",
                mock_analysis
            )
            
            assert followup is None  # Should return None when not needed
    
    def test_save_answer(self, mock_session):
        """Test saving answers to state"""
        initial_count = len(mock_session.state.answers)
        
        mock_session.save_answer(
            "p1",
            "What do you think?",
            "I like it"
        )
        
        assert len(mock_session.state.answers) == initial_count + 1
        answer = mock_session.state.answers[-1]
        assert answer.persona_id == "p1"
        assert answer.question == "What do you think?"
        assert answer.response == "I like it"
        assert answer.phase == Phase.WARMUP  # Default phase
    
    def test_save_analysis(self, mock_session):
        """Test saving analysis and updating coverage"""
        analysis = Analysis(
            persona_id="p1",
            question="Test question",
            themes=["theme1"],
            sentiment=0.5,
            hypotheses_hit=["H1", "H2"],
            key_quotes=["quote"],
            confidence=0.8
        )
        
        initial_h1_coverage = mock_session.state.hypothesis_coverage["H1"]
        initial_h2_coverage = mock_session.state.hypothesis_coverage["H2"]
        
        mock_session.save_analysis(analysis)
        
        # Check analysis was saved
        assert len(mock_session.state.analyses) == 1
        assert mock_session.state.analyses[0] == analysis
        
        # Check coverage was updated
        assert mock_session.state.hypothesis_coverage["H1"] > initial_h1_coverage
        assert mock_session.state.hypothesis_coverage["H2"] > initial_h2_coverage
    
    def test_transition_phase(self, mock_session):
        """Test phase transitions"""
        assert mock_session.state.phase == Phase.WARMUP
        
        mock_session.transition_phase(Phase.DIVERGE)
        assert mock_session.state.phase == Phase.DIVERGE
        
        mock_session.transition_phase(Phase.CONVERGE)
        assert mock_session.state.phase == Phase.CONVERGE
    
    def test_get_session_metadata(self, mock_session):
        """Test session metadata generation"""
        metadata = mock_session.get_session_metadata()
        
        assert "session_id" in metadata
        assert "start_time" in metadata
        assert "current_phase" in metadata
        assert "coverage" in metadata
        assert "total_answers" in metadata
        assert "total_analyses" in metadata
        assert "hypothesis_coverage" in metadata
        
        assert metadata["current_phase"] == Phase.WARMUP.value
        assert metadata["total_answers"] == 0
        assert isinstance(metadata["coverage"], float)