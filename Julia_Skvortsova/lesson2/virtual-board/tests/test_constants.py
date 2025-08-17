"""
Test constants and enums
"""
import pytest
from src.constants import Phase, AgentType, MemoryEntryType


class TestPhaseEnum:
    """Test Phase enumeration"""
    
    def test_phase_values(self):
        """Test that all expected phases exist with correct values"""
        assert Phase.WARMUP.value == "warmup"
        assert Phase.DIVERGE.value == "diverge"
        assert Phase.REFLECT.value == "reflect"
        assert Phase.CROSS_PROBE.value == "cross_probe"
        assert Phase.CONVERGE.value == "converge"
        assert Phase.CLOSURE.value == "closure"
    
    def test_phase_order(self):
        """Test typical phase progression"""
        phases = [Phase.WARMUP, Phase.DIVERGE, Phase.REFLECT, Phase.CONVERGE, Phase.CLOSURE]
        
        # Should be able to iterate through phases
        for i, phase in enumerate(phases[:-1]):
            next_phase = phases[i + 1]
            assert phase != next_phase
    
    def test_phase_string_conversion(self):
        """Test that phases can be used as strings"""
        assert str(Phase.DIVERGE) == "Phase.DIVERGE"  # Enum string representation
        assert Phase.DIVERGE.value == "diverge"  # Actual value
        assert f"{Phase.CONVERGE.value}" == "converge"
    
    def test_phase_comparison(self):
        """Test phase comparison"""
        assert Phase.WARMUP == Phase.WARMUP
        assert Phase.WARMUP != Phase.DIVERGE
        assert Phase.DIVERGE.value == "diverge"


class TestAgentTypeEnum:
    """Test AgentType enumeration"""
    
    def test_basic_agent_types(self):
        """Test basic agent types"""
        assert AgentType.FACILITATOR.value == "facilitator"
        assert AgentType.ANALYST.value == "analyst"
        assert AgentType.MODERATOR.value == "moderator"
        assert AgentType.ORCHESTRATOR.value == "orchestrator"
        assert AgentType.PERSONA.value == "persona"
    
    def test_specialized_agent_types(self):
        """Test specialized agent types"""
        assert AgentType.FACILITATOR_FOLLOWUP.value == "facilitator_followup"
        assert AgentType.ANALYST_RESPONSE.value == "analyst_response"
        assert AgentType.ANALYST_THEMES.value == "analyst_themes"
        assert AgentType.MODERATOR_BIAS.value == "moderator_bias"
        assert AgentType.THEME_ANALYST.value == "theme_analyst"
        assert AgentType.BIAS_MODERATOR.value == "bias_moderator"
    
    def test_agent_type_uniqueness(self):
        """Test that all agent types are unique"""
        values = [agent_type.value for agent_type in AgentType]
        assert len(values) == len(set(values))  # No duplicates
    
    def test_agent_type_string_usage(self):
        """Test using agent types as strings"""
        facilitator_type = AgentType.FACILITATOR
        assert facilitator_type.value == "facilitator"
        assert str(facilitator_type) == "AgentType.FACILITATOR"


class TestMemoryEntryTypeEnum:
    """Test MemoryEntryType enumeration"""
    
    def test_memory_entry_types(self):
        """Test all memory entry types"""
        assert MemoryEntryType.RESPONSE.value == "response"
        assert MemoryEntryType.QUESTION.value == "question"
        assert MemoryEntryType.INSIGHT.value == "insight"
        assert MemoryEntryType.TRADEOFF.value == "tradeoff"
        assert MemoryEntryType.ANALYSIS.value == "analysis"
        assert MemoryEntryType.CLUSTER.value == "cluster"
        assert MemoryEntryType.HYPOTHESIS.value == "hypothesis"
        assert MemoryEntryType.BIAS_CHECK.value == "bias_check"
        assert MemoryEntryType.PERSONA_DRIFT.value == "persona_drift"
        assert MemoryEntryType.REDUNDANCY_CHECK.value == "redundancy_check"
    
    def test_memory_entry_type_coverage(self):
        """Test that we have memory types for all major operations"""
        # Should have types for all major session components
        required_types = {
            "response", "question", "analysis", "bias_check", 
            "persona_drift", "insight", "cluster"
        }
        
        available_types = {entry_type.value for entry_type in MemoryEntryType}
        
        assert required_types.issubset(available_types)


class TestEnumIntegration:
    """Test integration between different enums"""
    
    def test_phase_agent_compatibility(self):
        """Test that phases work with agent types"""
        # Should be able to create mappings
        phase_agents = {
            Phase.WARMUP: [AgentType.FACILITATOR, AgentType.MODERATOR],
            Phase.DIVERGE: [AgentType.FACILITATOR, AgentType.ANALYST, AgentType.MODERATOR],
            Phase.CONVERGE: [AgentType.FACILITATOR, AgentType.ANALYST]
        }
        
        assert len(phase_agents) == 3
        assert AgentType.FACILITATOR in phase_agents[Phase.WARMUP]
    
    def test_enum_as_dict_keys(self):
        """Test using enums as dictionary keys"""
        phase_config = {
            Phase.DIVERGE: {"min_answers": 3, "min_coverage": 0.3},
            Phase.CONVERGE: {"min_answers": 5}
        }
        
        assert phase_config[Phase.DIVERGE]["min_answers"] == 3
        assert phase_config[Phase.CONVERGE]["min_answers"] == 5
    
    def test_enum_serialization(self):
        """Test that enums can be serialized"""
        import json
        
        # Should be able to convert to JSON-serializable format
        data = {
            "phase": Phase.DIVERGE.value,
            "agent": AgentType.ANALYST.value,
            "entry_type": MemoryEntryType.ANALYSIS.value
        }
        
        json_str = json.dumps(data)
        loaded_data = json.loads(json_str)
        
        assert loaded_data["phase"] == "diverge"
        assert loaded_data["agent"] == "analyst"
        assert loaded_data["entry_type"] == "analysis"
    
    def test_enum_validation(self):
        """Test enum validation with invalid values"""
        # Test that invalid phase values can be detected
        valid_phases = {phase.value for phase in Phase}
        assert "diverge" in valid_phases
        assert "invalid_phase" not in valid_phases
        
        # Test that invalid agent types can be detected
        valid_agents = {agent.value for agent in AgentType}
        assert "facilitator" in valid_agents
        assert "invalid_agent" not in valid_agents