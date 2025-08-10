"""
Logfire integration for OpenAI Agents SDK with OpenTelemetry
"""
import asyncio
import nest_asyncio
import logfire
import structlog
from typing import Optional
from agents import Runner

# Apply nest_asyncio to handle nested asyncio loops
nest_asyncio.apply()

logger = structlog.get_logger()

# Global logfire configuration
_logfire_configured = False

def configure_logfire(service_name: str = "pm_agent_service", send_to_logfire: bool = False) -> None:
    """Configure Logfire with OpenTelemetry instrumentation for OpenAI Agents SDK"""
    global _logfire_configured
    
    if _logfire_configured:
        return
    
    try:
        # Configure logfire to export traces locally  
        # This will export to console and can be configured for OTLP endpoints
        logfire.configure(
            service_name=service_name,
            send_to_logfire=send_to_logfire,
            # Configure console export for local development
            console=True,
            # Can also configure OTLP endpoint here if needed
            # otlp_endpoint="http://langfuse:3000/api/public/ingestion/otlp"
        )
        
        # Instrument OpenAI Agents SDK to emit OpenTelemetry spans
        logfire.instrument_openai_agents()
        
        # Also instrument OpenAI client if needed
        logfire.instrument_openai()
        
        _logfire_configured = True
        logger.info("✅ Logfire configured with OpenAI Agents SDK instrumentation")
        
    except Exception as e:
        logger.exception("Failed to configure Logfire", error=str(e))
        raise

class LogfireAgentRunner:
    """Agent Runner with Logfire OpenTelemetry instrumentation"""
    
    def __init__(self, service_name: str = "pm_agent_service"):
        # Configure logfire if not already done
        configure_logfire(service_name=service_name)
        
        # Create the standard runner - logfire will automatically instrument it
        self.runner = Runner()
        
        logger.info("LogfireAgentRunner initialized with OpenTelemetry instrumentation")
    
    async def run(self, agent, input_text: str, **kwargs):
        """Run agent - OpenTelemetry tracing happens automatically via logfire instrumentation"""
        try:
            # Add custom span information
            with logfire.span(
                f"agent_run_{agent.name}",
                agent_name=agent.name,
                input_text=input_text[:100] + "..." if len(input_text) > 100 else input_text,
                has_tools=len(agent.tools) > 0 if hasattr(agent, 'tools') else False
            ):
                # The actual agent run - logfire will automatically trace this
                result = await self.runner.run(agent, input_text, **kwargs)
                
                # Log the result
                logfire.info(
                    "Agent run completed",
                    agent_name=agent.name,
                    result_length=len(str(result.final_output)) if hasattr(result, 'final_output') else 0
                )
                
                return result
                
        except Exception as e:
            # Log error with context
            logfire.error(
                "Agent run failed",
                agent_name=agent.name,
                error=str(e)
            )
            raise

def create_logfire_runner(service_name: str = "pm_agent_service") -> LogfireAgentRunner:
    """Create a Logfire-instrumented agent runner"""
    return LogfireAgentRunner(service_name=service_name)

# Example usage function
async def run_agent_with_logfire(agent, input_text: str) -> any:
    """Run an agent with Logfire OpenTelemetry tracing"""
    runner = create_logfire_runner()
    result = await runner.run(agent, input_text)
    return result