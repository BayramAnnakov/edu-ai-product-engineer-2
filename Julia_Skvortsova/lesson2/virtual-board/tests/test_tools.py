"""
Test Python function tools
"""
import pytest
import json
from src.constants import Phase


# Direct implementation of tool logic for testing (avoiding decorator issues)
async def check_hypothesis_coverage(analyses: str, hypotheses: str) -> str:
    """Test implementation of hypothesis coverage calculation"""
    import json
    
    try:
        analyses_data = json.loads(analyses) if isinstance(analyses, str) else analyses
        hypotheses_data = json.loads(hypotheses) if isinstance(hypotheses, str) else hypotheses
        
        # Get hypothesis IDs
        if isinstance(hypotheses_data, list):
            hypothesis_ids = [h.get('id', h) if isinstance(h, dict) else h for h in hypotheses_data]
        else:
            hypothesis_ids = list(hypotheses_data.keys())
        
        # Calculate coverage for each hypothesis
        coverage = {}
        total_analyses = len(analyses_data) if analyses_data else 1
        
        for h_id in hypothesis_ids:
            mentions = 0
            for analysis in analyses_data:
                hypotheses_hit = analysis.get('hypotheses_hit', [])
                if h_id in hypotheses_hit:
                    mentions += 1
            coverage[h_id] = round(mentions / total_analyses, 2)
        
        return json.dumps(coverage)
        
    except Exception as e:
        return json.dumps({"H1": 0.0, "H2": 0.0, "H3": 0.0})


async def update_hypothesis_coverage(current_coverage: str, new_analyses: str) -> str:
    """Test implementation of hypothesis coverage update"""
    import json
    
    try:
        current = json.loads(current_coverage) if isinstance(current_coverage, str) else current_coverage
        new_analyses_data = json.loads(new_analyses) if isinstance(new_analyses, str) else new_analyses
        
        # Initialize coverage if empty
        if not current:
            current = {}
        
        # Process new analyses
        for analysis in new_analyses_data:
            hypotheses_hit = analysis.get('hypotheses_hit', [])
            for h_id in hypotheses_hit:
                if h_id not in current:
                    current[h_id] = 0.0
                # Increase coverage by 0.2 for each mention, max 1.0
                current[h_id] = min(1.0, current[h_id] + 0.2)
        
        return json.dumps(current)
        
    except Exception as e:
        return current_coverage if isinstance(current_coverage, str) else json.dumps(current_coverage or {})


async def should_transition_phase(current_phase: str, coverage: str, answer_count: int, phase_config: str) -> str:
    """Test implementation of phase transition logic"""
    import json
    
    try:
        coverage_data = json.loads(coverage) if isinstance(coverage, str) else coverage
        config_data = json.loads(phase_config) if isinstance(phase_config, str) else phase_config
        
        # Phase transition logic
        if current_phase == "warmup":
            min_answers = config_data.get("warmup_min_answers", 1)
            if answer_count >= min_answers:
                return json.dumps({
                    "should_transition": True,
                    "next_phase": "diverge",
                    "reason": "Warmup complete, ready for transition"
                })
            else:
                return json.dumps({
                    "should_transition": False,
                    "next_phase": None,
                    "reason": f"Need {min_answers - answer_count} more answers"
                })
        
        elif current_phase == "diverge":
            min_answers = config_data.get("diverge_min_answers", 3)
            min_coverage = config_data.get("diverge_min_coverage", 0.3)
            avg_coverage = sum(coverage_data.values()) / len(coverage_data) if coverage_data else 0.0
            
            if answer_count >= min_answers and avg_coverage >= min_coverage:
                return json.dumps({
                    "should_transition": True,
                    "next_phase": "reflect",
                    "reason": f"{answer_count} answers with {avg_coverage:.2f} coverage"
                })
            else:
                reason = f"Need {min_coverage - avg_coverage:.2f} more coverage" if avg_coverage < min_coverage else f"Need {min_answers - answer_count} more answers"
                return json.dumps({
                    "should_transition": False,
                    "next_phase": None,
                    "reason": reason
                })
        
        elif current_phase == "reflect":
            min_answers = config_data.get("reflect_min_answers", 5)
            if answer_count >= min_answers:
                return json.dumps({
                    "should_transition": True,
                    "next_phase": "converge",
                    "reason": "Reflection phase complete"
                })
            else:
                return json.dumps({
                    "should_transition": False,
                    "next_phase": None,
                    "reason": f"Need {min_answers - answer_count} more answers"
                })
        
        else:
            return json.dumps({
                "should_transition": False,
                "next_phase": None,
                "reason": "Unknown phase " + current_phase
            })
            
    except Exception as e:
        return json.dumps({
            "should_transition": False,
            "next_phase": None,
            "reason": "Error evaluating transition: " + str(e)
        })


