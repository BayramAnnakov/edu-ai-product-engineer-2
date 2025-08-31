"""
Context Pruning for Product Management using LangGraph.

Implements LLM-based context pruning following the LangGraph pattern:
- LLM-driven pruning in tool responses
- Removes irrelevant information based on user request
- StateGraph workflow with pruning node
- Focus on maintaining relevant context only
- Token reduction while preserving essential information

Based on: https://github.com/langchain-ai/how_to_fix_your_context/notebooks/04-context-pruning.ipynb
"""

import os
from typing import List, Dict, Any, Literal
from datetime import datetime

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.tools.retriever import create_retriever_tool
from langchain_core.messages import SystemMessage, ToolMessage, HumanMessage
from langgraph.graph import END, START, StateGraph, MessagesState

from dotenv import load_dotenv
load_dotenv()


class PruningState(MessagesState):
    """Extended state that includes pruning capabilities"""
    initial_request: str = ""


class PMPruningAgent:
    """
    Product Management agent with context pruning in tool responses.
    """
    
    def __init__(self, collection_name: str = "pm_docs_pruned"):
        """Initialize agent with pruning capabilities"""
        
        # Initialize embeddings and vector store
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory="./chroma_db_pruned"
        )
        
        # Initialize LLMs
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        self.pruning_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        
        # Create retriever
        self.retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": 6}  # Get more initially, then prune
        )
        
        # Create retriever tool
        self.retriever_tool = create_retriever_tool(
            self.retriever,
            "retrieve_pm_docs",
            "Search and return information from Product Management documents."
        )
        
        # Set up tools
        self.tools = [self.retriever_tool]
        self.tools_by_name = {tool.name: tool for tool in self.tools}
        
        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # System prompt
        self.system_prompt = """You are a Product Management assistant with access to document repositories.

Use the retrieval tool to gather relevant context before answering questions.
The retrieved context will be automatically pruned to focus on information most relevant to the user's request.

Provide clear, actionable answers based on the pruned context."""
        
        # Pruning prompt
        self.pruning_prompt = """You are an expert at extracting relevant information from documents.

Your task: Analyze the provided document and extract ONLY the information that directly answers or supports the user's specific request.

User's Request: {initial_request}

Instructions for pruning:
1. Keep information that directly addresses the user's question
2. Preserve key facts, data, metrics, and examples that support the answer
3. Remove tangential discussions, unrelated topics, and excessive background
4. Maintain the logical flow and context of relevant information
5. Focus only on content needed to answer the user's request
6. Preserve important numbers, dates, and specific details when relevant

Document to prune:
{document}

Return the pruned content that focuses solely on answering the user's request."""
        
        # Build workflow
        self.agent = self._build_workflow()
    
    def add_documents(self, documents: List[Dict[str, str]]) -> None:
        """Add documents to the vector store"""
        from langchain.schema import Document
        
        docs = []
        for doc in documents:
            docs.append(Document(
                page_content=doc['content'],
                metadata=doc.get('metadata', {})
            ))
        
        # Split documents
        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=3000,
            chunk_overlap=200
        )
        splits = text_splitter.split_documents(docs)
        
        # Add to vector store
        self.vectorstore.add_documents(splits)
        print(f"✅ Added {len(splits)} chunks from {len(documents)} documents")
    
    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow with pruning"""
        
        def llm_call(state: PruningState) -> dict:
            """LLM decides whether to call a tool or respond"""
            
            # Store initial request if this is the first message
            if state["messages"] and isinstance(state["messages"][0], HumanMessage):
                initial_request = state["messages"][0].content
            else:
                initial_request = state.get("initial_request", "")
            
            messages = [SystemMessage(content=self.system_prompt)] + state["messages"]
            response = self.llm_with_tools.invoke(messages)
            
            return {
                "messages": [response],
                "initial_request": initial_request
            }
        
        def tool_node_with_pruning(state: PruningState) -> dict:
            """Execute tool calls with context pruning"""
            
            results = []
            for tool_call in state["messages"][-1].tool_calls:
                tool = self.tools_by_name[tool_call["name"]]
                observation = tool.invoke(tool_call["args"])
                
                # Get the initial user request
                initial_request = state.get("initial_request", "")
                
                # Prune the document content to focus on user's request
                pruning_messages = [
                    {
                        "role": "system",
                        "content": self.pruning_prompt.format(
                            initial_request=initial_request,
                            document=observation
                        )
                    },
                    {
                        "role": "user",
                        "content": "Extract only the relevant information."
                    }
                ]
                
                pruned_response = self.pruning_llm.invoke(pruning_messages)
                pruned_content = pruned_response.content
                
                # Calculate reduction
                original_len = len(observation)
                pruned_len = len(pruned_content)
                reduction_pct = ((original_len - pruned_len) / original_len * 100) if original_len > 0 else 0
                
                # Add metadata about pruning
                pruned_with_meta = f"{pruned_content}\n\n[Context pruned by {reduction_pct:.1f}% to focus on relevant information]"
                
                results.append(
                    ToolMessage(
                        content=pruned_with_meta,
                        tool_call_id=tool_call["id"]
                    )
                )
            
            return {"messages": results}
        
        def should_continue(state: PruningState) -> Literal["tool_node_with_pruning", "__end__"]:
            """Decide whether to continue with tool calls or end"""
            last_message = state["messages"][-1]
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                return "tool_node_with_pruning"
            return END
        
        # Build workflow
        workflow = StateGraph(PruningState)
        
        # Add nodes
        workflow.add_node("llm_call", llm_call)
        workflow.add_node("tool_node_with_pruning", tool_node_with_pruning)
        
        # Add edges
        workflow.add_edge(START, "llm_call")
        workflow.add_conditional_edges(
            "llm_call",
            should_continue,
            {
                "tool_node_with_pruning": "tool_node_with_pruning",
                END: END,
            }
        )
        workflow.add_edge("tool_node_with_pruning", "llm_call")
        
        # Compile
        return workflow.compile()
    
    def query(self, question: str) -> Dict[str, Any]:
        """Query the agent with context pruning"""
        
        result = self.agent.invoke({
            "messages": [HumanMessage(content=question)],
            "initial_request": question
        })
        
        # Extract final answer
        final_message = result["messages"][-1]
        
        # Find pruned content
        pruned_contexts = []
        for msg in result["messages"]:
            if isinstance(msg, ToolMessage):
                # Extract pruning info
                if "[Context pruned by" in msg.content:
                    pruned_contexts.append(msg.content.split("\n\n[Context pruned")[0][:200] + "...")
        
        return {
            "answer": final_message.content if hasattr(final_message, 'content') else str(final_message),
            "pruned_contexts": pruned_contexts[:3],
            "full_conversation": result["messages"]
        }


def demo_pruning_agent():
    """Demonstrate context pruning in RAG"""
    
    print("🚀 Context Pruning Demo for Product Management")
    print("=" * 60)
    
    # Initialize agent
    agent = PMPruningAgent()
    
    # Add sample documents with lots of content
    documents = [
        {
            "content": """Product Strategy Document Q1 2025
            
            Executive Summary:
            This document outlines our comprehensive product strategy for Q1 2025, covering all aspects
            of product development, market positioning, and growth initiatives. We'll discuss various
            topics including market trends, competitive landscape, technical architecture, design systems,
            marketing campaigns, sales enablement, customer success programs, and much more.
            
            Market Analysis:
            The SaaS market continues to grow at 18% annually. Cloud adoption is accelerating across
            all industries. Digital transformation initiatives are driving demand. Remote work trends
            persist post-pandemic. AI integration is becoming table stakes. Security concerns are
            paramount. Privacy regulations are tightening globally.
            
            Product Roadmap Highlights:
            - Feature A: Advanced analytics dashboard with ML-powered insights (Launch: February)
            - Feature B: Real-time collaboration tools for distributed teams (Launch: March)
            - Feature C: API v2 with GraphQL support for enterprise clients (Launch: January)
            - Feature D: Mobile app redesign with offline capabilities (Launch: March)
            
            Technical Initiatives:
            Infrastructure modernization including Kubernetes migration. Microservices architecture
            adoption. Event-driven design patterns. GraphQL API implementation. Real-time data
            streaming. Machine learning pipeline development. Security hardening. Performance
            optimization. Database sharding strategy. CDN implementation.
            
            Customer Feedback Themes:
            Users love the intuitive interface but want more customization options. Performance
            during peak hours needs improvement. Mobile experience requires enhancement. Integration
            with third-party tools is highly requested. Advanced filtering and search capabilities
            are needed. Bulk operations would save time. Better onboarding flow is essential.
            
            Competitive Positioning:
            We're positioned as the mid-market leader with superior UX. Our pricing is competitive
            but not the cheapest. Feature parity with top competitors on core functionality.
            Differentiation through AI-powered insights and automation. Strong customer support
            is a key advantage. Faster implementation time than enterprise solutions.
            
            Success Metrics:
            - User activation rate target: 65% (currently 52%)
            - Feature adoption goal: 40% using new features within 30 days
            - NPS target: 50+ (currently 42)
            - Monthly churn target: <3% (currently 4.2%)
            - Customer satisfaction: 4.5/5 stars
            
            Go-to-Market Strategy:
            Product-led growth with free trial. Content marketing and SEO focus. Webinar series
            for education. Partnership channel development. Referral program enhancement. Account-based
            marketing for enterprise. Social media engagement. Influencer partnerships.""",
            "metadata": {
                "doc_type": "Strategy",
                "quarter": "Q1 2025"
            }
        },
        {
            "content": """Sprint 45 Retrospective and Planning
            
            Retrospective Summary:
            Sprint 45 was challenging but productive. We faced several blockers including third-party
            API downtime, unexpected complexity in the payment integration, team member illness, and
            scope creep on the dashboard project. Despite these challenges, we delivered most planned
            features and maintained quality standards.
            
            What Went Well:
            - Daily standups were efficient and focused
            - Pair programming sessions improved code quality
            - Automated testing caught several bugs early
            - Team collaboration was excellent
            - Documentation was kept up-to-date
            - Customer feedback was incorporated quickly
            
            What Didn't Go Well:
            - Estimation accuracy was poor (only 60% of stories properly sized)
            - Too many context switches due to urgent bugs
            - Insufficient time for code reviews
            - Technical debt accumulated in the auth module
            - Deployment pipeline had multiple failures
            - Communication with stakeholders could be better
            
            Sprint 46 Planning:
            
            Capacity: 42 story points (accounting for upcoming holiday)
            
            Committed User Stories:
            1. FEAT-234: Implement SSO for enterprise clients (8 points)
               - Acceptance criteria: SAML 2.0 support, Admin configuration UI, Testing with 3 providers
            
            2. FEAT-235: Dashboard performance optimization (5 points)
               - Acceptance criteria: Load time <2s, Support 10k data points, Smooth scrolling
            
            3. FEAT-236: Mobile push notifications (8 points)
               - Acceptance criteria: iOS and Android support, User preferences, Rich notifications
            
            4. BUG-456: Fix data export memory leak (3 points)
               - Acceptance criteria: Memory usage stable, Support 1M+ rows, No timeout errors
            
            5. TECH-789: Refactor authentication module (13 points)
               - Acceptance criteria: Improved test coverage, Reduced complexity, Better error handling
            
            6. FEAT-237: Add bulk user import (5 points)
               - Acceptance criteria: CSV support, Validation rules, Error reporting
            
            Technical Tasks:
            - Database index optimization
            - Security audit preparation
            - Performance profiling setup
            - CI/CD pipeline improvements
            - Documentation updates
            
            Risks and Mitigations:
            - SSO complexity might be underestimated → Time-boxed spike first
            - Third-party service dependencies → Build fallback mechanisms
            - Team member on vacation next week → Knowledge transfer session
            
            Definition of Done:
            - Code reviewed and approved
            - Unit tests written and passing
            - Integration tests completed
            - Documentation updated
            - Deployed to staging
            - QA sign-off received""",
            "metadata": {
                "doc_type": "Sprint Planning",
                "sprint": "46"
            }
        },
        {
            "content": """User Research Findings - December 2024
            
            Research Methodology:
            We conducted 50 user interviews, 500 survey responses, 10 usability tests, 5 focus groups,
            and analyzed 6 months of usage data. Participants included power users, new users,
            churned users, and potential customers across various industries and company sizes.
            
            User Personas Identified:
            
            1. The Efficiency Expert (35% of users)
            - Wants to automate everything possible
            - Values keyboard shortcuts and bulk operations
            - Frustrated by repetitive tasks
            - Needs powerful filtering and search
            - Decision maker: Team lead or manager
            
            2. The Data Analyst (25% of users)
            - Needs advanced analytics and reporting
            - Wants to export and manipulate data
            - Requires API access for integrations
            - Values accuracy and real-time updates
            - Decision maker: Analytics team
            
            3. The Collaborator (20% of users)
            - Focuses on team features and sharing
            - Needs commenting and notifications
            - Wants activity feeds and history
            - Values transparency and communication
            - Decision maker: Project manager
            
            4. The Executive (20% of users)
            - Wants high-level dashboards
            - Needs executive summaries
            - Values mobile access
            - Requires scheduled reports
            - Decision maker: C-suite
            
            Key Pain Points:
            
            Onboarding Issues:
            - 40% of users struggle with initial setup
            - Configuration options are overwhelming
            - Lack of templates for common use cases
            - Tutorial is too long and not interactive
            - No progressive disclosure of features
            
            Performance Problems:
            - Dashboard loads slowly with large datasets
            - Search functionality is not intuitive
            - Filters reset unexpectedly
            - Mobile app crashes frequently
            - Sync issues between devices
            
            Feature Gaps:
            - No dark mode option (requested by 60% of users)
            - Limited customization of dashboards
            - Can't schedule recurring tasks
            - No offline mode for mobile
            - Lack of advanced automation rules
            
            Feature Usage Statistics:
            - Dashboard: 95% daily usage
            - Reports: 70% weekly usage
            - Collaboration: 45% daily usage
            - API: 15% of accounts
            - Mobile: 30% of total usage
            - Integrations: 25% have at least one
            
            Customer Satisfaction:
            - Overall NPS: 42
            - Promoters cite ease of use and support
            - Detractors mention performance and missing features
            - Feature satisfaction ranges from 3.2 to 4.6 out of 5
            - Support satisfaction: 4.5/5
            
            Competitive Comparison Feedback:
            Users prefer our UX but want competitor features like advanced automation,
            better integrations, more customization options, and enterprise features.
            Price is seen as fair but not compelling without differentiating features.""",
            "metadata": {
                "doc_type": "User Research",
                "date": "December 2024"
            }
        }
    ]
    
    print("\n📚 Adding PM documents to vector store...")
    agent.add_documents(documents)
    
    # Test queries - specific questions that should trigger pruning
    print("\n\n💬 Testing Context Pruning")
    print("-" * 40)
    
    test_queries = [
        "What are the sprint 46 committed user stories and their story points?",
        "What is our NPS target for Q1 2025?",
        "What percentage of users struggle with initial setup?",
        "What features are launching in March according to the roadmap?",
        "What were the specific acceptance criteria for the SSO implementation?"
    ]
    
    for query in test_queries:
        print(f"\n❓ Query: {query}")
        result = agent.query(query)
        print(f"\n📝 Answer: {result['answer']}")
        
        if result['pruned_contexts']:
            print(f"\n✂️ Pruned Context Samples:")
            for i, context in enumerate(result['pruned_contexts'], 1):
                print(f"  {i}. {context}")
        print("-" * 40)


if __name__ == "__main__":
    demo_pruning_agent()