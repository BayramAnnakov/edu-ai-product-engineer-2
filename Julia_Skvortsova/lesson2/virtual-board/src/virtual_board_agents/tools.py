"""
Tool definitions for Virtual Board agents

This file contains only Python function tools that perform actual calculations.
Analysis tools (bias checking, response analysis, etc.) are now handled by 
specialized agents with structured outputs defined in models.py.
"""
import json
from agents import function_tool
from ..constants import Phase


# Python Function Tools - These perform actual calculations and data manipulation

@function_tool
async def check_hypothesis_coverage(
    analyses: str,
    hypotheses: str
) -> str:
    """
    Calculate coverage percentage for each hypothesis based on analyses.
    
    Args:
        analyses: JSON string of analysis dictionaries
        hypotheses: JSON string of hypothesis dictionaries
        
    Returns:
        JSON string mapping hypothesis ID to coverage percentage
    """
    print("🔧 check_hypothesis_coverage tool called!")
    
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
        print(f"Coverage calculation error: {e}")
        # Return zero coverage for all hypotheses
        if isinstance(hypotheses, str):
            try:
                hypotheses_data = json.loads(hypotheses)
                if isinstance(hypotheses_data, list):
                    hypothesis_ids = [h.get('id', h) if isinstance(h, dict) else h for h in hypotheses_data]
                else:
                    hypothesis_ids = list(hypotheses_data.keys())
                return json.dumps({h_id: 0.0 for h_id in hypothesis_ids})
            except:
                pass
        return json.dumps({"H1": 0.0, "H2": 0.0, "H3": 0.0})


@function_tool
async def update_hypothesis_coverage(
    current_coverage: str,
    new_analyses: str
) -> str:
    """
    Update hypothesis coverage based on new analyses.
    
    Args:
        current_coverage: JSON string of current coverage percentages
        new_analyses: JSON string of new analyses to incorporate
        
    Returns:
        JSON string of updated coverage percentages
    """
    print("🔧 update_hypothesis_coverage tool called!")
    
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
        print(f"Coverage update error: {e}")
        # Return current coverage unchanged
        return current_coverage if isinstance(current_coverage, str) else json.dumps(current_coverage or {})


@function_tool
async def should_transition_phase(
    current_phase: str,
    coverage: str,
    answer_count: int,
    phase_config: str
) -> str:
    """
    Determine if it's time to transition to the next phase.
    This is a Python function tool that applies transition logic.
    
    Args:
        current_phase: Current discussion phase
        coverage: JSON string of hypothesis coverage percentages
        answer_count: Number of answers collected
        phase_config: JSON string of phase configuration settings
        
    Returns:
        JSON string with should_transition (bool), reason, and next_phase
    """
    print("🔧 should_transition_phase tool called!")
    
    try:
        coverage_data = json.loads(coverage) if isinstance(coverage, str) else coverage
        config_data = json.loads(phase_config) if isinstance(phase_config, str) else phase_config
        
        # Use Phase enum for transitions
        # phase_order = [Phase.WARMUP, Phase.DIVERGE, Phase.REFLECT, Phase.CROSS_PROBE, Phase.CONVERGE, Phase.CLOSURE]
        phase_order = [Phase.WARMUP, Phase.DIVERGE, Phase.REFLECT, Phase.CONVERGE, Phase.CLOSURE]
        
        # Find current phase and next phase
        try:
            current_phase_enum = Phase(current_phase.lower())
            current_index = phase_order.index(current_phase_enum)
            next_phase = phase_order[current_index + 1] if current_index < len(phase_order) - 1 else None
        except (ValueError, IndexError):
            return json.dumps({
                "should_transition": False,
                "reason": f"Unknown phase: {current_phase}",
                "next_phase": None
            })
        
        # Calculate average coverage  
        avg_coverage = sum(coverage_data.values()) / len(coverage_data) if coverage_data else 0.0
        
        # Get phase-specific configuration with defaults
        phase_key = current_phase_enum.value
        phase_settings = {
            Phase.WARMUP.value: {
                "min_answers": config_data.get(f"{phase_key}_min_answers", 1),
                "criteria": "none"  # Always ready to transition
            },
            Phase.DIVERGE.value: {
                "min_answers": config_data.get(f"{phase_key}_min_answers", 3),
                "min_coverage": config_data.get(f"{phase_key}_min_coverage", 0.3),
                "criteria": "answers_and_coverage"
            },
            Phase.REFLECT.value: {
                "min_answers": config_data.get(f"{phase_key}_min_answers", 5),
                "criteria": "answers_only"
            },
            Phase.CROSS_PROBE.value: {
                "min_coverage": config_data.get(f"{phase_key}_min_coverage", 0.7),
                "criteria": "coverage_only"
            },
            Phase.CONVERGE.value: {
                "min_answers": config_data.get(f"{phase_key}_min_answers", 8),
                "criteria": "answers_only"
            },
            Phase.CLOSURE.value: {
                "criteria": "none"  # Always ready to close
            }
        }
        
        settings = phase_settings.get(phase_key, {"criteria": "none"})
        criteria = settings.get("criteria", "none")
        
        # Apply transition logic based on criteria
        should_transition = False
        reason = ""
        
        if criteria == "answers_and_coverage":
            min_answers = settings["min_answers"]
            min_coverage = settings["min_coverage"]
            if answer_count >= min_answers and avg_coverage >= min_coverage:
                should_transition = True
                reason = f"Collected {answer_count} answers with {avg_coverage:.1%} coverage"
            else:
                reason = f"Need {min_answers} answers and {min_coverage:.1%} coverage (current: {answer_count}, {avg_coverage:.1%})"
        
        elif criteria == "answers_only":
            min_answers = settings["min_answers"]
            if answer_count >= min_answers:
                should_transition = True
                reason = f"Completed {phase_key} with {answer_count} responses"
            else:
                reason = f"Need {min_answers} responses (current: {answer_count})"
        
        elif criteria == "coverage_only":
            min_coverage = settings["min_coverage"]
            if avg_coverage >= min_coverage:
                should_transition = True
                reason = f"Achieved {avg_coverage:.1%} coverage in {phase_key}"
            else:
                reason = f"Need {min_coverage:.1%} coverage (current: {avg_coverage:.1%})"
        
        elif criteria == "none":
            should_transition = True
            reason = f"Phase {phase_key} ready for transition"
        
        else:
            reason = f"Unknown criteria for phase {phase_key}"
        
        return json.dumps({
            "should_transition": should_transition,
            "reason": reason,
            "next_phase": next_phase.value if next_phase else None
        })
        
    except Exception as e:
        print(f"Phase transition error: {e}")
        return json.dumps({
            "should_transition": False,
            "reason": f"Error evaluating transition: {str(e)}",
            "next_phase": None
        })