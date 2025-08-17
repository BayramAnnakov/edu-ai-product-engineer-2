"""
Production features for Virtual Board: guardrails, tracing, and error handling
"""
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import traceback
import logging
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from functools import wraps


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GuardrailType(Enum):
    """Types of guardrails"""
    INPUT_VALIDATION = "input_validation"
    OUTPUT_VALIDATION = "output_validation"
    RATE_LIMIT = "rate_limit"
    CONTENT_FILTER = "content_filter"
    CONSISTENCY_CHECK = "consistency_check"


@dataclass
class GuardrailViolation:
    """Details of a guardrail violation"""
    guardrail_type: GuardrailType
    message: str
    severity: str  # "warning", "error", "critical"
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TraceEvent:
    """Single event in execution trace"""
    timestamp: datetime
    agent_id: str
    event_type: str  # "start", "tool_call", "complete", "error"
    duration_ms: Optional[float] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class Guardrails:
    """Input and output validation for agent interactions"""
    
    def __init__(self):
        self.violations: List[GuardrailViolation] = []
        self.rules: Dict[GuardrailType, List[Callable]] = {
            GuardrailType.INPUT_VALIDATION: [],
            GuardrailType.OUTPUT_VALIDATION: [],
            GuardrailType.CONTENT_FILTER: [],
            GuardrailType.CONSISTENCY_CHECK: []
        }
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Setup default validation rules"""
        # Input validation rules
        self.add_rule(GuardrailType.INPUT_VALIDATION, self._validate_question_length)
        self.add_rule(GuardrailType.INPUT_VALIDATION, self._validate_no_harmful_content)
        
        # Output validation rules
        self.add_rule(GuardrailType.OUTPUT_VALIDATION, self._validate_response_length)
        self.add_rule(GuardrailType.OUTPUT_VALIDATION, self._validate_response_relevance)
        
        # Content filters
        self.add_rule(GuardrailType.CONTENT_FILTER, self._filter_pii)
        self.add_rule(GuardrailType.CONTENT_FILTER, self._filter_inappropriate_content)
    
    def add_rule(self, rule_type: GuardrailType, rule_func: Callable) -> None:
        """Add a validation rule"""
        self.rules[rule_type].append(rule_func)
    
    async def validate_input(self, agent_id: str, input_data: Dict[str, Any]) -> bool:
        """Validate input before sending to agent"""
        for rule in self.rules[GuardrailType.INPUT_VALIDATION]:
            try:
                result = await self._execute_rule(rule, agent_id, input_data)
                if not result:
                    return False
            except Exception as e:
                logger.error(f"Input validation error: {e}")
                self._record_violation(
                    GuardrailType.INPUT_VALIDATION,
                    str(e),
                    "error",
                    {"agent_id": agent_id, "input": input_data}
                )
                return False
        return True
    
    async def validate_output(self, agent_id: str, output_data: Any) -> bool:
        """Validate output from agent"""
        for rule in self.rules[GuardrailType.OUTPUT_VALIDATION]:
            try:
                result = await self._execute_rule(rule, agent_id, output_data)
                if not result:
                    return False
            except Exception as e:
                logger.error(f"Output validation error: {e}")
                self._record_violation(
                    GuardrailType.OUTPUT_VALIDATION,
                    str(e),
                    "error",
                    {"agent_id": agent_id, "output": output_data}
                )
                return False
        return True
    
    async def _execute_rule(self, rule: Callable, agent_id: str, data: Any) -> bool:
        """Execute a single rule"""
        if asyncio.iscoroutinefunction(rule):
            return await rule(agent_id, data)
        return rule(agent_id, data)
    
    def _record_violation(self, guardrail_type: GuardrailType, message: str, 
                         severity: str, context: Dict[str, Any]) -> None:
        """Record a guardrail violation"""
        violation = GuardrailViolation(
            guardrail_type=guardrail_type,
            message=message,
            severity=severity,
            context=context
        )
        self.violations.append(violation)
        logger.warning(f"Guardrail violation: {violation}")
    
    # Default validation rules
    def _validate_question_length(self, agent_id: str, data: Dict[str, Any]) -> bool:
        """Validate question length"""
        question = data.get("question", "")
        if len(question) > 500:
            self._record_violation(
                GuardrailType.INPUT_VALIDATION,
                "Question too long (>500 chars)",
                "warning",
                {"agent_id": agent_id, "length": len(question)}
            )
            return False
        return True
    
    def _validate_no_harmful_content(self, agent_id: str, data: Dict[str, Any]) -> bool:
        """Check for harmful content patterns"""
        # Simplified check - in production would use more sophisticated filtering
        harmful_patterns = ["<script>", "javascript:", "eval(", "exec("]
        content = str(data.get("question", "")).lower()
        
        for pattern in harmful_patterns:
            if pattern in content:
                self._record_violation(
                    GuardrailType.INPUT_VALIDATION,
                    f"Potentially harmful content detected: {pattern}",
                    "critical",
                    {"agent_id": agent_id, "pattern": pattern}
                )
                return False
        return True
    
    def _validate_response_length(self, agent_id: str, output: Any) -> bool:
        """Validate response length"""
        if isinstance(output, str) and len(output) > 2000:
            self._record_violation(
                GuardrailType.OUTPUT_VALIDATION,
                "Response too long (>2000 chars)",
                "warning",
                {"agent_id": agent_id, "length": len(output)}
            )
        return True
    
    def _validate_response_relevance(self, agent_id: str, output: Any) -> bool:
        """Basic relevance check"""
        if isinstance(output, str) and len(output.strip()) < 10:
            self._record_violation(
                GuardrailType.OUTPUT_VALIDATION,
                "Response too short or empty",
                "warning",
                {"agent_id": agent_id, "response": output}
            )
        return True
    
    def _filter_pii(self, agent_id: str, data: Any) -> bool:
        """Filter personally identifiable information"""
        # Simplified PII detection
        import re
        
        content = str(data)
        # Check for email addresses
        if re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content):
            self._record_violation(
                GuardrailType.CONTENT_FILTER,
                "Email address detected",
                "warning",
                {"agent_id": agent_id}
            )
        
        # Check for phone numbers (simplified)
        if re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', content):
            self._record_violation(
                GuardrailType.CONTENT_FILTER,
                "Phone number detected",
                "warning",
                {"agent_id": agent_id}
            )
        
        return True
    
    def _filter_inappropriate_content(self, agent_id: str, data: Any) -> bool:
        """Filter inappropriate content"""
        # In production, would use more sophisticated content filtering
        return True


class ExecutionTracer:
    """Trace agent execution for debugging and monitoring"""
    
    def __init__(self):
        self.traces: List[TraceEvent] = []
        self.active_traces: Dict[str, datetime] = {}
    
    def start_trace(self, agent_id: str, event_type: str, input_data: Optional[Dict[str, Any]] = None) -> str:
        """Start tracing an execution"""
        trace_id = f"{agent_id}_{datetime.now().timestamp()}"
        self.active_traces[trace_id] = datetime.now()
        
        event = TraceEvent(
            timestamp=datetime.now(),
            agent_id=agent_id,
            event_type=f"{event_type}_start",
            input_data=input_data
        )
        self.traces.append(event)
        
        return trace_id
    
    def end_trace(self, trace_id: str, output_data: Optional[Any] = None, error: Optional[str] = None) -> None:
        """End an execution trace"""
        if trace_id not in self.active_traces:
            logger.warning(f"Unknown trace ID: {trace_id}")
            return
        
        start_time = self.active_traces.pop(trace_id)
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        agent_id = trace_id.split("_")[0]
        event = TraceEvent(
            timestamp=datetime.now(),
            agent_id=agent_id,
            event_type="complete" if error is None else "error",
            duration_ms=duration_ms,
            output_data={"result": output_data} if output_data else None,
            error=error
        )
        self.traces.append(event)
    
    def add_tool_call(self, agent_id: str, tool_name: str, args: Dict[str, Any], result: Any) -> None:
        """Record a tool call"""
        event = TraceEvent(
            timestamp=datetime.now(),
            agent_id=agent_id,
            event_type="tool_call",
            metadata={
                "tool_name": tool_name,
                "args": args,
                "result": str(result)[:200]  # Truncate large results
            }
        )
        self.traces.append(event)
    
    def get_agent_traces(self, agent_id: str) -> List[TraceEvent]:
        """Get all traces for a specific agent"""
        return [t for t in self.traces if t.agent_id == agent_id]
    
    def get_error_traces(self) -> List[TraceEvent]:
        """Get all error traces"""
        return [t for t in self.traces if t.event_type == "error"]
    
    def export_traces(self) -> List[Dict[str, Any]]:
        """Export traces for analysis"""
        return [
            {
                "timestamp": t.timestamp.isoformat(),
                "agent_id": t.agent_id,
                "event_type": t.event_type,
                "duration_ms": t.duration_ms,
                "has_error": t.error is not None,
                "metadata": t.metadata
            }
            for t in self.traces
        ]


class ErrorHandler:
    """Centralized error handling with recovery strategies"""
    
    def __init__(self):
        self.error_counts: Dict[str, int] = {}
        self.recovery_strategies: Dict[str, Callable] = {}
        self._setup_default_strategies()
    
    def _setup_default_strategies(self):
        """Setup default recovery strategies"""
        self.recovery_strategies["rate_limit"] = self._handle_rate_limit
        self.recovery_strategies["timeout"] = self._handle_timeout
        self.recovery_strategies["validation"] = self._handle_validation_error
        self.recovery_strategies["api_error"] = self._handle_api_error
    
    async def handle_error(self, error: Exception, context: Dict[str, Any]) -> Optional[Any]:
        """Handle an error with appropriate recovery strategy"""
        error_type = self._classify_error(error)
        agent_id = context.get("agent_id", "unknown")
        
        # Track error frequency
        error_key = f"{agent_id}_{error_type}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # Log error
        logger.error(f"Error in {agent_id}: {error_type} - {str(error)}")
        logger.debug(f"Error context: {context}")
        logger.debug(f"Traceback: {traceback.format_exc()}")
        
        # Apply recovery strategy
        if error_type in self.recovery_strategies:
            try:
                return await self.recovery_strategies[error_type](error, context)
            except Exception as recovery_error:
                logger.error(f"Recovery failed: {recovery_error}")
        
        return None
    
    def _classify_error(self, error: Exception) -> str:
        """Classify error type for appropriate handling"""
        error_str = str(error).lower()
        
        if "rate limit" in error_str:
            return "rate_limit"
        elif "timeout" in error_str or isinstance(error, asyncio.TimeoutError):
            return "timeout"
        elif "validation" in error_str:
            return "validation"
        elif "api" in error_str or "openai" in error_str:
            return "api_error"
        else:
            return "unknown"
    
    async def _handle_rate_limit(self, error: Exception, context: Dict[str, Any]) -> Optional[Any]:
        """Handle rate limit errors with exponential backoff"""
        agent_id = context.get("agent_id", "unknown")
        retry_count = context.get("retry_count", 0)
        
        if retry_count >= 3:
            logger.error(f"Max retries reached for {agent_id}")
            return None
        
        # Exponential backoff
        wait_time = 2 ** retry_count
        logger.info(f"Rate limited. Waiting {wait_time}s before retry...")
        await asyncio.sleep(wait_time)
        
        # Return retry signal
        return {"retry": True, "retry_count": retry_count + 1}
    
    async def _handle_timeout(self, error: Exception, context: Dict[str, Any]) -> Optional[Any]:
        """Handle timeout errors"""
        agent_id = context.get("agent_id", "unknown")
        
        # For timeouts, return a default response
        return {
            "error": "timeout",
            "message": f"Agent {agent_id} timed out. Please try with a simpler request.",
            "fallback": True
        }
    
    async def _handle_validation_error(self, error: Exception, context: Dict[str, Any]) -> Optional[Any]:
        """Handle validation errors"""
        return {
            "error": "validation",
            "message": str(error),
            "suggestion": "Please check input format and try again."
        }
    
    async def _handle_api_error(self, error: Exception, context: Dict[str, Any]) -> Optional[Any]:
        """Handle API errors"""
        # For API errors, log and return graceful degradation
        return {
            "error": "api_error",
            "message": "Service temporarily unavailable",
            "fallback": True
        }


def with_production_features(guardrails: Guardrails, tracer: ExecutionTracer, error_handler: ErrorHandler):
    """Decorator to add production features to agent calls"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract agent_id from args/kwargs
            agent_id = kwargs.get("agent_id", "unknown")
            if len(args) > 1 and isinstance(args[1], str):
                agent_id = args[1]
            
            # Start trace
            trace_id = tracer.start_trace(agent_id, func.__name__, kwargs)
            
            try:
                # Input validation
                if not await guardrails.validate_input(agent_id, kwargs):
                    raise ValueError("Input validation failed")
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Output validation
                if not await guardrails.validate_output(agent_id, result):
                    logger.warning("Output validation failed, but continuing")
                
                # End trace successfully
                tracer.end_trace(trace_id, result)
                
                return result
                
            except Exception as e:
                # Handle error
                recovery_result = await error_handler.handle_error(
                    e, 
                    {"agent_id": agent_id, "function": func.__name__, **kwargs}
                )
                
                # End trace with error
                tracer.end_trace(trace_id, error=str(e))
                
                # If recovery suggests retry
                if recovery_result and recovery_result.get("retry"):
                    kwargs["retry_count"] = recovery_result.get("retry_count", 0)
                    return await wrapper(*args, **kwargs)
                
                # Return recovery result or raise
                if recovery_result and recovery_result.get("fallback"):
                    return recovery_result
                
                raise
        
        return wrapper
    return decorator