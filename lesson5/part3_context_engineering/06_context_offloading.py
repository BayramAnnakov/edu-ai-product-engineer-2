"""
Context Offloading for Product Management using LangGraph.

Implements context offloading with state management:
- Scratchpad in StateGraph for session memory
- InMemoryStore for cross-thread persistence
- Read/Write scratchpad tools
- Checkpointing for thread-based state
- Research workflow with memory

Based on: https://github.com/langchain-ai/how_to_fix_your_context/notebooks/06-context-offloading.ipynb
"""

import os
from typing import List, Dict, Any, Literal, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, ToolMessage, HumanMessage
from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.store.memory import InMemoryStore
from langgraph.checkpoint.memory import InMemorySaver

from dotenv import load_dotenv
load_dotenv()


class ScratchpadState(MessagesState):
    """State that extends MessagesState to include a scratchpad field"""
    scratchpad: str = Field(default="", description="The scratchpad for storing notes")


# Scratchpad management tools
@tool
class WriteToScratchpad(BaseModel):
    """Save notes to the scratchpad for future reference within the conversation."""
    notes: str = Field(description="Notes to save to the scratchpad")


@tool  
class ReadFromScratchpad(BaseModel):
    """Read previously saved notes from the scratchpad."""
    reasoning: str = Field(description="Reasoning for fetching notes from the scratchpad")


