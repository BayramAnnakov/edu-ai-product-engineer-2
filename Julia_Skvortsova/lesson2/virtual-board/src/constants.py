from enum import Enum


class Phase(str, Enum):
    """Phases of the virtual board session"""
    WARMUP = "warmup"
    DIVERGE = "diverge"
    REFLECT = "reflect"
    CROSS_PROBE = "cross_probe"
    CONVERGE = "converge"
    CLOSURE = "closure"


class AgentType(str, Enum):
    """Types of agents in the virtual board system"""
    FACILITATOR = "facilitator"
    FACILITATOR_FOLLOWUP = "facilitator_followup"
    ANALYST = "analyst"
    ANALYST_RESPONSE = "analyst_response"
    ANALYST_THEMES = "analyst_themes"
    MODERATOR = "moderator"
    MODERATOR_BIAS = "moderator_bias"
    ORCHESTRATOR = "orchestrator"
    PERSONA = "persona"
    THEME_ANALYST = "theme_analyst"
    BIAS_MODERATOR = "bias_moderator"


class MemoryEntryType(str, Enum):
    """Types of memory entries"""
    RESPONSE = "response"
    QUESTION = "question"
    INSIGHT = "insight"
    TRADEOFF = "tradeoff"
    ANALYSIS = "analysis"
    CLUSTER = "cluster"
    HYPOTHESIS = "hypothesis"
    BIAS_CHECK = "bias_check"
    PERSONA_DRIFT = "persona_drift"
    REDUNDANCY_CHECK = "redundancy_check"