"""
Enhanced RAG System for Product Management using LangGraph.

Implements Retrieval-Augmented Generation following the LangGraph pattern:
- Document loading and chunking
- Vector store with embeddings
- Retriever tool for context fetching
- LangGraph workflow with state management
- Tool-based architecture

Based on: https://github.com/langchain-ai/how_to_fix_your_context/notebooks/01-rag.ipynb
"""

import os
from typing import List, Dict, Any, Literal
from typing_extensions import TypedDict
from datetime import datetime
import json

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.tools.retriever import create_retriever_tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, ToolMessage, HumanMessage, AIMessage
from langgraph.graph import END, START, StateGraph, MessagesState

from dotenv import load_dotenv
load_dotenv()


class PMRAGAgent:
    """
    Product Management RAG agent using LangGraph workflow.
    """
    
    def __init__(self, collection_name: str = "pm_documents"):
        """Initialize RAG agent with vector store and tools"""
        
        # Initialize embeddings and vector store
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory="./chroma_db"
        )
        
        # Initialize LLM
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        
        # Create retriever
        self.retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": 4}
        )
        
        # Create retriever tool
        self.retriever_tool = create_retriever_tool(
            self.retriever,
            "retrieve_pm_docs",
            "Search and return information from Product Management documents including PRDs, metrics, sprint planning, and user feedback."
        )
        
        # Set up tools
        self.tools = [self.retriever_tool]
        self.tools_by_name = {tool.name: tool for tool in self.tools}
        
        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # System prompt for PM assistant
        self.system_prompt = """You are a Product Management assistant with access to a comprehensive document repository.

Your capabilities include:
- Retrieving information from PRDs, specifications, and planning documents
- Analyzing product metrics and KPIs
- Providing insights on sprint planning and agile processes
- Synthesizing user feedback and market research

When answering questions:
1. First clarify the scope if needed
2. Use the retrieval tool to gather relevant context
3. Provide comprehensive, actionable answers
4. Reference specific documents when possible

Always use the retrieval tool before providing answers that require specific information."""
        
        # Build the workflow
        self.agent = self._build_workflow()
    
    def add_documents(self, documents: List[Dict[str, str]]) -> None:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of dicts with 'content' and 'metadata' keys
        """
        from langchain.schema import Document
        
        # Create Document objects
        docs = []
        for doc in documents:
            docs.append(Document(
                page_content=doc['content'],
                metadata=doc.get('metadata', {})
            ))
        
        # Split documents
        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=2000,
            chunk_overlap=200
        )
        splits = text_splitter.split_documents(docs)
        
        # Add to vector store
        self.vectorstore.add_documents(splits)
        print(f"✅ Added {len(splits)} chunks from {len(documents)} documents")
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for RAG"""
        
        def llm_call(state: MessagesState) -> dict:
            """LLM decides whether to call a tool or respond"""
            messages = [SystemMessage(content=self.system_prompt)] + state["messages"]
            response = self.llm_with_tools.invoke(messages)
            return {"messages": [response]}
        
        def tool_node(state: MessagesState) -> dict:
            """Execute tool calls"""
            results = []
            for tool_call in state["messages"][-1].tool_calls:
                tool = self.tools_by_name[tool_call["name"]]
                observation = tool.invoke(tool_call["args"])
                results.append(
                    ToolMessage(
                        content=observation,
                        tool_call_id=tool_call["id"]
                    )
                )
            return {"messages": results}
        
        def should_continue(state: MessagesState) -> Literal["tool_node", "__end__"]:
            """Decide whether to continue with tool calls or end"""
            last_message = state["messages"][-1]
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                return "tool_node"
            return END
        
        # Build the graph
        workflow = StateGraph(MessagesState)
        
        # Add nodes
        workflow.add_node("llm_call", llm_call)
        workflow.add_node("tool_node", tool_node)
        
        # Add edges
        workflow.add_edge(START, "llm_call")
        workflow.add_conditional_edges(
            "llm_call",
            should_continue,
            {
                "tool_node": "tool_node",
                END: END,
            }
        )
        workflow.add_edge("tool_node", "llm_call")
        
        # Compile
        return workflow.compile()
    
    def query(self, question: str) -> Dict[str, Any]:
        """
        Query the RAG system.
        
        Args:
            question: User's question
            
        Returns:
            Response with answer and sources
        """
        result = self.agent.invoke({
            "messages": [HumanMessage(content=question)]
        })
        
        # Extract the final answer
        final_message = result["messages"][-1]
        
        # Find tool calls for sources
        sources = []
        for msg in result["messages"]:
            if isinstance(msg, ToolMessage):
                # Extract first 100 chars as preview
                sources.append(msg.content[:200] + "...")
        
        return {
            "answer": final_message.content if hasattr(final_message, 'content') else str(final_message),
            "sources": sources[:3],  # Top 3 sources
            "full_conversation": result["messages"]
        }