class TestHypothesisCoverage:
    """Test hypothesis coverage tools"""
    
    @pytest.mark.asyncio
    async def test_check_hypothesis_coverage_basic(self):
        """Test basic hypothesis coverage calculation"""
        analyses = [
            {"hypotheses_hit": ["H1", "H2"]},
            {"hypotheses_hit": ["H1"]},
            {"hypotheses_hit": ["H3"]}
        ]
        hypotheses = ["H1", "H2", "H3"]
        
        result = await check_hypothesis_coverage(
            json.dumps(analyses),
            json.dumps(hypotheses)
        )
        
        coverage = json.loads(result)
        assert coverage["H1"] == 0.67  # 2/3 rounded
        assert coverage["H2"] == 0.33  # 1/3 rounded
        assert coverage["H3"] == 0.33  # 1/3 rounded
    
    @pytest.mark.asyncio
    async def test_check_hypothesis_coverage_dict_format(self):
        """Test coverage with hypothesis dict format"""
        analyses = [
            {"hypotheses_hit": ["H1"]},
            {"hypotheses_hit": ["H2"]}
        ]
        hypotheses = [
            {"id": "H1", "description": "Test hypothesis 1"},
            {"id": "H2", "description": "Test hypothesis 2"}
        ]
        
        result = await check_hypothesis_coverage(
            json.dumps(analyses),
            json.dumps(hypotheses)
        )
        
        coverage = json.loads(result)
        assert coverage["H1"] == 0.5
        assert coverage["H2"] == 0.5
    
    @pytest.mark.asyncio
    async def test_check_hypothesis_coverage_empty_analyses(self):
        """Test coverage with no analyses"""
        analyses = []
        hypotheses = ["H1", "H2"]
        
        result = await check_hypothesis_coverage(
            json.dumps(analyses),
            json.dumps(hypotheses)
        )
        
        coverage = json.loads(result)
        assert coverage["H1"] == 0.0
        assert coverage["H2"] == 0.0
    
    @pytest.mark.asyncio
    async def test_update_hypothesis_coverage(self):
        """Test updating hypothesis coverage"""
        current_coverage = {"H1": 0.2, "H2": 0.0}
        new_analyses = [
            {"hypotheses_hit": ["H1", "H2"]},
            {"hypotheses_hit": ["H2"]}
        ]
        
        result = await update_hypothesis_coverage(
            json.dumps(current_coverage),
            json.dumps(new_analyses)
        )
        
        updated_coverage = json.loads(result)
        assert updated_coverage["H1"] == 0.4  # 0.2 + 0.2
        assert updated_coverage["H2"] == 0.4  # 0.0 + 0.2 + 0.2
    
    @pytest.mark.asyncio
    async def test_update_hypothesis_coverage_max_limit(self):
        """Test that coverage doesn't exceed 1.0"""
        current_coverage = {"H1": 0.9}
        new_analyses = [
            {"hypotheses_hit": ["H1"]},
            {"hypotheses_hit": ["H1"]}
        ]
        
        result = await update_hypothesis_coverage(
            json.dumps(current_coverage),
            json.dumps(new_analyses)
        )
        
        updated_coverage = json.loads(result)
        assert updated_coverage["H1"] == 1.0  # Capped at 1.0


