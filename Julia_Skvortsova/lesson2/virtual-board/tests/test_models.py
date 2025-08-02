"""
Test Pydantic models and data structures
"""
import pytest
from datetime import datetime
from src.models import (
    Answer, Analysis, BoardState, 
    ResponseAnalysis, ThemeCluster, BiasCheck, FollowUpQuestion
)
from src.constants import Phase


class TestBasicModels:
    """Test core data models"""
    
    def test_answer_creation(self):
        """Test Answer model creation"""
        answer = Answer(
            persona_id="p1",
            question="What do you think?",
            response="I like it",
            phase=Phase.WARMUP
        )
        assert answer.persona_id == "p1"
        assert answer.question == "What do you think?"
        assert answer.response == "I like it"
        assert answer.phase == Phase.WARMUP
        assert isinstance(answer.timestamp, datetime)
    
    def test_analysis_creation(self):
        """Test Analysis model creation"""
        analysis = Analysis(
            persona_id="p1",
            question="What do you think?",
            themes=["positive", "cautious"],
            sentiment=0.3,
            hypotheses_hit=["H1"],
            key_quotes=["I like it"],
            confidence=0.7
        )
        assert analysis.persona_id == "p1"
        assert analysis.themes == ["positive", "cautious"]
        assert analysis.sentiment == 0.3
        assert analysis.hypotheses_hit == ["H1"]
        assert analysis.confidence == 0.7
    
    def test_board_state_creation(self):
        """Test BoardState model creation and methods"""
        state = BoardState()
        assert state.phase == Phase.WARMUP
        assert state.question_index == 0
        assert len(state.answers) == 0
        assert len(state.analyses) == 0
        assert state.coverage_percentage() == 0.0
    
    def test_board_state_add_answer(self):
        """Test adding answer to board state"""
        state = BoardState()
        answer = Answer(
            persona_id="p1",
            question="Test?",
            response="Yes",
            phase=Phase.DIVERGE
        )
        state.add_answer(answer)
        assert len(state.answers) == 1
        assert state.answers[0] == answer
    
    def test_board_state_coverage_calculation(self):
        """Test hypothesis coverage calculation"""
        state = BoardState()
        state.hypothesis_coverage = {"H1": 0.8, "H2": 0.4, "H3": 0.0}
        coverage = state.coverage_percentage()
        assert abs(coverage - 0.4) < 0.001  # (0.8 + 0.4 + 0.0) / 3, allowing floating point precision


class TestStructuredOutputModels:
    """Test agent output models"""
    
    def test_response_analysis_creation(self):
        """Test ResponseAnalysis model"""
        analysis = ResponseAnalysis(
            themes=["pricing", "features"],
            sentiment=0.5,
            hypotheses_hit=["H1", "H2"],
            key_quotes=["It's expensive but good"],
            confidence=0.8
        )
        assert analysis.themes == ["pricing", "features"]
        assert analysis.sentiment == 0.5
        assert analysis.hypotheses_hit == ["H1", "H2"]
        assert analysis.confidence == 0.8
    
    def test_response_analysis_validation(self):
        """Test ResponseAnalysis validation"""
        # Sentiment must be between -1 and 1
        with pytest.raises(ValueError):
            ResponseAnalysis(
                themes=["test"],
                sentiment=2.0,  # Invalid
                hypotheses_hit=[],
                key_quotes=[],
                confidence=0.5
            )
        
        # Confidence must be between 0 and 1
        with pytest.raises(ValueError):
            ResponseAnalysis(
                themes=["test"],
                sentiment=0.0,
                hypotheses_hit=[],
                key_quotes=[],
                confidence=1.5  # Invalid
            )
    
    def test_theme_cluster_creation(self):
        """Test ThemeCluster model"""
        cluster = ThemeCluster(
            theme_name="Price Sensitivity",
            personas_mentioned=["p1", "p2"],
            frequency=5,
            representative_quotes=["Too expensive", "Worth the cost"]
        )
        assert cluster.theme_name == "Price Sensitivity"
        assert cluster.personas_mentioned == ["p1", "p2"]
        assert cluster.frequency == 5
        assert len(cluster.representative_quotes) == 2
    
    def test_bias_check_creation(self):
        """Test BiasCheck model"""
        bias_check = BiasCheck(
            has_bias=True,
            bias_type="leading",
            severity="medium",
            recommendation="Rephrase to be more neutral"
        )
        assert bias_check.has_bias is True
        assert bias_check.bias_type == "leading"
        assert bias_check.severity == "medium"
        assert bias_check.recommendation == "Rephrase to be more neutral"
    
    def test_bias_check_no_bias(self):
        """Test BiasCheck with no bias detected"""
        bias_check = BiasCheck(
            has_bias=False,
            recommendation="Question appears unbiased"
        )
        assert bias_check.has_bias is False
        assert bias_check.bias_type is None
        assert bias_check.severity is None
    
    def test_followup_question_creation(self):
        """Test FollowUpQuestion model"""
        followup = FollowUpQuestion(
            is_needed=True,
            question="Can you elaborate on that?",
            rationale="Response was vague",
            target_hypothesis="H1"
        )
        assert followup.is_needed is True
        assert followup.question == "Can you elaborate on that?"
        assert followup.rationale == "Response was vague"
        assert followup.target_hypothesis == "H1"
    
    def test_followup_question_not_needed(self):
        """Test FollowUpQuestion when not needed"""
        followup = FollowUpQuestion(
            is_needed=False,
            question="none",
            rationale="Response was comprehensive"
        )
        assert followup.is_needed is False
        assert followup.question == "none"
        assert followup.target_hypothesis is None