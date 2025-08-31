"""
Context Quarantine for Product Management using LangGraph Supervisor.

Implements multi-agent architecture with isolated contexts:
- Supervisor agent for task routing
- Specialized agents with isolated context windows
- Hierarchical multi-agent pattern
- Parallel context processing
- Agent handoff mechanisms

Based on: https://github.com/langchain-ai/how_to_fix_your_context/notebooks/03-context-quarantine.ipynb
"""

import os
from typing import List, Dict, Any, Literal
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor

from dotenv import load_dotenv
load_dotenv()


# Mock data retrieval tools for specialized agents
@tool
def fetch_sprint_metrics(sprint_id: str) -> str:
    """Fetch sprint metrics and velocity data"""
    return f"""Sprint {sprint_id} Metrics:
    - Velocity: 45 story points
    - Completion rate: 89%
    - Bugs introduced: 3
    - Technical debt ratio: 20%
    - Team capacity utilization: 92%
    - Sprint goal achievement: Partially met (3 of 4 objectives)
    - Carryover items: 2 stories (8 points)"""


@tool
def fetch_user_analytics(time_period: str) -> str:
    """Fetch user analytics and engagement metrics"""
    return f"""User Analytics for {time_period}:
    - Monthly Active Users (MAU): 125,000 (+25% MoM)
    - Daily Active Users (DAU): 45,000 (+30% MoM)
    - User Retention (Day 7): 65%
    - User Retention (Day 30): 42%
    - Average Session Duration: 12.5 minutes
    - Sessions per User: 3.2 per day
    - Feature Adoption Rate: 58% for new features
    - User Satisfaction Score: 4.2/5.0"""


@tool
def fetch_revenue_data(quarter: str) -> str:
    """Fetch revenue and financial metrics"""
    return f"""Revenue Data for {quarter}:
    - Monthly Recurring Revenue (MRR): $1.25M (+18% QoQ)
    - Annual Recurring Revenue (ARR): $15M
    - Average Revenue Per User (ARPU): $45
    - Customer Acquisition Cost (CAC): $120
    - Lifetime Value (LTV): $540
    - LTV/CAC Ratio: 4.5
    - Gross Margin: 72%
    - Net Revenue Retention: 115%"""


@tool
def fetch_product_feedback(category: str) -> str:
    """Fetch product feedback and feature requests"""
    return f"""Product Feedback for {category}:
    Top Feature Requests:
    1. Advanced filtering options (requested by 45% of users)
    2. API access for enterprise (requested by 30% of enterprise customers)
    3. Mobile app improvements (requested by 60% of mobile users)
    4. Collaboration features (requested by 35% of team accounts)
    
    Pain Points:
    - Performance issues during peak hours (reported by 25% of users)
    - Complex onboarding process (40% drop-off rate)
    - Limited customization options (feedback from 20% of power users)
    
    NPS Breakdown:
    - Promoters: 62%
    - Passives: 23%
    - Detractors: 15%
    - Overall NPS: 47"""


@tool
def fetch_competitor_analysis(competitor: str) -> str:
    """Fetch competitor analysis and market intelligence"""
    return f"""Competitor Analysis for {competitor}:
    Market Position:
    - Market Share: 18% (vs our 12%)
    - Customer Base: 45,000 companies
    - Pricing: 20% higher than our pricing
    - Key Differentiators: Advanced AI features, Better enterprise support
    
    Recent Updates:
    - Launched new AI-powered analytics (last month)
    - Acquired startup for $50M (data visualization)
    - Expanded to European market
    - Released major UI overhaul
    
    Customer Sentiment:
    - G2 Rating: 4.5/5.0 (vs our 4.3)
    - Main complaints: High price, Steep learning curve
    - Main praise: Powerful features, Good support"""


@tool
def fetch_technical_metrics(system: str) -> str:
    """Fetch technical performance and infrastructure metrics"""
    return f"""Technical Metrics for {system}:
    Performance:
    - API Response Time (P50): 120ms
    - API Response Time (P95): 450ms
    - API Response Time (P99): 1200ms
    - Uptime: 99.95% this month
    - Error Rate: 0.3%
    
    Infrastructure:
    - Database Size: 2.5TB
    - Daily API Calls: 15M
    - Peak Concurrent Users: 8,500
    - CDN Hit Rate: 89%
    - Container Utilization: 75%
    
    Issues:
    - Memory leak in analytics service (identified, fix in progress)
    - Database connection pooling needs optimization
    - CDN cache invalidation delays affecting 5% of users"""


