"""
Langfuse integration for OpenAI Agents SDK
"""
import os
import structlog
from typing import Optional, Any, Dict
from datetime import datetime
from functools import wraps
from langfuse import Langfuse
from agents import Agent, Runner
import asyncio
import uuid
from src.config import settings

logger = structlog.get_logger()

# Global Langfuse client
_langfuse_client: Optional[Langfuse] = None

def get_langfuse_client() -> Langfuse:
    """Get or create Langfuse client"""
    global _langfuse_client
    if _langfuse_client is None:
        _langfuse_client = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST", "http://localhost:3000"),
        )
        logger.info("Langfuse client initialized", 
                   public_key="***...***",
                   project=settings.services.langfuse.project_name)
    return _langfuse_client

class LangfuseAgentRunner:
    """Wrapper for Agent Runner that adds Langfuse tracing"""
    
    def __init__(self):
        self.langfuse = get_langfuse_client()
        self.runner = Runner()
        self.last_trace_id = None  # Store last trace ID for retrieval
    
    async def run(self, agent: Agent, input_text: str, trace_id: Optional[str] = None, **kwargs) -> Any:
        """Run agent with full Langfuse tracing using v2 API
        
        Args:
            agent: The agent to run
            input_text: The input text for the agent
            trace_id: Optional trace ID to use (if not provided, one will be generated)
            **kwargs: Additional arguments for the runner
        """
        # Use provided trace ID or generate new one
        if not trace_id:
            trace_id = str(uuid.uuid4())
        
        self.last_trace_id = trace_id  # Store for later retrieval
        start_time = datetime.utcnow()
        
        # Create Langfuse trace using v2 API
        langfuse_trace = None
        try:
            langfuse_trace = self.langfuse.trace(
                name=f"agent_run_{agent.name}",
                id=trace_id,
                metadata={
                    "agent_name": agent.name,
                    "agent_model": getattr(agent, 'model', 'unknown'),
                    "tools_count": len(agent.tools) if hasattr(agent, 'tools') and agent.tools else 0,
                    "input_preview": input_text[:100] + "..." if len(input_text) > 100 else input_text,
                    "start_time": start_time.isoformat()
                },
                input={"user_message": input_text}
            )
            
            logger.info("Starting agent run", 
                       agent=agent.name, 
                       trace_id=trace_id,
                       input_preview=input_text[:100] + "..." if len(input_text) > 100 else input_text,
                       tools_count=len(agent.tools) if hasattr(agent, 'tools') and agent.tools else 0)
            
            # Run the agent with increased max_turns  
            result = await self.runner.run(agent, input_text, max_turns=20, **kwargs)
            
            # End timing
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Process and log results
            turns_used = len(result.new_items) if hasattr(result, 'new_items') else 0
            tool_calls = []
            
            # Extract tool calls from the result
            if hasattr(result, 'new_items'):
                for i, item in enumerate(result.new_items):
                    tool_name = "unknown_tool"
                    tool_args = {}
                    tool_result = str(item)
                    
                    # Try to extract tool information
                    if hasattr(item, 'raw_item'):
                        if hasattr(item.raw_item, 'name'):
                            tool_name = item.raw_item.name
                        if hasattr(item.raw_item, 'arguments'):
                            tool_args = getattr(item.raw_item, 'arguments', {})
                    
                    tool_calls.append({
                        "tool": tool_name,
                        "args": tool_args,
                        "result": tool_result[:200] + "..." if len(tool_result) > 200 else tool_result
                    })
                    
                    # Create a span for each tool call using v2 API
                    try:
                        tool_span = langfuse_trace.span(
                            name=f"tool_{tool_name}",
                            input={"arguments": tool_args},
                            output={"result": tool_result},
                            metadata={
                                "tool_index": i,
                                "tool_name": tool_name
                            }
                        )
                        tool_span.end()
                    except Exception as span_e:
                        logger.warning("Failed to create tool span", tool=tool_name, error=str(span_e))
            
            # Get the final output
            final_output = ""
            if hasattr(result, 'final_output'):
                final_output = str(result.final_output)
            else:
                final_output = str(result)
            
            # Create a generation span for the overall agent conversation using v2 API
            try:
                generation = langfuse_trace.generation(
                    name=f"agent_conversation_{agent.name}",
                    model=getattr(agent, 'model', settings.models.default_chat),
                    input={"user_message": input_text},
                    output={"final_response": final_output},
                    usage={
                        "input_tokens": len(input_text) // 4,  # Rough estimate
                        "output_tokens": len(final_output) // 4,  # Rough estimate
                        "total_tokens": (len(input_text) + len(final_output)) // 4
                    },
                    metadata={
                        "turns_used": turns_used,
                        "tool_calls_count": len(tool_calls),
                        "duration_ms": duration_ms
                    }
                )
                generation.end()
            except Exception as gen_e:
                logger.warning("Failed to create generation span", error=str(gen_e))
            
            # Update trace with final results
            langfuse_trace.update(
                output={
                    "final_response": final_output,
                    "turns_used": turns_used,
                    "tool_calls_count": len(tool_calls),
                    "duration_ms": duration_ms
                },
                metadata={
                    "agent_name": agent.name,
                    "end_time": end_time.isoformat(),
                    "duration_ms": duration_ms,
                    "status": "success"
                }
            )
            
            # Flush data to Langfuse
            self.langfuse.flush()
            
            logger.info("Agent run completed successfully", 
                       agent=agent.name, 
                       trace_id=trace_id,
                       duration_ms=duration_ms,
                       turns_used=turns_used,
                       tool_calls_count=len(tool_calls),
                       tool_calls=tool_calls[:3],  # Log first 3 tool calls
                       result_preview=final_output[:200] + "..." if len(final_output) > 200 else final_output)
            
            return result
            
        except Exception as e:
            end_time = datetime.utcnow() 
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Update trace with error information if trace was created
            if langfuse_trace:
                try:
                    langfuse_trace.update(
                        output={
                            "error": str(e),
                            "duration_ms": duration_ms
                        },
                        metadata={
                            "agent_name": agent.name,
                            "end_time": end_time.isoformat(),
                            "duration_ms": duration_ms,
                            "status": "error"
                        }
                    )
                    self.langfuse.flush()
                except Exception as trace_e:
                    logger.warning("Failed to update trace with error", error=str(trace_e))
            
            logger.exception("Agent run failed", 
                           agent=agent.name,
                           trace_id=trace_id, 
                           duration_ms=duration_ms,
                           error=str(e))
            raise
    
    def get_last_trace_id(self) -> Optional[str]:
        """Get the trace ID from the last run"""
        return self.last_trace_id

def trace_agent_tools(agent: Agent) -> Agent:
    """Wrap agent tools with Langfuse tracing (v2 API compatible)"""
    if not hasattr(agent, 'tools') or not agent.tools:
        return agent
    
    logger.info("Wrapping agent tools with tracing", 
               agent=agent.name, 
               tools_count=len(agent.tools))
    
    # Note: Individual tool tracing is handled within the main trace
    # This function is kept for compatibility but doesn't modify tools
    # since the v2 API tracing is done at the conversation level
    
    return agent

# Convenience function to create traced runner
def create_traced_runner() -> LangfuseAgentRunner:
    """Create a Langfuse-traced agent runner"""
    return LangfuseAgentRunner()

# Example usage function
async def run_agent_with_tracing(agent: Agent, input_text: str) -> Any:
    """Run an agent with full Langfuse tracing"""
    runner = create_traced_runner()
    result = await runner.run(agent, input_text)
    return result