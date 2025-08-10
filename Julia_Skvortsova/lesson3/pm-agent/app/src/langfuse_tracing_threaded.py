"""
Thread-based Langfuse TracingProcessor to avoid async conflicts
"""
import os
import structlog
from typing import Optional, Dict, Any, Mapping, Sequence
from agents import TracingProcessor, add_trace_processor, Span
from agents.tracing.span_data import GenerationSpanData, FunctionSpanData, AgentSpanData, ResponseSpanData
from langfuse import Langfuse
from datetime import datetime
import threading
import queue
import time
from dataclasses import dataclass
from enum import Enum

logger = structlog.get_logger()

def _text_from_messages(msgs: Sequence[Mapping[str, Any]] | None) -> str:
    """Flatten the OpenAI-style messages structure into text"""
    if not msgs:
        return ""
    chunks = []
    for m in msgs:
        for part in m.get("content", []):
            # input_text / text depending on the span
            t = part.get("text") or part.get("input_text") or part.get("output_text")
            if t:
                chunks.append(t)
    return "\n".join(chunks)

class OperationType(Enum):
    TRACE_START = "trace_start"
    TRACE_END = "trace_end"
    SPAN_START = "span_start" 
    SPAN_END = "span_end"
    RESPONSE_DATA = "response_data"  # New operation for ResponseSpanData
    FLUSH = "flush"
    SHUTDOWN = "shutdown"

@dataclass
class LangfuseOperation:
    operation_type: OperationType
    data: Dict[str, Any]
    timestamp: float

