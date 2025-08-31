"""
Claude Code SDK - Concurrent Agents and Multi-turn Conversations Demo.

Focuses on two key patterns:
1. Concurrent agents (multiple agents working in parallel)
2. Multi-turn conversations (maintaining context across multiple turns)
"""

from dotenv import load_dotenv
load_dotenv()

import asyncio
from typing import Dict, Any, AsyncGenerator, Optional
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions, CLINotFoundError, ProcessError


# Query function with session management (Method 2 from example)
async def query(
    prompt: str, 
    options: Optional[ClaudeCodeOptions] = None
) -> AsyncGenerator[Any, None]:
    """
    Query function with session management support.
    
    Supports:
    - continue_conversation=True to continue most recent conversation
    - resume="session_id" to resume a specific session
    - max_turns to limit conversation turns
    """
    if options is None:
        options = ClaudeCodeOptions()
    
    async with ClaudeSDKClient(options=options) as client:
        await client.query(prompt)
        
        async for message in client.receive_response():
            yield message


# Helper function to collect response with metadata (no streaming)
async def get_response_with_metadata(client: ClaudeSDKClient, prompt: str) -> Dict[str, Any]:
    """Collect full response with metadata (no streaming output)"""
    await client.query(prompt)
    text = []
    metadata = {}
    
    async for msg in client.receive_response():
        if hasattr(msg, 'content'):
            for block in msg.content:
                if hasattr(block, 'text'):
                    text.append(block.text)
        
        if type(msg).__name__ == "ResultMessage":
            metadata = {
                'text': ''.join(text),
                'cost': msg.total_cost_usd,
                'duration_ms': msg.duration_ms,
                'session_id': msg.session_id
            }
            break
    
    return metadata


# Helper function with streaming output
async def stream_response(client: ClaudeSDKClient, prompt: str) -> Dict[str, Any]:
    """Stream response text as it arrives and return metadata"""
    await client.query(prompt)
    text_parts = []
    metadata = {}
    
    # Stream responses
    async for message in client.receive_response():
        if hasattr(message, 'content'):
            for block in message.content:
                if hasattr(block, 'text'):
                    # Print text as it arrives (streaming)
                    print(block.text, end='', flush=True)
                    text_parts.append(block.text)
        
        if type(message).__name__ == "ResultMessage":
            metadata = {
                'text': ''.join(text_parts),
                'cost': message.total_cost_usd,
                'duration_ms': message.duration_ms,
                'session_id': message.session_id
            }
            break
    
    return metadata


async def demo_concurrent_agents():
    """PATTERN 1: Run multiple specialized agents concurrently"""
    
    print("\n🚀 PATTERN 1: Concurrent Agents")
    print("=" * 60)
    print("Running 3 specialized agents in parallel for comprehensive analysis")
    print("-" * 60)
    
    product_idea = "AI-Powered Sprint Planning Assistant"
    
    try:
        # Create 3 specialized agents for different aspects of PRD analysis
        async with ClaudeSDKClient(
            options=ClaudeCodeOptions(
                system_prompt="You are a market research expert. Analyze competitive landscape and market opportunities. Be concise.",
                max_turns=1
            )
        ) as market_agent, ClaudeSDKClient(
            options=ClaudeCodeOptions(
                system_prompt="You are a technical architect. Define technical requirements and system design. Be concise.",
                max_turns=1
            )
        ) as tech_agent, ClaudeSDKClient(
            options=ClaudeCodeOptions(
                system_prompt="You are a UX designer. Define user experience and interface requirements. Be concise.",
                max_turns=1
            )
        ) as ux_agent:
            
            print(f"\n📦 Analyzing: {product_idea}")
            print("\n⚡ Launching agents:")
            print("  • Market Research Agent")
            print("  • Technical Architecture Agent")
            print("  • UX Design Agent")
            
            # Prepare prompts for each agent
            market_prompt = f"Analyze the market opportunity for: {product_idea}. Give 3 key insights in bullet points."
            tech_prompt = f"Define technical architecture for: {product_idea}. List 3 key technical requirements."
            ux_prompt = f"Design user experience for: {product_idea}. Describe 3 essential UI components."
            
            # Run all agents concurrently using asyncio.gather
            print("\n⏳ Agents working in parallel (collecting responses)...")
            results = await asyncio.gather(
                get_response_with_metadata(market_agent, market_prompt),
                get_response_with_metadata(tech_agent, tech_prompt),
                get_response_with_metadata(ux_agent, ux_prompt),
                return_exceptions=True  # Don't fail if one agent fails
            )
            
            # Process results
            print("\n📊 Results:")
            for result, agent_name in zip(results, ['Market Research', 'Technical Architecture', 'UX Design']):
                if isinstance(result, Exception):
                    print(f"  ❌ {agent_name}: Failed - {result}")
                else:
                    print(f"  ✅ {agent_name}: Completed")
                    print(f"     • Cost: ${result['cost']:.4f}")
                    print(f"     • Duration: {result['duration_ms']}ms")
                    print(f"     • Response preview: {result['text'][:100]}...")
            
            # Calculate totals
            total_cost = sum(r['cost'] for r in results if isinstance(r, dict))
            total_duration = max(r['duration_ms'] for r in results if isinstance(r, dict))
            print(f"\n💰 Total Cost: ${total_cost:.4f}")
            print(f"⏱️  Total Duration: {total_duration}ms (parallel execution)")
    
    except CLINotFoundError:
        print("❌ Claude Code CLI not found! Install with: npm install -g @anthropic-ai/claude-code")
    except ProcessError as e:
        print(f"❌ Process error: {e}")
    except Exception as e:
        print(f"❌ Error in concurrent execution: {e}")