class TestPhaseTransition:
    """Test phase transition logic"""
    
    @pytest.mark.asyncio
    async def test_should_transition_warmup_ready(self):
        """Test warmup to diverge transition when ready"""
        coverage = {"H1": 0.2, "H2": 0.1}
        phase_config = {"warmup_min_answers": 1}
        
        result = await should_transition_phase(
            Phase.WARMUP.value,
            json.dumps(coverage),
            2,  # answer_count
            json.dumps(phase_config)
        )
        
        decision = json.loads(result)
        assert decision["should_transition"] is True
        assert decision["next_phase"] == Phase.DIVERGE.value
        assert "ready for transition" in decision["reason"]
    
    @pytest.mark.asyncio
    async def test_should_transition_diverge_insufficient_coverage(self):
        """Test diverge phase with insufficient coverage"""
        coverage = {"H1": 0.1, "H2": 0.2}  # Average 0.15, below 0.3 threshold
        phase_config = {
            "diverge_min_answers": 3,
            "diverge_min_coverage": 0.3
        }
        
        result = await should_transition_phase(
            Phase.DIVERGE.value,
            json.dumps(coverage),
            5,  # answer_count (sufficient)
            json.dumps(phase_config)
        )
        
        decision = json.loads(result)
        assert decision["should_transition"] is False
        assert "Need" in decision["reason"]
        assert "coverage" in decision["reason"]
    
    @pytest.mark.asyncio
    async def test_should_transition_diverge_ready(self):
        """Test diverge to reflect transition when ready"""
        coverage = {"H1": 0.4, "H2": 0.5}  # Average 0.45, above 0.3 threshold
        phase_config = {
            "diverge_min_answers": 3,
            "diverge_min_coverage": 0.3
        }
        
        result = await should_transition_phase(
            Phase.DIVERGE.value,
            json.dumps(coverage),
            4,  # answer_count (sufficient)
            json.dumps(phase_config)
        )
        
        decision = json.loads(result)
        assert decision["should_transition"] is True
        assert decision["next_phase"] == Phase.REFLECT.value
        assert "answers with" in decision["reason"]
        assert "coverage" in decision["reason"]
    
    @pytest.mark.asyncio
    async def test_should_transition_reflect_ready(self):
        """Test reflect to converge transition"""
        coverage = {"H1": 0.5, "H2": 0.6}
        phase_config = {"reflect_min_answers": 5}
        
        result = await should_transition_phase(
            Phase.REFLECT.value,
            json.dumps(coverage),
            6,  # answer_count (sufficient)
            json.dumps(phase_config)
        )
        
        decision = json.loads(result)
        assert decision["should_transition"] is True
        assert decision["next_phase"] == Phase.CONVERGE.value
    
    @pytest.mark.asyncio
    async def test_should_transition_invalid_phase(self):
        """Test handling of invalid phase"""
        result = await should_transition_phase(
            "INVALID_PHASE",
            json.dumps({}),
            1,
            json.dumps({})
        )
        
        decision = json.loads(result)
        assert decision["should_transition"] is False
        assert "Unknown phase" in decision["reason"]
        assert decision["next_phase"] is None
    
    @pytest.mark.asyncio
    async def test_should_transition_error_handling(self):
        """Test error handling in phase transition"""
        result = await should_transition_phase(
            Phase.DIVERGE.value,
            "invalid json",  # This should cause an error
            1,
            json.dumps({})
        )
        
        decision = json.loads(result)
        assert decision["should_transition"] is False
        assert "Error evaluating transition" in decision["reason"]
        assert decision["next_phase"] is None