class ThreadedLangfuseTracingProcessor(TracingProcessor):
    """Thread-isolated TracingProcessor to avoid OpenAI SDK conflicts"""
    
    def __init__(self):
        """Initialize with dedicated worker thread"""
        super().__init__()
        
        # Thread-safe communication
        self.operation_queue = queue.Queue(maxsize=1000)
        self.shutdown_event = threading.Event()
        
        # Langfuse config for worker thread
        self._langfuse_config = {
            "public_key": os.getenv("LANGFUSE_PUBLIC_KEY"),
            "secret_key": os.getenv("LANGFUSE_SECRET_KEY"),
            "host": os.getenv("LANGFUSE_HOST", "http://localhost:3000"),
        }
        
        # Start dedicated worker thread
        self.worker_thread = threading.Thread(
            target=self._worker_thread,
            name="LangfuseWorker",
            daemon=True
        )
        self.worker_thread.start()
        
        logger.info("ThreadedLangfuseTracingProcessor initialized")
    
    def _worker_thread(self):
        """Dedicated thread for all Langfuse operations"""
        try:
            # Create Langfuse client in worker thread context
            langfuse = Langfuse(**self._langfuse_config)
            traces = {}  # Store active traces in worker thread
            
            logger.info("🧵 Langfuse worker thread started")
            
            while not self.shutdown_event.is_set():
                try:
                    # Wait for operations with timeout
                    operation = self.operation_queue.get(timeout=1.0)
                    
                    if operation.operation_type == OperationType.TRACE_START:
                        self._handle_trace_start(langfuse, traces, operation.data)
                    
                    elif operation.operation_type == OperationType.TRACE_END:
                        self._handle_trace_end(langfuse, traces, operation.data)
                    
                    elif operation.operation_type == OperationType.SPAN_START:
                        self._handle_span_start(langfuse, traces, operation.data)
                    
                    elif operation.operation_type == OperationType.SPAN_END:
                        self._handle_span_end(langfuse, traces, operation.data)
                    
                    elif operation.operation_type == OperationType.RESPONSE_DATA:
                        self._handle_response_data(langfuse, traces, operation.data)
                    
                    elif operation.operation_type == OperationType.FLUSH:
                        langfuse.flush()
                        logger.debug("🔄 Worker thread flushed")
                    
                    elif operation.operation_type == OperationType.SHUTDOWN:
                        break
                        
                    self.operation_queue.task_done()
                    
                except queue.Empty:
                    continue  # Timeout, check shutdown event
                except Exception as e:
                    logger.error(f"❌ Worker thread error: {e}")
                    try:
                        self.operation_queue.task_done()
                    except:
                        pass
            
            # Final cleanup
            langfuse.flush()
            logger.info("🧵 Langfuse worker thread shutdown")
            
        except Exception as e:
            logger.error(f"❌ Critical worker thread error: {e}")
    
    def _queue_operation(self, operation_type: OperationType, data: Dict[str, Any]):
        """Queue operation for worker thread"""
        try:
            operation = LangfuseOperation(
                operation_type=operation_type,
                data=data,
                timestamp=time.time()
            )
            self.operation_queue.put_nowait(operation)
        except queue.Full:
            logger.warning("⚠️ Langfuse operation queue full, dropping operation")
        except Exception as e:
            logger.error(f"❌ Failed to queue operation: {e}")
    
    def _handle_trace_start(self, langfuse, traces, data):
        """Handle trace start in worker thread"""
        try:
            trace_id = data['trace_id']
            
            langfuse_trace = langfuse.trace(
                name=f"agent_run_{trace_id[:8]}",
                metadata={
                    "trace_id": trace_id,
                    "start_time": datetime.now().isoformat(),
                }
            )
            
            traces[trace_id] = {
                'trace': langfuse_trace,
                'spans': {},
                'generations': {},
                'user_input': data.get('user_input'),
                'final_output': None,
                'conversation_inputs': [],  # Collect user inputs from ResponseSpanData
                'conversation_outputs': [],  # Collect agent responses from ResponseSpanData
                'trace_input_set': False  # Track if we've set the trace-level input
            }
            
            logger.info(f"🟢 Trace created in worker thread: {trace_id[:12]}")
            
        except Exception as e:
            logger.error(f"❌ Worker trace start failed: {e}")
    
    def _handle_span_start(self, langfuse, traces, data):
        """Handle span start in worker thread"""
        try:
            trace_id = data['trace_id']
            span_id = data['span_id']
            span_type = data['span_type']
            span_name = data['span_name']
            
            if trace_id not in traces:
                logger.warning(f"⚠️ Span start: trace {trace_id[:12]} not found")
                return
            
            trace_data = traces[trace_id]
            langfuse_trace = trace_data['trace']
            
            if span_type == 'function':
                # Function call span
                langfuse_span = langfuse_trace.span(
                    name=f"tool_{span_name}",
                    metadata={
                        "span_id": span_id,
                        "span_type": span_type,
                        "tool_name": span_name,
                        "start_time": datetime.now().isoformat()
                    }
                )
                trace_data['spans'][span_id] = langfuse_span
                
                logger.info(f"🔧 Function span created: {span_name}")
                
            elif span_type == 'generation':
                # Generation span - extract model from span_name
                model = span_name.replace('generation_', '') if 'generation_' in span_name else "gpt-4.1-nano-2025-04-14"
                generation = langfuse_trace.generation(
                    name=f"generation",
                    model=model,
                    metadata={
                        "span_id": span_id,
                        "span_type": span_type,
                        "start_time": datetime.now().isoformat()
                    }
                )
                trace_data['generations'][span_id] = generation
                
                logger.info(f"🤖 Generation span created: {model}")
                
            elif span_type == 'agent':
                # Agent span - create as generation
                generation = langfuse_trace.generation(
                    name=f"agent_{span_name}",
                    model="gpt-4.1-nano-2025-04-14",  # Default model for agent
                    metadata={
                        "span_id": span_id,
                        "span_type": span_type,
                        "agent_name": span_name,
                        "start_time": datetime.now().isoformat()
                    }
                )
                trace_data['generations'][span_id] = generation
                
                logger.info(f"👤 Agent generation created: {span_name}")
            
        except Exception as e:
            logger.error(f"❌ Worker span start failed: {e}")
    
    def _handle_span_end(self, langfuse, traces, data):
        """Handle span end in worker thread"""
        try:
            trace_id = data['trace_id']
            span_id = data['span_id']
            span_type = data.get('span_type')
            span_input = data.get('input')
            span_output = data.get('output')
            
            if trace_id not in traces:
                logger.warning(f"⚠️ Trace {trace_id[:12]} not found for span end")
                return
                
            trace_data = traces[trace_id]
            
            # Handle function call span end
            if span_type == 'function' and span_id in trace_data['spans']:
                langfuse_span = trace_data['spans'][span_id]
                
                update_data = {
                    "metadata": {
                        "end_time": datetime.now().isoformat(),
                        "span_type": span_type
                    }
                }
                
                if span_input:
                    update_data["input"] = span_input
                    logger.debug(f"📥 Function input: {str(span_input)[:100]}")
                    
                if span_output:
                    update_data["output"] = span_output
                    logger.debug(f"📤 Function output: {str(span_output)[:100]}")
                    
                langfuse_span.update(**update_data)
                langfuse_span.end()
                
                del trace_data['spans'][span_id]
                logger.info(f"🔧 Function span ended: {span_id[:12]}")
            
            # Handle generation span end  
            elif span_type == 'generation' and span_id in trace_data['generations']:
                generation = trace_data['generations'][span_id]
                
                update_data = {
                    "metadata": {
                        "end_time": datetime.now().isoformat(),
                        "span_type": span_type
                    }
                }
                
                if span_input:
                    update_data["input"] = span_input
                    logger.debug(f"📥 Generation input: {str(span_input)[:100]}")
                else:
                    logger.warning(f"⚠️ No generation input: {span_id[:12]}")
                    
                if span_output:
                    update_data["output"] = span_output
                    logger.debug(f"📤 Generation output: {str(span_output)[:100]}")
                else:
                    logger.warning(f"⚠️ No generation output: {span_id[:12]}")
                
                logger.info(f"🤖 Updating generation with real I/O data: {update_data}")
                    
                generation.update(**update_data)
                generation.end()
                
                del trace_data['generations'][span_id]
                logger.info(f"🤖 Generation span ended: {span_id[:12]}")
                
            # Handle agent span end (treated as generation)
            elif span_type == 'agent' and span_id in trace_data['generations']:
                generation = trace_data['generations'][span_id]
                
                update_data = {
                    "metadata": {
                        "end_time": datetime.now().isoformat(),
                        "span_type": span_type
                    }
                }
                
                # Use collected conversation data for agent I/O
                conversation_inputs = trace_data.get('conversation_inputs', [])
                conversation_outputs = trace_data.get('conversation_outputs', [])
                
                if conversation_inputs:
                    # Get unique user messages to avoid duplication
                    unique_user_messages = []
                    seen_content = set()
                    
                    for msg in conversation_inputs:
                        if msg.get('role') == 'user':
                            content = msg.get('content', '')
                            if content and content not in seen_content:
                                unique_user_messages.append(content)
                                seen_content.add(content)
                    
                    if unique_user_messages:
                        # Use the first unique user message for agent input
                        combined_input = unique_user_messages[0] if len(unique_user_messages) == 1 else "\n".join(unique_user_messages)
                        update_data["input"] = {"content": combined_input}  # Format as dict for Langfuse
                        logger.debug(f"📥 Agent input (deduplicated): {combined_input[:100]}")
                    else:
                        logger.warning(f"⚠️ No user messages in conversation inputs: {span_id[:12]}")
                else:
                    logger.warning(f"⚠️ No conversation inputs: {span_id[:12]}")
                    
                if conversation_outputs:
                    # Extract final agent response - handle different response types
                    final_response_obj = conversation_outputs[-1]
                    if final_response_obj:
                        # Try different ways to extract response content
                        final_response = None
                        
                        # If it's already a string, use it directly
                        if isinstance(final_response_obj, str):
                            final_response = final_response_obj
                        # Try common response object attributes
                        elif hasattr(final_response_obj, 'content'):
                            final_response = final_response_obj.content
                        elif hasattr(final_response_obj, 'text'):
                            final_response = final_response_obj.text
                        elif hasattr(final_response_obj, 'message') and hasattr(final_response_obj.message, 'content'):
                            final_response = final_response_obj.message.content
                        elif hasattr(final_response_obj, 'choices') and final_response_obj.choices:
                            choice = final_response_obj.choices[0]
                            if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                                final_response = choice.message.content
                        
                        # If still no content found, try to inspect the object structure
                        if not final_response:
                            # Log the object structure for debugging
                            obj_attrs = [attr for attr in dir(final_response_obj) if not attr.startswith('_')]
                            logger.debug(f"🔍 Response object attributes: {obj_attrs}")
                            
                            # Check if it's a config object that might have result data
                            if hasattr(final_response_obj, '__dict__'):
                                logger.debug(f"🔍 Response object dict: {final_response_obj.__dict__}")
                            
                            # Last resort - string representation, but filter out config objects
                            str_repr = str(final_response_obj)
                            if not ('Config' in str_repr or 'format=' in str_repr):
                                final_response = str_repr
                            else:
                                logger.warning(f"⚠️ Skipping config object response: {str_repr[:100]}")
                        
                        # Ensure final_response is a string and format properly
                        if final_response and str(final_response).strip():
                            update_data["output"] = {"content": str(final_response)[:500]}  # Format as dict
                            logger.debug(f"📤 Agent output (from conversation): {str(final_response)[:100]}")
                        else:
                            logger.warning(f"⚠️ No valid response content found: {span_id[:12]}")
                    else:
                        logger.warning(f"⚠️ Empty final response: {span_id[:12]}")
                else:
                    logger.warning(f"⚠️ No conversation outputs: {span_id[:12]}")
                
                logger.info(f"👤 Updating agent generation with conversation data: {len(conversation_inputs)} inputs, {len(conversation_outputs)} outputs")
                    
                generation.update(**update_data)
                generation.end()
                
                del trace_data['generations'][span_id]
                logger.info(f"👤 Agent generation ended: {span_id[:12]}")
            else:
                logger.debug(f"⏭️ Span end ignored: {span_type} {span_id[:12]}")
                
        except Exception as e:
            logger.error(f"❌ Worker span end failed: {e}")
    
    def _handle_response_data(self, langfuse, traces, data):
        """Handle ResponseSpanData to collect conversation input/output"""
        try:
            trace_id = data['trace_id']
            user_inputs = data.get('user_inputs', [])
            agent_responses = data.get('agent_responses', [])
            
            if trace_id not in traces:
                logger.warning(f"⚠️ Trace {trace_id[:12]} not found for response data")
                return
                
            trace_data = traces[trace_id]
            
            # Accumulate conversation data
            if user_inputs:
                trace_data['conversation_inputs'].extend(user_inputs)
                logger.debug(f"📥 Added user inputs: {len(user_inputs)} messages")
                
                # Set trace-level input from first user message (to fix null input)
                if not trace_data.get('trace_input_set', False):
                    first_user_msg = user_inputs[0]
                    if first_user_msg.get('role') == 'user':
                        user_content = first_user_msg.get('content', '')
                        if user_content:
                            langfuse_trace = trace_data['trace']
                            langfuse_trace.update(input={"content": user_content})
                            trace_data['trace_input_set'] = True
                            logger.debug(f"📥 Set trace input: {user_content[:100]}")
                
            if agent_responses:
                trace_data['conversation_outputs'].extend(agent_responses)
                logger.debug(f"📤 Added agent responses: {len(agent_responses)} responses")
                
            logger.debug(f"🗨️ Total conversation: {len(trace_data['conversation_inputs'])} inputs, {len(trace_data['conversation_outputs'])} outputs")
            
        except Exception as e:
            logger.error(f"❌ Worker response data failed: {e}")
    
    def _handle_trace_end(self, langfuse, traces, data):
        """Handle trace end in worker thread"""
        try:
            trace_id = data['trace_id']
            
            if trace_id not in traces:
                return
                
            trace_data = traces[trace_id]
            langfuse_trace = trace_data['trace']
            
            # Store final output for agent generations
            final_output = data.get('final_output')
            trace_data['final_output'] = final_output
            
            # Get the final agent response for trace output
            conversation_outputs = trace_data.get('conversation_outputs', [])
            trace_output = {"status": "completed"}
            
            if conversation_outputs:
                # Try to extract the final response content
                final_response_obj = conversation_outputs[-1]
                if isinstance(final_response_obj, str):
                    trace_output["response"] = final_response_obj
                elif final_response_obj:
                    # Try to extract string content from the response object
                    response_str = str(final_response_obj)
                    if not ('Config' in response_str or 'format=' in response_str):
                        trace_output["response"] = response_str[:200]  # Truncate for trace level
            
            langfuse_trace.update(
                output=trace_output,
                metadata={
                    "end_time": datetime.now().isoformat(),
                    "trace_id": trace_id
                }
            )
            
            del traces[trace_id]
            
            # Flush after trace completion
            langfuse.flush()
            
            logger.info(f"🟢 Trace completed in worker thread: {trace_id[:12]}")
            
        except Exception as e:
            logger.error(f"❌ Worker trace end failed: {e}")
    
    # TracingProcessor interface - these run in SDK context
    def on_trace_start(self, trace) -> None:
        """Called when a trace starts - queue for worker thread"""
        try:
            trace_id = str(trace.trace_id)
            
            # Try to extract user input if available
            user_input = None
            try:
                # Check if trace has input data
                if hasattr(trace, 'input'):
                    user_input = trace.input
                elif hasattr(trace, 'data'):
                    user_input = getattr(trace.data, 'input', None)
                    
                logger.debug(f"📥 Trace user input: {str(user_input)[:100] if user_input else 'None'}")
            except Exception as input_error:
                logger.debug(f"Could not extract trace input: {input_error}")
            
            self._queue_operation(OperationType.TRACE_START, {
                'trace_id': trace_id,
                'user_input': user_input
            })
            logger.info(f"🟢 Queued trace start: {trace_id[:12]}")
        except Exception as e:
            logger.error(f"❌ Failed to queue trace start: {e}")
    
    def on_trace_end(self, trace) -> None:
        """Called when a trace ends - queue for worker thread"""
        try:
            trace_id = str(trace.trace_id)
            
            # Try to extract final output if available
            final_output = None
            try:
                # Check if trace has output data
                if hasattr(trace, 'output'):
                    final_output = trace.output
                elif hasattr(trace, 'result'):
                    final_output = trace.result
                elif hasattr(trace, 'data'):
                    final_output = getattr(trace.data, 'output', None)
                    
                logger.debug(f"📤 Trace final output: {str(final_output)[:100] if final_output else 'None'}")
            except Exception as output_error:
                logger.debug(f"Could not extract trace output: {output_error}")
            
            self._queue_operation(OperationType.TRACE_END, {
                'trace_id': trace_id,
                'final_output': final_output
            })
            logger.info(f"🔴 Queued trace end: {trace_id[:12]}")
        except Exception as e:
            logger.error(f"❌ Failed to queue trace end: {e}")
    
    def on_span_start(self, span: Span[Any]) -> None:
        """Called when a span starts - queue for worker thread"""
        try:
            trace_id = str(span.trace_id)
            span_id = str(span.span_id)
            
            # Get span data using the correct approach
            try:
                data = span.span_data
                span_type = None
                span_name = None
                
                if isinstance(data, GenerationSpanData):
                    span_type = "generation"
                    span_name = f"generation_{data.model}"
                    logger.info(f"🤖 GENERATION SPAN START: {data.model}")
                    
                elif isinstance(data, FunctionSpanData):
                    span_type = "function"
                    span_name = data.name
                    logger.info(f"🔧 FUNCTION SPAN START: {data.name}")
                    
                elif isinstance(data, AgentSpanData):
                    span_type = "agent"
                    span_name = data.name
                    logger.info(f"👤 AGENT SPAN START: {data.name}")
                    logger.debug(f"   Agent data attributes: {[attr for attr in dir(data) if not attr.startswith('_')]}")
                    
                elif isinstance(data, ResponseSpanData):
                    # ResponseSpanData contains conversation data - queue for processing
                    logger.debug(f"🗨️ RESPONSE SPAN START - queuing data collection")
                    return  # Will be processed in on_span_end
                    
                else:
                    logger.debug(f"⏭️ Skipped span type: {type(data)}")
                    return
                
                self._queue_operation(OperationType.SPAN_START, {
                    'trace_id': trace_id,
                    'span_id': span_id,
                    'span_type': span_type,
                    'span_name': span_name
                })
                logger.debug(f"🟡 Queued span start: {span_type} {span_name}")
                    
            except Exception as data_error:
                logger.warning(f"⚠️ Span data access failed: {data_error}")
                
        except Exception as e:
            logger.error(f"❌ Failed to queue span start: {e}")
    
    def on_span_end(self, span: Span[Any]) -> None:
        """Called when a span ends - queue for worker thread"""
        try:
            trace_id = str(span.trace_id)
            span_id = str(span.span_id)
            
            # Get span data using the correct approach
            try:
                data = span.span_data
                span_input = None
                span_output = None
                span_type = None
                
                if isinstance(data, GenerationSpanData):
                    span_type = "generation"
                    span_input = _text_from_messages(data.input)
                    span_output = _text_from_messages(data.output)
                    
                    logger.info(f"🤖 GENERATION SPAN END:")
                    logger.info(f"  Model: {data.model}")
                    logger.debug(f"  Input: {span_input[:100] if span_input else 'None'}")
                    logger.debug(f"  Output: {span_output[:100] if span_output else 'None'}")
                    
                elif isinstance(data, FunctionSpanData):
                    span_type = "function" 
                    span_input = data.input
                    span_output = data.output
                    
                    logger.info(f"🔧 FUNCTION SPAN END:")
                    logger.info(f"  Name: {data.name}")
                    logger.debug(f"  Args: {span_input}")
                    logger.debug(f"  Result: {span_output}")
                    
                elif isinstance(data, AgentSpanData):
                    span_type = "agent"
                    # For agent spans, we might need to extract input/output differently
                    span_input = getattr(data, 'input', None)
                    span_output = getattr(data, 'output', None)
                    
                    logger.info(f"👤 AGENT SPAN END:")
                    logger.info(f"  Name: {data.name}")
                    logger.debug(f"  Input: {span_input}")
                    logger.debug(f"  Output: {span_output}")
                    logger.debug(f"  Agent data attributes: {[attr for attr in dir(data) if not attr.startswith('_')]}")
                    
                elif isinstance(data, ResponseSpanData):
                    # Extract conversation data from ResponseSpanData
                    logger.debug(f"🗨️ RESPONSE SPAN END - extracting conversation data")
                    logger.debug(f"🔍 ResponseSpanData attributes: {[attr for attr in dir(data) if not attr.startswith('_')]}")
                    
                    user_inputs = []
                    agent_responses = []
                    
                    # Extract user input messages
                    if hasattr(data, 'input') and data.input:
                        user_inputs = [msg for msg in data.input if isinstance(msg, dict) and msg.get('role') == 'user']
                        logger.debug(f"📥 Found {len(user_inputs)} user messages")
                    
                    # Look for actual response content in different locations
                    agent_response_content = None
                    
                    # Check if response has the actual content  
                    if hasattr(data, 'response') and data.response:
                        logger.debug(f"🔍 ResponseSpanData.response type: {type(data.response)}")
                        logger.debug(f"🔍 ResponseSpanData.response: {str(data.response)[:200]}")
                        
                        # Check if it's an OpenAI Response object - explore its structure
                        response_attrs = [attr for attr in dir(data.response) if not attr.startswith('_')]
                        logger.debug(f"🔍 Response object attributes: {response_attrs}")
                        
                        # Try different approaches to extract content
                        if hasattr(data.response, 'messages') and data.response.messages:
                            logger.debug(f"🔍 Found messages: {len(data.response.messages)}")
                            # Extract from messages
                            for i, message in enumerate(data.response.messages):
                                logger.debug(f"🔍 Message {i}: {type(message)} - {str(message)[:100]}")
                                if hasattr(message, 'content'):
                                    if isinstance(message.content, list):
                                        for content_part in message.content:
                                            if hasattr(content_part, 'text'):
                                                agent_response_content = content_part.text
                                                logger.debug(f"📤 Found response text: {agent_response_content[:100]}")
                                                break
                                    elif isinstance(message.content, str):
                                        agent_response_content = message.content
                                        logger.debug(f"📤 Found response text: {agent_response_content[:100]}")
                                        break
                                if agent_response_content:
                                    break
                        
                        # Try extracting from output field (list of messages)
                        if not agent_response_content and hasattr(data.response, 'output') and data.response.output:
                            logger.debug(f"🔍 Response.output: {type(data.response.output)} with {len(data.response.output)} items")
                            
                            # Look for the final response message (usually the last one)
                            for i, output_item in enumerate(data.response.output):
                                logger.debug(f"🔍 Output item {i}: {type(output_item)} - {str(output_item)[:100]}")
                                
                                # Check if it's a ResponseOutputMessage with content
                                if hasattr(output_item, 'content') and output_item.content:
                                    if isinstance(output_item.content, list):
                                        # Extract text from content parts
                                        for content_part in output_item.content:
                                            logger.debug(f"🔍 Content part: {type(content_part)} - {str(content_part)[:100]}")
                                            if hasattr(content_part, 'text'):
                                                agent_response_content = content_part.text
                                                logger.debug(f"📤 Found response text from output: {agent_response_content[:100]}")
                                                break
                                    elif isinstance(output_item.content, str):
                                        agent_response_content = output_item.content
                                        logger.debug(f"📤 Found response content from output: {agent_response_content[:100]}")
                                        break
                                
                                if agent_response_content:
                                    break
                        
                        # Try other common response fields as fallback
                        if not agent_response_content:
                            for field in ['content', 'text', 'result', 'final_output']:
                                if hasattr(data.response, field):
                                    field_value = getattr(data.response, field)
                                    logger.debug(f"🔍 Response.{field}: {type(field_value)} - {str(field_value)[:100]}")
                                    if isinstance(field_value, str) and field_value.strip():
                                        agent_response_content = field_value
                                        logger.debug(f"📤 Found content in {field}: {agent_response_content[:100]}")
                                        break
                    
                    # Check for output field
                    if hasattr(data, 'output') and data.output:
                        logger.debug(f"🔍 ResponseSpanData.output type: {type(data.output)}")
                        logger.debug(f"🔍 ResponseSpanData.output: {str(data.output)[:200]}")
                        # Try to extract from output
                        if isinstance(data.output, str):
                            agent_response_content = data.output
                        elif hasattr(data.output, 'content'):
                            agent_response_content = data.output.content
                        elif hasattr(data.output, 'text'):
                            agent_response_content = data.output.text
                    
                    # Check for result field
                    if not agent_response_content and hasattr(data, 'result') and data.result:
                        logger.debug(f"🔍 ResponseSpanData.result type: {type(data.result)}")
                        logger.debug(f"🔍 ResponseSpanData.result: {str(data.result)[:200]}")
                        if isinstance(data.result, str):
                            agent_response_content = data.result
                    
                    # If we found actual content, use it; otherwise fall back to response object
                    if agent_response_content:
                        agent_responses = [agent_response_content]
                        logger.debug(f"📤 Found actual agent content: {str(agent_response_content)[:100]}")
                    elif hasattr(data, 'response') and data.response:
                        # Store the config object and let handler deal with it
                        agent_responses = [data.response]
                        logger.debug(f"📤 Found agent response config: {str(data.response)[:100]}")
                    
                    # Queue the conversation data for the worker thread
                    if user_inputs or agent_responses:
                        self._queue_operation(OperationType.RESPONSE_DATA, {
                            'trace_id': trace_id,
                            'user_inputs': user_inputs,
                            'agent_responses': agent_responses
                        })
                        logger.debug(f"🗨️ Queued conversation data: {len(user_inputs)} inputs, {len(agent_responses)} responses")
                    
                    return  # Don't process as regular span
                    
                else:
                    logger.debug(f"⏭️ Skipping span type: {type(data)}")
                    return
                
                self._queue_operation(OperationType.SPAN_END, {
                    'trace_id': trace_id,
                    'span_id': span_id,
                    'span_type': span_type,
                    'input': span_input,
                    'output': span_output
                })
                logger.debug(f"🔴 Queued span end: {span_id[:12]} ({span_type})")
                
            except Exception as data_error:
                logger.warning(f"⚠️ Span data extraction failed: {data_error}")
                
        except Exception as e:
            logger.error(f"❌ Failed to queue span end: {e}")
    
    def force_flush(self) -> None:
        """Force flush all pending traces"""
        self._queue_operation(OperationType.FLUSH, {})
    
    def shutdown(self) -> None:
        """Shutdown the processor and worker thread"""
        try:
            # Signal shutdown
            self._queue_operation(OperationType.SHUTDOWN, {})
            self.shutdown_event.set()
            
            # Wait for worker thread to finish
            if self.worker_thread.is_alive():
                self.worker_thread.join(timeout=5.0)
                
            logger.info("🛑 ThreadedLangfuseTracingProcessor shutdown")
        except Exception as e:
            logger.error(f"❌ Shutdown error: {e}")

def setup_threaded_langfuse_tracing():
    """Set up threaded Langfuse tracing for OpenAI Agents SDK"""
    try:
        processor = ThreadedLangfuseTracingProcessor()
        add_trace_processor(processor)
        logger.info("Threaded Langfuse tracing configured for OpenAI Agents SDK")
        return True
    except Exception as e:
        logger.exception("Failed to set up threaded Langfuse tracing")
        return False