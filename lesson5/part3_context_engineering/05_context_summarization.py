"""
Context Summarization for Product Management using LangGraph.

Implements context summarization in tool responses:
- Summarization in tool node to reduce tokens
- Condensation while preserving critical information
- StateGraph workflow with summarization
- Uses smaller model for efficiency
- Maintains completeness while reducing verbosity

Based on: https://github.com/langchain-ai/how_to_fix_your_context/notebooks/05-context-summarization.ipynb
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


class SummarizationState(MessagesState):
    """Extended state that includes summarization tracking"""
    summary_stats: Dict[str, Any] = {}


class PMSummarizationAgent:
    """
    Product Management agent with context summarization in tool responses.
    """
    
    def __init__(self, collection_name: str = "pm_docs_summarized"):
        """Initialize agent with summarization capabilities"""
        
        # Initialize embeddings and vector store
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory="./chroma_db_summarized"
        )
        
        # Initialize LLMs
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        self.summarization_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        
        # Create retriever
        self.retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": 4}
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
The retrieved context will be automatically summarized to reduce token usage while preserving all critical information.

Provide comprehensive answers based on the summarized context."""
        
        # Summarization prompt
        self.tool_summarization_prompt = """You are an expert at condensing technical documents while preserving all critical information.

Transform the provided document into a comprehensive yet concise version.

Condensation Guidelines:
1. **Preserve All Key Information**: Include every important fact, statistic, finding, and conclusion
2. **Eliminate Verbosity**: Remove repetitive text, excessive explanations, and filler words
3. **Maintain Logical Structure**: Keep the natural flow and relationships between concepts
4. **Use Precise Language**: Replace lengthy phrases with direct, technical terminology
5. **Ensure Completeness**: The condensed version should contain all necessary information to fully understand the topic
6. **Keep Specific Details**: Preserve numbers, dates, names, and concrete examples

Target: Reduce content by 50-70% while retaining 100% of essential information.

Document to condense:
{document}

Provide the condensed version:"""
        
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
            chunk_size=2000,
            chunk_overlap=200
        )
        splits = text_splitter.split_documents(docs)
        
        # Add to vector store
        self.vectorstore.add_documents(splits)
        print(f"✅ Added {len(splits)} chunks from {len(documents)} documents")
    
    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow with summarization"""
        
        def llm_call(state: SummarizationState) -> dict:
            """LLM decides whether to call a tool or respond"""
            messages = [SystemMessage(content=self.system_prompt)] + state["messages"]
            response = self.llm_with_tools.invoke(messages)
            return {"messages": [response]}
        
        def tool_node_with_summarization(state: SummarizationState) -> dict:
            """Execute tool calls and summarize results for context efficiency"""
            
            results = []
            summary_stats = {}
            total_original = 0
            total_condensed = 0
            
            for tool_call in state["messages"][-1].tool_calls:
                tool = self.tools_by_name[tool_call["name"]]
                observation = tool.invoke(tool_call["args"])
                
                # Summarize the tool output to reduce context size
                summarization_messages = [
                    {
                        "role": "system",
                        "content": self.tool_summarization_prompt.format(
                            document=observation
                        )
                    },
                    {
                        "role": "user",
                        "content": "Condense this content while preserving all key information."
                    }
                ]
                
                condensed_response = self.summarization_llm.invoke(summarization_messages)
                condensed_content = condensed_response.content
                
                # Calculate statistics
                original_len = len(observation)
                condensed_len = len(condensed_content)
                reduction_pct = ((original_len - condensed_len) / original_len * 100) if original_len > 0 else 0
                
                total_original += original_len
                total_condensed += condensed_len
                
                # Add metadata about summarization
                condensed_with_meta = f"{condensed_content}\n\n[Content condensed by {reduction_pct:.1f}% for efficiency]"
                
                results.append(
                    ToolMessage(
                        content=condensed_with_meta,
                        tool_call_id=tool_call["id"]
                    )
                )
            
            # Update summary statistics
            if total_original > 0:
                summary_stats = {
                    "total_original_chars": total_original,
                    "total_condensed_chars": total_condensed,
                    "overall_reduction_pct": ((total_original - total_condensed) / total_original * 100),
                    "compression_ratio": total_condensed / total_original
                }
            
            return {
                "messages": results,
                "summary_stats": summary_stats
            }
        
        def should_continue(state: SummarizationState) -> Literal["tool_node_with_summarization", "__end__"]:
            """Decide whether to continue with tool calls or end"""
            last_message = state["messages"][-1]
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                return "tool_node_with_summarization"
            return END
        
        # Build workflow
        workflow = StateGraph(SummarizationState)
        
        # Add nodes
        workflow.add_node("llm_call", llm_call)
        workflow.add_node("tool_node_with_summarization", tool_node_with_summarization)
        
        # Add edges
        workflow.add_edge(START, "llm_call")
        workflow.add_conditional_edges(
            "llm_call",
            should_continue,
            {
                "tool_node_with_summarization": "tool_node_with_summarization",
                END: END,
            }
        )
        workflow.add_edge("tool_node_with_summarization", "llm_call")
        
        # Compile
        return workflow.compile()
    
    def query(self, question: str) -> Dict[str, Any]:
        """Query the agent with context summarization"""
        
        result = self.agent.invoke({
            "messages": [HumanMessage(content=question)]
        })
        
        # Extract final answer
        final_message = result["messages"][-1]
        
        # Get summarization stats
        summary_stats = result.get("summary_stats", {})
        
        # Find summarized content
        summarized_contexts = []
        for msg in result["messages"]:
            if isinstance(msg, ToolMessage):
                if "[Content condensed by" in msg.content:
                    summarized_contexts.append(msg.content.split("\n\n[Content condensed")[0][:200] + "...")
        
        return {
            "answer": final_message.content if hasattr(final_message, 'content') else str(final_message),
            "summarized_contexts": summarized_contexts[:3],
            "summary_stats": summary_stats,
            "full_conversation": result["messages"]
        }


def demo_summarization_agent():
    """Demonstrate context summarization in RAG"""
    
    print("🚀 Context Summarization Demo for Product Management")
    print("=" * 60)
    
    # Initialize agent
    agent = PMSummarizationAgent()
    
    # Add sample documents
    documents = [
        {
            "content": """Product Performance Report - Q4 2024
            
            Executive Overview:
            The fourth quarter of 2024 marked a significant period of growth and transformation
            for our product portfolio. We witnessed substantial improvements across all key
            performance indicators, driven by strategic feature releases, enhanced user experience
            initiatives, and targeted market expansion efforts.
            
            User Growth Metrics:
            Our user base expanded dramatically during Q4, with Monthly Active Users (MAU)
            reaching 125,000, representing a 25% quarter-over-quarter increase. This growth
            was particularly strong in the enterprise segment, where we saw a 40% increase
            in new account acquisitions. Daily Active Users (DAU) climbed to 45,000, a 30%
            increase from Q3, resulting in an improved stickiness ratio of 36%. The growth
            was driven by our new onboarding flow, which reduced time-to-first-value by 50%,
            and the launch of our mobile app, which contributed to 40% of new user acquisitions.
            
            Revenue Performance:
            Revenue metrics exceeded expectations with Monthly Recurring Revenue (MRR) reaching
            $1.25 million, an 18% increase from the previous quarter. Annual Recurring Revenue
            (ARR) now stands at $15 million, positioning us well for our Series B fundraising.
            Average Revenue Per User (ARPU) improved to $45, up from $39 in Q3, driven by
            successful upselling campaigns and the introduction of premium features. Our
            Customer Acquisition Cost (CAC) decreased to $120, while Lifetime Value (LTV)
            increased to $540, resulting in a healthy LTV/CAC ratio of 4.5.
            
            Product Development Achievements:
            The engineering team successfully delivered 15 major features and resolved 247 bugs
            during Q4. Key launches included the AI-powered analytics dashboard, real-time
            collaboration tools, and enterprise SSO integration. Our deployment frequency
            increased to 3.5 times per week, while maintaining a change failure rate below 5%.
            The team also made significant progress on technical debt, reducing it by 30%
            through targeted refactoring efforts.
            
            Customer Satisfaction:
            Net Promoter Score (NPS) improved significantly to 58, up from 42 in Q3. This
            improvement was driven by enhanced product stability, faster support response times,
            and the delivery of highly requested features. Customer support ticket volume
            decreased by 20% despite user growth, indicating improved product quality. Our
            average resolution time dropped to 4 hours, with 95% of tickets resolved within SLA.
            
            Market Position:
            We strengthened our position as the preferred solution for mid-market companies,
            with 60% of new customers coming from this segment. Competitive win rate improved
            to 45%, up from 35% in Q3. Brand awareness increased by 30% based on survey data,
            aided by our content marketing efforts and industry conference participation.
            
            Challenges and Opportunities:
            Despite strong performance, we face challenges including increased competition from
            well-funded startups, technical scaling issues during peak usage, and the need for
            more localized solutions for international markets. Opportunities include expansion
            into adjacent verticals, development of an ecosystem through API partnerships, and
            potential acquisition targets for accelerated growth.""",
            "metadata": {
                "doc_type": "Performance Report",
                "quarter": "Q4 2024"
            }
        },
        {
            "content": """Feature Prioritization Framework and Roadmap
            
            Framework Overview:
            Our feature prioritization framework combines quantitative scoring methodologies
            with qualitative strategic assessment to ensure optimal resource allocation and
            maximum value delivery. We employ a hybrid approach incorporating RICE scoring,
            Kano model analysis, and strategic alignment assessment.
            
            RICE Scoring Methodology:
            Reach: We estimate the number of users or customers affected by each feature within
            a defined time period, typically one quarter. This includes both direct users and
            indirect beneficiaries.
            
            Impact: We assess the degree of impact on individual users using a scale from 0.25
            (minimal) to 3 (massive). Impact considers user satisfaction, revenue potential,
            and strategic value.
            
            Confidence: We evaluate our confidence in the estimates using percentages from 50%
            (low confidence) to 100% (high confidence). This accounts for market uncertainty,
            technical complexity, and data quality.
            
            Effort: We estimate person-months required for complete implementation, including
            development, testing, documentation, and deployment.
            
            Current Priority Queue:
            
            1. Advanced Analytics Dashboard (RICE: 2,500)
               - Reach: 5,000 users
               - Impact: 3 (massive)
               - Confidence: 80%
               - Effort: 6 person-months
               - Strategic rationale: Differentiator in enterprise segment
            
            2. API v2 Development (RICE: 1,800)
               - Reach: 2,000 integration partners
               - Impact: 3 (massive)
               - Confidence: 90%
               - Effort: 4 person-months
               - Strategic rationale: Ecosystem expansion enabler
            
            3. Mobile Offline Mode (RICE: 1,200)
               - Reach: 3,000 mobile users
               - Impact: 2 (high)
               - Confidence: 70%
               - Effort: 3.5 person-months
               - Strategic rationale: Field sales enablement
            
            4. Automated Workflows (RICE: 1,000)
               - Reach: 4,000 users
               - Impact: 2 (high)
               - Confidence: 60%
               - Effort: 4 person-months
               - Strategic rationale: Operational efficiency improvement
            
            5. Collaborative Editing (RICE: 950)
               - Reach: 2,500 team users
               - Impact: 2 (high)
               - Confidence: 75%
               - Effort: 4 person-months
               - Strategic rationale: Team collaboration enhancement
            
            Quarterly Capacity Allocation:
            Q1 2025: 24 person-months available
            - 40% on priority features (9.6 PM)
            - 20% on technical debt (4.8 PM)
            - 20% on bugs and maintenance (4.8 PM)
            - 20% on innovation/experiments (4.8 PM)
            
            Strategic Themes:
            - Enterprise readiness: SSO, audit logs, compliance
            - Platform extensibility: APIs, webhooks, integrations
            - User engagement: Gamification, social features
            - Performance optimization: Speed, reliability, scalability
            - Market expansion: Localization, vertical solutions""",
            "metadata": {
                "doc_type": "Prioritization Framework",
                "date": "2024-12-20"
            }
        }
    ]
    
    print("\n📚 Adding PM documents to vector store...")
    agent.add_documents(documents)
    
    # Test queries
    print("\n\n💬 Testing Context Summarization")
    print("-" * 40)
    
    test_queries = [
        "What were our key revenue metrics in Q4 2024?",
        "Explain the RICE scoring methodology we use",
        "What is our current NPS score and what drove the improvement?",
        "What are the top 3 priority features and their RICE scores?",
        "How are we allocating capacity in Q1 2025?"
    ]
    
    for query in test_queries:
        print(f"\n❓ Query: {query}")
        result = agent.query(query)
        print(f"\n📝 Answer: {result['answer']}")
        
        if result.get('summary_stats'):
            stats = result['summary_stats']
            if stats:
                print(f"\n📊 Summarization Stats:")
                print(f"  - Original: {stats.get('total_original_chars', 0):,} chars")
                print(f"  - Condensed: {stats.get('total_condensed_chars', 0):,} chars")
                print(f"  - Reduction: {stats.get('overall_reduction_pct', 0):.1f}%")
        
        if result['summarized_contexts']:
            print(f"\n📄 Summarized Context Samples:")
            for i, context in enumerate(result['summarized_contexts'], 1):
                print(f"  {i}. {context}")
        print("-" * 40)


if __name__ == "__main__":
    demo_summarization_agent()