def demo_rag_agent():
    """Demonstrate the RAG agent with PM documents"""
    
    print("🚀 LangGraph RAG Agent Demo for Product Management")
    print("=" * 60)
    
    # Initialize agent
    agent = PMRAGAgent()
    
    # Add sample PM documents
    documents = [
        {
            "content": """Product Requirements Document: AI-Powered Analytics Dashboard
            
            Overview:
            We're building an AI-powered analytics dashboard that provides real-time insights
            for product managers. The dashboard will use machine learning to identify trends,
            anomalies, and opportunities in product metrics.
            
            Key Features:
            1. Real-time metric tracking (MAU, DAU, retention, revenue)
            2. Anomaly detection using statistical models
            3. Predictive analytics for user churn
            4. Natural language querying of metrics
            5. Automated insight generation
            
            Success Metrics:
            - 80% reduction in time to identify metric anomalies
            - 60% improvement in forecast accuracy
            - 90% user satisfaction score
            
            Timeline: Q1 2025 launch with phased rollout""",
            "metadata": {
                "doc_type": "PRD",
                "product": "Analytics Dashboard",
                "version": "1.0",
                "date": "2024-12-01"
            }
        },
        {
            "content": """Sprint Planning Meeting Notes - Sprint 42
            
            Date: 2024-12-15
            Attendees: Product Team, Engineering, Design
            
            Sprint Goals:
            1. Complete user authentication flow
            2. Implement basic dashboard layout
            3. Set up data pipeline for metrics ingestion
            
            Capacity Planning:
            - Team velocity: 45 story points
            - Available capacity: 40 points (accounting for holidays)
            - Technical debt allocation: 8 points (20%)
            
            Committed Items:
            - AUTH-101: OAuth integration (8 points)
            - DASH-201: Dashboard wireframe implementation (13 points)
            - DATA-301: Metrics pipeline setup (8 points)
            - TECH-401: Database optimization (5 points)
            - BUG-501: Fix metric calculation errors (6 points)
            
            Risks:
            - Third-party API dependencies for OAuth
            - Data pipeline complexity higher than estimated
            
            Action Items:
            - Review API documentation by EOD Monday
            - Schedule architecture review for pipeline""",
            "metadata": {
                "doc_type": "Sprint Planning",
                "sprint": "42",
                "date": "2024-12-15"
            }
        },
        {
            "content": """Q4 2024 Product Metrics Report
            
            Executive Summary:
            Strong quarter with significant growth in user engagement and revenue metrics.
            
            Key Metrics:
            - Monthly Active Users (MAU): 125,000 (+25% QoQ)
            - Daily Active Users (DAU): 45,000 (+30% QoQ)
            - Stickiness (DAU/MAU): 36% (+2pp QoQ)
            - Average Revenue Per User (ARPU): $12.50 (+15% QoQ)
            - Customer Acquisition Cost (CAC): $35 (-10% QoQ)
            - Lifetime Value (LTV): $450 (+20% QoQ)
            - LTV/CAC Ratio: 12.9 (improved from 10.2)
            - Net Promoter Score (NPS): 72 (+8 points QoQ)
            - Customer Churn Rate: 3.5% monthly (-1.5pp QoQ)
            
            Growth Drivers:
            1. New feature adoption reached 65% of user base
            2. Mobile app launch contributed 40% of new users
            3. Improved onboarding reduced time-to-value by 50%
            
            Challenges:
            - Support ticket volume increased 40%
            - Performance issues in European region
            - Competitor launched similar features
            
            Recommendations:
            1. Invest in customer support automation
            2. Optimize infrastructure for global scale
            3. Accelerate innovation in differentiating features""",
            "metadata": {
                "doc_type": "Metrics Report",
                "quarter": "Q4 2024",
                "date": "2025-01-10"
            }
        },
        {
            "content": """User Feedback Synthesis - December 2024
            
            Feedback Sources:
            - In-app surveys: 2,500 responses
            - Customer interviews: 50 sessions
            - Support tickets: 1,200 analyzed
            - App store reviews: 500 reviews
            
            Top Themes:
            
            1. Performance & Reliability (35% of feedback)
            - Dashboard loading times too slow
            - Occasional data sync issues
            - Mobile app crashes on older devices
            
            2. Feature Requests (30% of feedback)
            - Advanced filtering options
            - Custom metric creation
            - Team collaboration features
            - Export capabilities for reports
            
            3. User Experience (20% of feedback)
            - Onboarding process still confusing
            - Navigation between sections unclear
            - Too many clicks to access key features
            
            4. Pricing & Value (15% of feedback)
            - Free tier too limited
            - Enterprise pricing not transparent
            - Value proposition unclear for mid-market
            
            Sentiment Analysis:
            - Positive: 62%
            - Neutral: 23%
            - Negative: 15%
            
            Priority Recommendations:
            1. Address performance issues immediately
            2. Simplify navigation in next sprint
            3. Add most requested features to roadmap
            4. Review pricing strategy for Q1""",
            "metadata": {
                "doc_type": "User Feedback",
                "period": "December 2024",
                "date": "2025-01-05"
            }
        }
    ]
    
    print("\n📚 Adding PM documents to vector store...")
    agent.add_documents(documents)
    
    # Test queries
    print("\n\n💬 Testing RAG Agent Queries")
    print("-" * 40)
    
    test_queries = [
        "What are the key features of the AI-powered analytics dashboard?",
        "What is our current team velocity and how are we allocating technical debt?",
        "How have our key metrics changed in Q4? What's our NPS score?",
        "What are the top user complaints and feature requests?",
        "What risks were identified in sprint planning?"
    ]
    
    for query in test_queries:
        print(f"\n❓ Query: {query}")
        result = agent.query(query)
        print(f"\n📝 Answer: {result['answer']}")
        
        if result['sources']:
            print(f"\n📚 Sources Used:")
            for i, source in enumerate(result['sources'], 1):
                print(f"  {i}. {source}")
        print("-" * 40)


if __name__ == "__main__":
    demo_rag_agent()