class PMOffloadingAgent:
    """
    Product Management agent with context offloading capabilities.
    """
    
    def __init__(self, use_persistent_memory: bool = False):
        """
        Initialize agent with offloading capabilities.
        
        Args:
            use_persistent_memory: If True, uses InMemoryStore for cross-thread persistence
        """
        
        # Initialize LLM
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        
        # Initialize search tool
        self.search_tool = TavilySearchResults(
            max_results=3,
            topic="general",
            name="tavily_search",
            description="Search the web for current information"
        )
        
        # Set up tools
        self.tools = [ReadFromScratchpad, WriteToScratchpad, self.search_tool]
        self.tools_by_name = {tool.name: tool for tool in self.tools}
        
        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # System prompt with scratchpad instructions
        self.scratchpad_prompt = """You are a Product Management research assistant with access to web search and a persistent scratchpad.

Your Research Workflow:
1. **Check Scratchpad**: Before starting a new research task, check your scratchpad for relevant information
2. **Create Research Plan**: Write a structured research plan to your scratchpad
3. **Conduct Research**: Use web search to gather information
4. **Update Scratchpad**: After each search, update your scratchpad with findings
5. **Iterate**: Continue researching and updating until comprehensive
6. **Synthesize**: Provide a thorough response based on accumulated research

Tools Available:
- WriteToScratchpad: Save research plans, findings, and progress
- ReadFromScratchpad: Retrieve previous research work
- tavily_search: Search the web for current information

Always maintain organized notes in your scratchpad and build upon previous research systematically."""
        
        # Setup memory stores if using persistent memory
        self.use_persistent_memory = use_persistent_memory
        if use_persistent_memory:
            self.memory_store = InMemoryStore()
            self.checkpointer = InMemorySaver()
            self.namespace = ("pm_research", "scratchpad")
        
        # Build workflow
        self.agent = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow with scratchpad"""
        
        def llm_call(state: ScratchpadState) -> dict:
            """Execute LLM call with system prompt and conversation history"""
            response = self.llm_with_tools.invoke(
                [SystemMessage(content=self.scratchpad_prompt)] + state["messages"]
            )
            return {"messages": [response]}
        
        def tool_node(state: ScratchpadState) -> dict:
            """Execute tool calls and manage scratchpad state"""
            
            results = []
            scratchpad_update = None
            
            for tool_call in state["messages"][-1].tool_calls:
                tool = self.tools_by_name[tool_call["name"]]
                
                if tool_call["name"] == "WriteToScratchpad":
                    # Save notes to scratchpad
                    observation = tool.invoke(tool_call["args"])
                    notes = observation.notes
                    
                    # Update state scratchpad
                    current_scratchpad = state.get("scratchpad", "")
                    new_scratchpad = f"{current_scratchpad}\n\n---\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{notes}" if current_scratchpad else notes
                    scratchpad_update = new_scratchpad
                    
                    # If using persistent memory, also save there
                    if self.use_persistent_memory:
                        self.memory_store.put(
                            self.namespace,
                            "scratchpad",
                            {"scratchpad": new_scratchpad, "timestamp": datetime.now().isoformat()}
                        )
                    
                    results.append(ToolMessage(
                        content=f"Wrote to scratchpad: {notes}",
                        tool_call_id=tool_call["id"]
                    ))
                    
                elif tool_call["name"] == "ReadFromScratchpad":
                    # Retrieve notes from scratchpad
                    if self.use_persistent_memory:
                        # Try to get from persistent store first
                        stored_data = self.memory_store.get(self.namespace, "scratchpad")
                        notes = stored_data.value["scratchpad"] if stored_data else state.get("scratchpad", "")
                    else:
                        notes = state.get("scratchpad", "")
                    
                    if not notes:
                        notes = "Scratchpad is empty"
                    
                    results.append(ToolMessage(
                        content=f"Notes from scratchpad:\n{notes}",
                        tool_call_id=tool_call["id"]
                    ))
                    
                elif tool_call["name"] == "tavily_search":
                    # Execute web search
                    observation = tool.invoke(tool_call["args"])
                    results.append(ToolMessage(
                        content=observation,
                        tool_call_id=tool_call["id"]
                    ))
            
            # Build update dict
            update = {"messages": results}
            if scratchpad_update is not None:
                update["scratchpad"] = scratchpad_update
            
            return update
        
        def should_continue(state: ScratchpadState) -> Literal["tool_node", "__end__"]:
            """Determine workflow continuation based on tool calls"""
            last_message = state["messages"][-1]
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                return "tool_node"
            return END
        
        # Build workflow
        workflow = StateGraph(ScratchpadState)
        
        # Add nodes
        workflow.add_node("llm_call", llm_call)
        workflow.add_node("tool_node", tool_node)
        
        # Add edges
        workflow.add_edge(START, "llm_call")
        workflow.add_conditional_edges(
            "llm_call",
            should_continue,
            {"tool_node": "tool_node", END: END}
        )
        workflow.add_edge("tool_node", "llm_call")
        
        # Compile with optional checkpointer and store
        if self.use_persistent_memory:
            return workflow.compile(
                checkpointer=self.checkpointer,
                store=self.memory_store
            )
        else:
            return workflow.compile()
    
    def query(self, question: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Query the agent with optional thread persistence.
        
        Args:
            question: User's question
            thread_id: Optional thread ID for checkpointing
            
        Returns:
            Response with answer and scratchpad contents
        """
        
        # Build config with thread ID if provided
        config = {}
        if thread_id and self.use_persistent_memory:
            config = {"configurable": {"thread_id": thread_id}}
        
        # Invoke agent
        result = self.agent.invoke(
            {"messages": [HumanMessage(content=question)]},
            config
        )
        
        # Extract final answer
        final_message = result["messages"][-1]
        
        # Get final scratchpad state
        scratchpad_contents = result.get("scratchpad", "")
        
        return {
            "answer": final_message.content if hasattr(final_message, 'content') else str(final_message),
            "scratchpad": scratchpad_contents,
            "full_conversation": result["messages"]
        }


def demo_context_offloading():
    """Demonstrate context offloading with scratchpad"""
    
    print("🚀 Context Offloading Demo for Product Management")
    print("=" * 60)
    
    # Test 1: Basic scratchpad within single session
    print("\n📝 Test 1: Basic Scratchpad (Single Session)")
    print("-" * 40)
    
    agent = PMOffloadingAgent(use_persistent_memory=False)
    
    queries = [
        "Research the current state of AI adoption in product management. Start by creating a research plan.",
        "Now search for specific statistics about AI tool usage by product managers.",
        "Based on your research so far, what are the key findings about AI in product management?"
    ]
    
    for query in queries:
        print(f"\n❓ Query: {query}")
        result = agent.query(query)
        print(f"\n📝 Answer: {result['answer']}")
        
        if result['scratchpad']:
            print(f"\n📋 Current Scratchpad:")
            print(result['scratchpad'][:500] + "..." if len(result['scratchpad']) > 500 else result['scratchpad'])
    
    # Test 2: Persistent memory across threads
    print("\n\n📝 Test 2: Persistent Memory (Cross-Thread)")
    print("-" * 40)
    
    persistent_agent = PMOffloadingAgent(use_persistent_memory=True)
    
    # First thread
    print("\n🧵 Thread 1: Initial Research")
    result1 = persistent_agent.query(
        "Research competitor analysis best practices for SaaS products. Create a comprehensive plan and save findings.",
        thread_id="research_thread_1"
    )
    print(f"Answer: {result1['answer'][:300]}...")
    
    # Second thread - should have access to previous research
    print("\n🧵 Thread 2: Continuing Research")
    result2 = persistent_agent.query(
        "Check your previous research notes and expand on the competitor analysis framework.",
        thread_id="research_thread_2"
    )
    print(f"Answer: {result2['answer'][:300]}...")
    
    # Return to first thread - should maintain its state
    print("\n🧵 Thread 1: Returning to Original Thread")
    result3 = persistent_agent.query(
        "Summarize the key points from your competitor analysis research.",
        thread_id="research_thread_1"
    )
    print(f"Answer: {result3['answer'][:300]}...")