class PMSupervisorAgent:
    """
    Product Management supervisor agent that coordinates specialized sub-agents.
    """
    
    def __init__(self):
        """Initialize supervisor and specialized agents"""
        
        # Initialize LLM
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        
        # Create specialized agents with isolated contexts
        self.agents = self._create_specialized_agents()
        
        # Create supervisor workflow
        self.supervisor = self._create_supervisor()
    
    def _create_specialized_agents(self) -> List[Any]:
        """Create specialized agents for different PM domains"""
        
        # Sprint Management Agent
        sprint_agent = create_react_agent(
            model=self.llm,
            tools=[fetch_sprint_metrics],
            name="sprint_manager",
            prompt="""You are a Sprint Management specialist focused on agile processes.
            
Your expertise includes:
- Sprint planning and velocity tracking
- Capacity management and forecasting
- Burndown analysis and impediment tracking
- Team performance metrics

When answering questions:
1. Use the sprint metrics tool to gather data
2. Provide specific insights about sprint performance
3. Identify trends and patterns in team velocity
4. Suggest improvements for sprint execution

You only handle sprint and agile-related queries."""
        )
        
        # User Analytics Agent
        analytics_agent = create_react_agent(
            model=self.llm,
            tools=[fetch_user_analytics],
            name="analytics_expert",
            prompt="""You are a User Analytics specialist focused on user behavior and engagement.
            
Your expertise includes:
- User engagement metrics (DAU, MAU, retention)
- Behavior analysis and segmentation
- Feature adoption tracking
- User satisfaction measurement

When answering questions:
1. Use the analytics tool to gather user data
2. Identify trends in user behavior
3. Provide actionable insights for improving engagement
4. Correlate metrics to understand user patterns

You only handle user analytics and engagement queries."""
        )
        
        # Revenue Agent
        revenue_agent = create_react_agent(
            model=self.llm,
            tools=[fetch_revenue_data],
            name="revenue_analyst",
            prompt="""You are a Revenue and Financial Metrics specialist.
            
Your expertise includes:
- Revenue metrics (MRR, ARR, ARPU)
- Unit economics (CAC, LTV, margins)
- Financial forecasting and modeling
- Pricing strategy analysis

When answering questions:
1. Use the revenue tool to gather financial data
2. Calculate key financial ratios and metrics
3. Identify revenue growth opportunities
4. Analyze pricing and monetization effectiveness

You only handle revenue and financial queries."""
        )
        
        # Product Feedback Agent
        feedback_agent = create_react_agent(
            model=self.llm,
            tools=[fetch_product_feedback],
            name="feedback_synthesizer",
            prompt="""You are a Product Feedback specialist focused on user voice and requirements.
            
Your expertise includes:
- Feature request analysis and prioritization
- User feedback synthesis
- NPS and satisfaction tracking
- Pain point identification

When answering questions:
1. Use the feedback tool to gather user input
2. Identify common themes and patterns
3. Prioritize feedback based on impact and frequency
4. Connect feedback to product strategy

You only handle product feedback and user voice queries."""
        )
        
        # Competitive Intelligence Agent
        competitor_agent = create_react_agent(
            model=self.llm,
            tools=[fetch_competitor_analysis],
            name="competitive_analyst",
            prompt="""You are a Competitive Intelligence specialist focused on market analysis.
            
Your expertise includes:
- Competitor feature analysis
- Market positioning and differentiation
- Pricing strategy comparison
- Competitive threat assessment

When answering questions:
1. Use the competitor tool to gather market data
2. Identify competitive advantages and gaps
3. Suggest strategic responses to competition
4. Track competitor movements and strategies

You only handle competitive and market analysis queries."""
        )
        
        # Technical Metrics Agent
        technical_agent = create_react_agent(
            model=self.llm,
            tools=[fetch_technical_metrics],
            name="technical_analyst",
            prompt="""You are a Technical Metrics specialist focused on system performance.
            
Your expertise includes:
- Performance metrics and monitoring
- Infrastructure capacity planning
- Error rate and uptime analysis
- Technical debt assessment

When answering questions:
1. Use the technical metrics tool to gather system data
2. Identify performance bottlenecks
3. Suggest technical improvements
4. Correlate technical metrics with user experience

You only handle technical and infrastructure queries."""
        )
        
        return [
            sprint_agent,
            analytics_agent,
            revenue_agent,
            feedback_agent,
            competitor_agent,
            technical_agent
        ]
    
    def _create_supervisor(self) -> Any:
        """Create supervisor workflow for coordinating agents"""
        
        supervisor_prompt = """You are a Product Management team supervisor coordinating specialized experts.

Your team includes:
1. **sprint_manager**: Handles sprint planning, velocity, and agile metrics
2. **analytics_expert**: Handles user analytics, engagement, and behavior metrics
3. **revenue_analyst**: Handles revenue, financial metrics, and unit economics
4. **feedback_synthesizer**: Handles user feedback, feature requests, and NPS
5. **competitive_analyst**: Handles competitor analysis and market intelligence
6. **technical_analyst**: Handles technical performance and infrastructure metrics

Your role:
1. Analyze incoming requests to determine required expertise
2. Delegate to the most appropriate specialist(s)
3. For complex queries spanning multiple domains, coordinate sequential delegation
4. Synthesize responses from multiple agents when necessary

Delegation strategy:
- Sprint/agile questions → sprint_manager
- User behavior/engagement → analytics_expert
- Revenue/financial metrics → revenue_analyst
- User feedback/requests → feedback_synthesizer
- Competition/market → competitive_analyst
- Technical/performance → technical_analyst

For queries requiring multiple perspectives:
1. First gather data from relevant specialists
2. Then synthesize insights across domains
3. Provide integrated recommendations

Important: You coordinate but don't execute. Always delegate to specialists."""
        
        return create_supervisor(
            self.agents,
            model=self.llm,
            prompt=supervisor_prompt
        )
    
    def query(self, question: str) -> Dict[str, Any]:
        """
        Query the supervisor system.
        
        Args:
            question: User's question
            
        Returns:
            Response with answer and agent routing information
        """
        
        # Compile the supervisor workflow
        app = self.supervisor.compile()
        
        # Execute query
        result = app.invoke({
            "messages": [HumanMessage(content=question)]
        })
        
        # Extract routing information
        agents_used = []
        for msg in result.get("messages", []):
            # Check for tool calls that indicate agent routing
            if hasattr(msg, "name") and msg.name:
                agents_used.append(msg.name)
        
        # Get final response
        final_message = result["messages"][-1] if result.get("messages") else None
        
        return {
            "answer": final_message.content if final_message and hasattr(final_message, 'content') else str(final_message),
            "agents_consulted": list(set(agents_used)),
            "full_conversation": result.get("messages", [])
        }


def demo_supervisor_system():
    """Demonstrate the supervisor multi-agent system"""
    
    print("🚀 Context Quarantine with Supervisor Pattern Demo")
    print("=" * 60)
    
    # Initialize supervisor system
    supervisor = PMSupervisorAgent()
    
    # Test queries requiring different agents
    test_queries = [
        "What's our current sprint velocity and are we on track?",
        "How is user engagement trending this month?",
        "What's our LTV/CAC ratio and is it healthy?",
        "What are the top user complaints and feature requests?",
        "How do we compare to our main competitor in terms of features?",
        "Are there any performance issues affecting users?",
        "Give me a comprehensive overview of our product health including sprint progress, user metrics, and revenue"
    ]
    
    for query in test_queries:
        print(f"\n❓ Query: {query}")
        result = supervisor.query(query)
        print(f"\n📝 Answer: {result['answer']}")
        
        if result['agents_consulted']:
            print(f"\n👥 Agents Consulted: {', '.join(result['agents_consulted'])}")
        print("-" * 40)


if __name__ == "__main__":
    demo_supervisor_system()