async def demo_query_function_sessions():
    """PATTERN 2A: Using query function with session management"""
    
    print("\n\n🔄 PATTERN 2A: Query Function with Session Management")
    print("=" * 60)
    print("Using the query() function for session continuation and resumption")
    print("-" * 60)
    
    session_id = None
    
    try:
        # Start initial conversation using query function
        print("\n📝 Starting initial conversation with query()...")
        async for message in query(
            prompt="Let's create a PRD for a task management app. Start with a brief product vision.",
            options=ClaudeCodeOptions(
                system_prompt="You are a Senior Product Manager. Be concise.",
                max_turns=2
            )
        ):
            if hasattr(message, 'content'):
                for block in message.content:
                    if hasattr(block, 'text'):
                        print(block.text, end='', flush=True)
            
            if type(message).__name__ == "ResultMessage":
                session_id = message.session_id
                print(f"\n\n✓ Initial conversation complete")
                print(f"  Session ID: {session_id[:8]}...")
        
        # Method 1: Continue the most recent conversation
        print("\n\n📝 Method 1: Continuing most recent conversation with query()...")
        async for message in query(
            prompt="Now refactor this for better performance and add 3 key user personas.",
            options=ClaudeCodeOptions(continue_conversation=True)
        ):
            if hasattr(message, 'content'):
                for block in message.content:
                    if hasattr(block, 'text'):
                        print(block.text, end='', flush=True)
            
            if type(message).__name__ == "ResultMessage":
                print("\n✓ Continued conversation successfully")
        
        # Method 2: Resume a specific session by ID
        if session_id:
            print(f"\n\n📝 Method 2: Resuming specific session {session_id[:8]} with query()...")
            async for message in query(
                prompt="Update the tests and define 3 success metrics for this product.",
                options=ClaudeCodeOptions(
                    resume=session_id,
                    max_turns=3
                )
            ):
                if hasattr(message, 'content'):
                    for block in message.content:
                        if hasattr(block, 'text'):
                            print(block.text, end='', flush=True)
                
                if type(message).__name__ == "ResultMessage":
                    print("\n✓ Resumed specific session successfully")
    
    except Exception as e:
        print(f"❌ Error in query function session management: {e}")


