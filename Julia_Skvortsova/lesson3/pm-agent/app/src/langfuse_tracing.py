"""
Configure Langfuse tracing for OpenAI Agents SDK
"""
import os
import structlog
from typing import Optional, Dict, Any
from agents import TracingProcessor, add_trace_processor
from langfuse import Langfuse
from datetime import datetime

logger = structlog.get_logger()

class LangfuseTracingProcessor(TracingProcessor):
    """Custom tracing processor to send OpenAI Agents SDK traces to Langfuse"""
    
    def __init__(self):
        """Initialize Langfuse client with threading support"""
        super().__init__()
        self._traces = {}  # Store active traces
        self._thread_local_langfuse = None
        
        try:
            # Store connection params for thread-safe access
            self._langfuse_config = {
                "public_key": os.getenv("LANGFUSE_PUBLIC_KEY"),
                "secret_key": os.getenv("LANGFUSE_SECRET_KEY"),
                "host": os.getenv("LANGFUSE_HOST", "http://langfuse:3000"),
            }
            
            # Test initial connection
            self.langfuse = Langfuse(**self._langfuse_config)
            logger.info("Langfuse tracing processor initialized")
        except Exception as e:
            logger.exception("Failed to initialize Langfuse tracing processor")
            self.langfuse = None
    
    def on_trace_start(self, trace) -> None:
        """Called when a trace starts"""
        if not self.langfuse:
            return
            
        try:
            trace_id = str(trace.trace_id)  # Convert to string
            logger.info(f"🟢 TRACE START: {trace_id[:12]} (full: {trace_id})")
            
            # Create a new Langfuse trace
            langfuse_trace = self.langfuse.trace(
                name=f"agent_run_{trace_id[:8]}",  # Shorten name
                metadata={
                    "trace_id": trace_id,
                    "start_time": datetime.now().isoformat(),  # Fix deprecated utcnow
                }
            )
            self._traces[trace_id] = langfuse_trace
            
            # Note: Avoid immediate flush - let it batch for better performance
            
            logger.info("✅ Trace created and flushed successfully", trace_id=trace_id[:12])
        except Exception as e:
            logger.error("❌ CRITICAL: Failed to start trace", 
                        trace_id=getattr(trace, 'trace_id', 'unknown'),
                        error=str(e)[:400],
                        error_type=type(e).__name__)
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
    
    def on_trace_end(self, trace) -> None:
        """Called when a trace ends"""
        trace_id = str(trace.trace_id)
        if not self.langfuse or trace_id not in self._traces:
            return
            
        try:
            langfuse_trace = self._traces.get(trace_id)
            if langfuse_trace:
                langfuse_trace.update(
                    output={"status": "completed"},
                    metadata={
                        "end_time": datetime.now().isoformat(),  # Fix deprecated utcnow
                        "trace_id": trace_id
                    }
                )
                # Clean up
                del self._traces[trace_id]
                
                # CRITICAL: Single flush at trace end to send all data
                self.langfuse.flush()
                
                logger.debug("Trace ended and flushed", trace_id=trace_id[:12])
        except Exception as e:
            logger.error("Failed to end trace", 
                        trace_id=trace_id,
                        error=str(e)[:200])
    
    def on_span_start(self, span) -> None:
        """Called when a span starts - identify and create spans for tool calls"""
        try:
            trace_id = str(span.trace_id)
            span_id = str(span.span_id)
            
            # Get the Langfuse trace for this span
            langfuse_trace = self._traces.get(trace_id)
            if not langfuse_trace:
                logger.debug("No langfuse trace found for span", trace_id=trace_id[:12])
                return
            
            # Get the actual span data using export()
            try:
                export_data = span.export()
                span_data = export_data.get('span_data', {})
                span_type = span_data.get('type', 'unknown')
                span_name = span_data.get('name', 'unknown')
                
                logger.debug("Span detected", 
                           trace_id=trace_id[:12],
                           span_id=span_id[:12], 
                           span_type=span_type,
                           span_name=span_name[:20])
                
                # Only create Langfuse spans for function calls (tool calls)
                if span_type == 'function':
                    # This is a tool call!
                    logger.info(f"🔧 Creating tool call span for: {span_name}")
                    try:
                        langfuse_span = langfuse_trace.span(
                            name=f"tool_{span_name}",
                            metadata={
                                "span_id": span_id,
                                "span_type": span_type,
                                "tool_name": span_name,
                                "start_time": datetime.now().isoformat()
                            }
                        )
                        
                        # Store span for later update
                        if not hasattr(langfuse_trace, '_spans'):
                            langfuse_trace._spans = {}
                        langfuse_trace._spans[span_id] = langfuse_span
                        
                        # Note: Avoid immediate flush - let it batch
                        
                        logger.info("✅ Tool call span created and flushed successfully", 
                                   trace_id=trace_id[:12], 
                                   span_id=span_id[:12],
                                   tool_name=span_name)
                    except Exception as span_error:
                        logger.error(f"❌ CRITICAL: Failed to create tool span", 
                                   trace_id=trace_id[:12],
                                   tool_name=span_name,
                                   error=str(span_error)[:400],
                                   error_type=type(span_error).__name__)
                        import traceback
                        logger.error(f"Span creation traceback: {traceback.format_exc()}")
                               
                elif span_type == 'agent':
                    # Main agent span - create a generation
                    generation = langfuse_trace.generation(
                        name=f"agent_{span_name}",
                        model="gpt-4.1-nano-2025-04-14",  # Default model
                        metadata={
                            "span_id": span_id,
                            "span_type": span_type,
                            "agent_name": span_name,
                            "start_time": datetime.now().isoformat()
                        }
                    )
                    
                    # Store generation for later update
                    if not hasattr(langfuse_trace, '_generations'):
                        langfuse_trace._generations = {}
                    langfuse_trace._generations[span_id] = generation
                    
                    # Note: Avoid immediate flush - let it batch
                    
                    logger.debug("Agent generation created and flushed", 
                                trace_id=trace_id[:12], 
                                span_id=span_id[:12],
                                agent_name=span_name)
                else:
                    # Skip other types (response, etc.) - they're internal
                    logger.debug("Skipping internal span", 
                               trace_id=trace_id[:12], 
                               span_id=span_id[:12],
                               span_type=span_type)
                               
            except Exception as export_error:
                logger.warning("Failed to export span data", 
                             trace_id=trace_id[:12],
                             span_id=span_id[:12],
                             error=str(export_error)[:100])
                        
        except Exception as e:
            logger.error("Span start processing failed", 
                        trace_id=getattr(span, 'trace_id', 'unknown'),
                        span_id=getattr(span, 'span_id', 'unknown'),
                        error=str(e)[:100])
    
    def on_span_end(self, span) -> None:
        """Called when a span ends - get input/output data for tool calls and agents"""
        try:
            trace_id = str(span.trace_id)
            span_id = str(span.span_id)
            
            # Get the Langfuse trace
            langfuse_trace = self._traces.get(trace_id)
            if not langfuse_trace:
                return
            
            # Get the final span data with input/output
            try:
                export_data = span.export()
                span_data = export_data.get('span_data', {})
                span_type = span_data.get('type', 'unknown')
                span_input = span_data.get('input', {})
                span_output = span_data.get('output', {})
                
                logger.debug("Span ending", 
                           trace_id=trace_id[:12],
                           span_id=span_id[:12],
                           span_type=span_type,
                           has_input=bool(span_input),
                           has_output=bool(span_output))
                
                # Handle tool call spans
                if hasattr(langfuse_trace, '_spans') and span_id in langfuse_trace._spans:
                    langfuse_span = langfuse_trace._spans[span_id]
                    
                    # Update with actual input/output data
                    update_data = {
                        "metadata": {
                            "end_time": datetime.now().isoformat(),
                            "span_type": span_type
                        }
                    }
                    
                    if span_input:
                        update_data["input"] = span_input
                    if span_output:
                        update_data["output"] = span_output
                    else:
                        update_data["output"] = {"result": "completed"}
                    
                    langfuse_span.update(**update_data)
                    langfuse_span.end()
                    
                    # Note: Avoid immediate flush - let it batch
                    
                    # Clean up
                    del langfuse_trace._spans[span_id]
                    
                    logger.info("🔧 Tool call span ended and flushed", 
                               trace_id=trace_id[:12], 
                               span_id=span_id[:12],
                               tool_name=span_data.get('name', 'unknown'))
                
                # Handle agent generation spans  
                elif hasattr(langfuse_trace, '_generations') and span_id in langfuse_trace._generations:
                    generation = langfuse_trace._generations[span_id]
                    
                    # Update generation with input/output
                    update_data = {
                        "metadata": {
                            "end_time": datetime.now().isoformat(),
                            "span_type": span_type
                        }
                    }
                    
                    if span_input:
                        update_data["input"] = span_input
                    if span_output:
                        update_data["output"] = span_output
                    
                    generation.update(**update_data)
                    generation.end()
                    
                    # Note: Avoid immediate flush - let it batch
                    
                    # Clean up
                    del langfuse_trace._generations[span_id]
                    
                    logger.debug("Agent generation ended and flushed", 
                                trace_id=trace_id[:12], 
                                span_id=span_id[:12])
                else:
                    # This is expected for skipped spans (response, etc.)
                    logger.debug("Span ended (no Langfuse span)", 
                               trace_id=trace_id[:12], 
                               span_id=span_id[:12],
                               span_type=span_type)
                               
            except Exception as export_error:
                logger.warning("Failed to export span end data", 
                             trace_id=trace_id[:12],
                             span_id=span_id[:12],
                             error=str(export_error)[:100])
                             
        except Exception as e:
            logger.error("Span end processing failed", 
                        trace_id=getattr(span, 'trace_id', 'unknown'),
                        span_id=getattr(span, 'span_id', 'unknown'),
                        error=str(e)[:100])
    
    def _get_fresh_langfuse_client(self):
        """Get a fresh Langfuse client to avoid threading issues"""
        try:
            return Langfuse(**self._langfuse_config)
        except Exception as e:
            logger.error(f"Failed to create fresh Langfuse client: {e}")
            return None

    def force_flush(self) -> None:
        """Force flush all pending traces"""
        if self.langfuse:
            try:
                self.langfuse.flush()
            except Exception as e:
                logger.warning(f"Main client flush failed, trying fresh client: {e}")
                # Try with fresh client
                fresh_client = self._get_fresh_langfuse_client()
                if fresh_client:
                    fresh_client.flush()
    
    def shutdown(self) -> None:
        """Shutdown the processor"""
        if self.langfuse:
            self.langfuse.flush()
            # Clean up traces
            self._traces.clear()

def setup_langfuse_tracing():
    """Set up Langfuse tracing for OpenAI Agents SDK"""
    try:
        processor = LangfuseTracingProcessor()
        add_trace_processor(processor)
        logger.info("Langfuse tracing configured for OpenAI Agents SDK")
        return True
    except Exception as e:
        logger.exception("Failed to set up Langfuse tracing")
        return False