def demo_memory_hierarchy():
    """Demonstrate memory hierarchy with hot/warm/cold storage"""
    
    print("\n\n🗄️ Memory Hierarchy Demo")
    print("=" * 60)
    
    # This would typically use a more sophisticated storage backend
    # For demo purposes, we're showing the concept
    
    class MemoryHierarchyAgent(PMOffloadingAgent):
        """Extended agent with memory hierarchy"""
        
        def __init__(self):
            super().__init__(use_persistent_memory=True)
            self.hot_memory = {}  # Immediate access
            self.warm_memory = {}  # Recent items
            self.cold_memory = {}  # Archived items
            
        def manage_memory_tiers(self, content: str, importance: float):
            """Move items between memory tiers based on importance and recency"""
            
            item_id = f"mem_{datetime.now().timestamp()}"
            
            if importance > 0.8:
                # High importance - keep in hot memory
                self.hot_memory[item_id] = {
                    "content": content,
                    "timestamp": datetime.now(),
                    "importance": importance
                }
            elif importance > 0.5:
                # Medium importance - warm memory
                self.warm_memory[item_id] = {
                    "content": content,
                    "timestamp": datetime.now(),
                    "importance": importance
                }
            else:
                # Low importance - cold storage
                self.cold_memory[item_id] = {
                    "content": content,
                    "timestamp": datetime.now(),
                    "importance": importance
                }
            
            # Age out old items
            self._age_memory_items()
            
            return item_id
        
        def _age_memory_items(self):
            """Move items to colder storage based on age"""
            now = datetime.now()
            
            # Move hot to warm after 5 minutes
            for item_id, item in list(self.hot_memory.items()):
                if (now - item["timestamp"]).seconds > 300:
                    self.warm_memory[item_id] = self.hot_memory.pop(item_id)
            
            # Move warm to cold after 15 minutes
            for item_id, item in list(self.warm_memory.items()):
                if (now - item["timestamp"]).seconds > 900:
                    self.cold_memory[item_id] = self.warm_memory.pop(item_id)
    
    # Demo the hierarchy
    hierarchy_agent = MemoryHierarchyAgent()
    
    # Store items with different importance
    items = [
        ("Critical product decision: Move to microservices architecture", 0.9),
        ("Team standup notes from Monday", 0.3),
        ("Q4 revenue target: $2M MRR", 0.8),
        ("Lunch menu options for team outing", 0.1),
        ("Customer feedback on new feature", 0.7)
    ]
    
    print("\n📊 Storing items in memory hierarchy:")
    for content, importance in items:
        item_id = hierarchy_agent.manage_memory_tiers(content, importance)
        tier = "hot" if importance > 0.8 else "warm" if importance > 0.5 else "cold"
        print(f"  - [{tier.upper()}] {content[:50]}... (importance: {importance})")
    
    print(f"\n📈 Memory Distribution:")
    print(f"  - Hot Memory: {len(hierarchy_agent.hot_memory)} items")
    print(f"  - Warm Memory: {len(hierarchy_agent.warm_memory)} items")
    print(f"  - Cold Memory: {len(hierarchy_agent.cold_memory)} items")


if __name__ == "__main__":
    # Run main demo
    demo_context_offloading()
    
    # Run memory hierarchy demo
    demo_memory_hierarchy()