async def demo_session_resume():
    """PATTERN 2B: Resume and continue sessions using ClaudeSDKClient directly"""
    
    print("\n\n🔄 PATTERN 2B: Direct Session Management with ClaudeSDKClient")
    print("=" * 60)
    print("Demonstrating session continuation using ClaudeSDKClient")
    print("-" * 60)
    
    session_id = None
    
    try:
        # Start initial conversation
        print("\n📝 Starting initial conversation...")
        async with ClaudeSDKClient(
            options=ClaudeCodeOptions(
                system_prompt="You are a Senior Product Manager. Be concise.",
                max_turns=2
            )
        ) as client:
            await client.query("Let's create a PRD for a sprint planning assistant. Start with a brief product vision.")
            
            async for message in client.receive_response():
                if hasattr(message, 'content'):
                    for block in message.content:
                        if hasattr(block, 'text'):
                            print(block.text, end='', flush=True)
                
                if type(message).__name__ == "ResultMessage":
                    session_id = message.session_id
                    print(f"\n\n✓ Initial conversation complete")
                    print(f"  Session ID: {session_id[:8]}...")
        
        # Continue the most recent conversation
        print("\n\n📝 Continuing most recent conversation...")
        async with ClaudeSDKClient(
            options=ClaudeCodeOptions(
                continue_conversation=True,
                max_turns=2
            )
        ) as client:
            await client.query("Now add 3 key user personas based on that vision.")
            
            async for message in client.receive_response():
                if hasattr(message, 'content'):
                    for block in message.content:
                        if hasattr(block, 'text'):
                            print(block.text, end='', flush=True)
            
            print("\n✓ Continued conversation successfully")
        
        # Resume a specific session by ID
        if session_id:
            print(f"\n\n📝 Resuming specific session {session_id[:8]}...")
            async with ClaudeSDKClient(
                options=ClaudeCodeOptions(
                    resume=session_id,
                    max_turns=3
                )
            ) as client:
                await client.query("Finally, define 3 success metrics for this product.")
                
                async for message in client.receive_response():
                    if hasattr(message, 'content'):
                        for block in message.content:
                            if hasattr(block, 'text'):
                                print(block.text, end='', flush=True)
                
                print("\n✓ Resumed specific session successfully")
    
    except Exception as e:
        print(f"❌ Error in session management: {e}")


async def demo_multi_turn_conversation():
    """PATTERN 2B: Multi-turn conversation with persistent context and streaming"""
    
    print("\n\n🔄 PATTERN 2B: Multi-turn Conversations with Streaming")
    print("=" * 60)
    print("Building a PRD iteratively through 6 turns with maintained context")
    print("Watch the responses stream in real-time!")
    print("-" * 60)
    
    try:
        async with ClaudeSDKClient(
            options=ClaudeCodeOptions(
                system_prompt="You are a Senior Product Manager helping create a comprehensive PRD. Be concise.",
                max_turns=6
            )
        ) as client:
            
            print("\n📝 Starting iterative PRD generation with streaming...\n")
            
            # Turn 1: Define the product (with streaming)
            print("\n" + "─" * 40)
            print("Turn 1: Defining product vision")
            print("─" * 40)
            await client.query("Let's create a PRD for an AI-powered sprint planning assistant. Give me a brief product vision (2-3 sentences).")
            
            # Stream the response
            async for message in client.receive_response():
                if hasattr(message, 'content'):
                    for block in message.content:
                        if hasattr(block, 'text'):
                            print(block.text, end='', flush=True)
            print("\n✓ Vision defined")
            
            # Turn 2: User personas (with streaming)
            print("\n" + "─" * 40)
            print("Turn 2: Defining user personas")
            print("─" * 40)
            await client.query("Now define 3 user personas. Keep each to 2-3 bullet points.")
            
            async for message in client.receive_response():
                if hasattr(message, 'content'):
                    for block in message.content:
                        if hasattr(block, 'text'):
                            print(block.text, end='', flush=True)
            print("\n✓ Personas created")
            
            # Turn 3: Core requirements (abbreviated streaming)
            print("\n" + "─" * 40)
            print("Turn 3: Core requirements")
            print("─" * 40)
            await client.query("List the top 3 core requirements as brief user stories.")
            
            # Stream but collect for summary
            requirement_text = []
            async for message in client.receive_response():
                if hasattr(message, 'content'):
                    for block in message.content:
                        if hasattr(block, 'text'):
                            print(block.text, end='', flush=True)
                            requirement_text.append(block.text)
            print("\n✓ Requirements defined")
            
            # Turn 4: Technical specs (dots for brevity)
            print("\n" + "─" * 40)
            print("Turn 4: Technical architecture (processing...)")
            print("─" * 40)
            await client.query("Briefly describe the tech stack in 3-4 bullet points.")
            
            # Show dots for this one to demonstrate different streaming styles
            async for message in client.receive_response():
                if hasattr(message, 'content'):
                    for block in message.content:
                        if hasattr(block, 'text'):
                            print(".", end='', flush=True)
            print(" ✓ Architecture defined")
            
            # Turn 5: Success metrics (partial streaming)
            print("\n" + "─" * 40)
            print("Turn 5: Success metrics")
            print("─" * 40)
            await client.query("Define 3 key success metrics with specific targets.")
            
            char_count = 0
            async for message in client.receive_response():
                if hasattr(message, 'content'):
                    for block in message.content:
                        if hasattr(block, 'text'):
                            # Show first 100 chars then dots
                            if char_count < 100:
                                print(block.text[:100-char_count], end='', flush=True)
                                char_count += len(block.text)
                            else:
                                print(".", end='', flush=True)
            print("\n✓ Metrics set")
            
            # Turn 6: Timeline (collect metadata)
            print("\n" + "─" * 40)
            print("Turn 6: Implementation timeline")
            print("─" * 40)
            await client.query("Create a simple 3-phase timeline.")
            
            total_cost = 0
            session_id = ""
            turns = 0
            
            async for message in client.receive_response():
                if hasattr(message, 'content'):
                    for block in message.content:
                        if hasattr(block, 'text'):
                            print(block.text, end='', flush=True)
                
                if type(message).__name__ == "ResultMessage":
                    total_cost = message.total_cost_usd
                    session_id = message.session_id
                    turns = message.num_turns
            print("\n✓ Timeline created")
            
            print(f"\n\n✅ Multi-turn PRD generation completed!")
            print(f"   • Total turns: {turns}")
            print(f"   • Total cost: ${total_cost:.4f}")
            print(f"   • Session ID: {session_id[:8] if session_id else 'N/A'}...")
            print(f"   • Context maintained throughout entire conversation")
    
    except CLINotFoundError:
        print("❌ Claude Code CLI not found! Install with: npm install -g @anthropic-ai/claude-code")
    except ProcessError as e:
        print(f"❌ Process error: {e}")
    except Exception as e:
        print(f"❌ Error in multi-turn conversation: {e}")


