"""
Test prompt loading functionality
"""
import pytest
from src.virtual_board_agents.prompts.prompt_loader import load_agent_instructions, load_analysis_prompt
from src.constants import AgentType


class TestPromptLoading:
    """Test that all prompts load correctly"""
    
    def test_load_agent_instructions_facilitator(self):
        """Test facilitator instructions load"""
        instructions = load_agent_instructions(AgentType.FACILITATOR.value)
        assert isinstance(instructions, str)
        assert len(instructions) > 50
        assert "facilitator" in instructions.lower()
    
    def test_load_agent_instructions_analyst(self):
        """Test analyst instructions load"""
        instructions = load_agent_instructions(AgentType.ANALYST.value)
        assert isinstance(instructions, str)
        assert len(instructions) > 50
        assert "analyst" in instructions.lower()
    
    def test_load_agent_instructions_persona_with_variables(self):
        """Test persona instructions with variables"""
        instructions = load_agent_instructions(
            AgentType.PERSONA.value,
            persona_name="Sarah Chen",
            persona_background="Busy parent of two"
        )
        assert isinstance(instructions, str)
        assert "Sarah Chen" in instructions
        assert "Busy parent of two" in instructions
    
    def test_load_analysis_prompt_response_analysis(self):
        """Test response analysis prompt with variables"""
        prompt = load_analysis_prompt(
            "response_analysis",
            response="I really like this product",
            question="What do you think?",
            hypotheses=[{"id": "H1", "description": "Users want simplicity"}],
            persona_name="Sarah",
            persona_background="Tech-savvy user",
            analysis_context="Initial feedback"
        )
        assert isinstance(prompt, str)
        assert "I really like this product" in prompt
        assert "What do you think?" in prompt
        assert "Sarah" in prompt
    
    def test_load_analysis_prompt_bias_check(self):
        """Test bias check prompt"""
        prompt = load_analysis_prompt(
            "bias_check",
            question="Don't you think this is the best product ever?",
            context="Product validation"
        )
        assert isinstance(prompt, str)
        assert "Don't you think this is the best product ever?" in prompt
        assert "bias" in prompt.lower()
    
    def test_load_analysis_prompt_followup(self):
        """Test follow-up prompt generation"""
        prompt = load_analysis_prompt(
            "followup",
            response="It's okay I guess",
            analysis_data={"themes": ["uncertainty"], "confidence": 0.3},
            uncovered_hypotheses=["H1", "H2"],
            phase="diverge"
        )
        assert isinstance(prompt, str)
        assert "It's okay I guess" in prompt
        assert "uncertainty" in prompt
    
    def test_invalid_agent_type_raises_error(self):
        """Test that invalid agent type raises FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            load_agent_instructions("nonexistent_agent")
    
    def test_invalid_analysis_prompt_raises_error(self):
        """Test that invalid analysis prompt raises FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            load_analysis_prompt("nonexistent_prompt")