async def demo_streaming():
    """Quick demonstration of streaming responses"""
    
    print("\n📺 STREAMING DEMO")
    print("=" * 60)
    print("Watch the response stream in real-time:")
    print("-" * 60)
    
    try:
        async with ClaudeSDKClient(
            options=ClaudeCodeOptions(
                system_prompt="You are a helpful assistant. Be concise.",
                max_turns=1
            )
        ) as client:
            
            await client.query("Explain the benefits of agile development in 2-3 sentences.")
            
            # Stream responses - text appears as it arrives
            async for message in client.receive_response():
                if hasattr(message, 'content'):
                    for block in message.content:
                        if hasattr(block, 'text'):
                            print(block.text, end='', flush=True)
            
            print("\n\n✅ Streaming complete!")
    
    except Exception as e:
        print(f"❌ Error in streaming demo: {e}")


async def main():
    """Main demonstration of streaming, concurrent agents, and multi-turn conversations"""
    
    print("🚀 Claude Code SDK - Key Patterns Demo")
    print("=" * 60)
    print("\nDemonstrating powerful patterns:")
    print("1. Streaming - Real-time response streaming")
    print("2. Concurrent Agents - Multiple specialized agents working in parallel")
    print("3. Session Management - Continue and resume conversations")
    print("4. Multi-turn Conversations - Maintaining context across multiple turns")
    print("=" * 60)
    
    # Quick streaming demo
    await demo_streaming()
    
    # Pattern 1: Concurrent agents
    await demo_concurrent_agents()
    
    # Pattern 2A: Query function with session management
    await demo_query_function_sessions()
    
    # Pattern 2B: Direct session management 
    await demo_session_resume()
    
    # Pattern 3: Multi-turn conversations
    await demo_multi_turn_conversation()
    
    print("\n" + "=" * 60)
    print("✨ All demos completed successfully!")
    print("=" * 60)
    print("\n📚 Key Implementation Patterns:")
    print("• Streaming: Use async for with message.content blocks")
    print("• Concurrent: Use asyncio.gather() for parallel agent execution")
    print("• Session Management: Use continue_conversation=True or resume='session_id'")
    print("• Query Function: Simplified API with query() for session management")
    print("• Multi-turn: Context automatically maintained across client.query() calls")
    print("• Error handling: Use return_exceptions=True for resilient execution")


if __name__ == "__main__":
    # Check CLI installation
    import subprocess
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("✅ Claude Code CLI is installed")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("⚠️ Claude Code CLI not found!")
        print("Install with: npm install -g @anthropic-ai/claude-code")
        print()
    
    # Run the main demo
    asyncio.run(main())