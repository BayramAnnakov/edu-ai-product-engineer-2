"""
Dynamic Tool Loadout for Product Management using LangGraph.

Implements semantic tool selection following the LangGraph pattern:
- Tool indexing with embeddings in InMemoryStore
- Semantic similarity search for tool selection
- Dynamic tool binding based on query context
- LangGraph workflow with tool loadout state
- Focused context to avoid tool confusion

Based on: https://github.com/langchain-ai/how_to_fix_your_context/notebooks/02-tool-loadout.ipynb
"""

import os
import uuid
import math
from typing import List, Dict, Any, Optional, Literal
from dataclasses import dataclass

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.messages import SystemMessage, ToolMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.store.memory import InMemoryStore

from dotenv import load_dotenv
load_dotenv()


class ToolLoadoutState(MessagesState):
    """State that extends MessagesState to include dynamically selected tools"""
    tools_by_name: Dict[str, Any] = {}


@tool
def sprint_velocity_calculator(story_points: int, sprint_days: int = 10) -> Dict[str, float]:
    """Calculate sprint velocity and capacity metrics"""
    daily_velocity = story_points / sprint_days
    weekly_velocity = daily_velocity * 5
    return {
        "total_points": story_points,
        "daily_velocity": round(daily_velocity, 2),
        "weekly_velocity": round(weekly_velocity, 2),
        "ideal_capacity": story_points * 0.8  # 80% for sustainable pace
    }


@tool  
def story_point_estimator(complexity: str, effort: str, risk: str) -> int:
    """Estimate story points based on complexity, effort, and risk"""
    scores = {
        "low": 1,
        "medium": 3,
        "high": 5,
        "very_high": 8
    }
    
    complexity_score = scores.get(complexity.lower(), 3)
    effort_score = scores.get(effort.lower(), 3)
    risk_score = scores.get(risk.lower(), 3)
    
    # Fibonacci-like scoring
    total = complexity_score + effort_score + risk_score
    if total <= 3:
        return 1
    elif total <= 6:
        return 3
    elif total <= 9:
        return 5
    elif total <= 12:
        return 8
    else:
        return 13


@tool
def burndown_tracker(total_points: int, completed_points: int, days_elapsed: int, total_days: int) -> Dict[str, Any]:
    """Track sprint burndown progress and forecasts"""
    remaining_points = total_points - completed_points
    remaining_days = total_days - days_elapsed
    
    if days_elapsed > 0:
        actual_velocity = completed_points / days_elapsed
        projected_completion = completed_points + (actual_velocity * remaining_days)
    else:
        actual_velocity = 0
        projected_completion = 0
    
    ideal_velocity = total_points / total_days
    ideal_progress = ideal_velocity * days_elapsed
    
    return {
        "completed": completed_points,
        "remaining": remaining_points,
        "progress_percentage": round((completed_points / total_points) * 100, 1),
        "actual_velocity": round(actual_velocity, 2),
        "ideal_velocity": round(ideal_velocity, 2),
        "on_track": completed_points >= ideal_progress,
        "projected_completion": round(projected_completion, 1),
        "forecast_vs_target": round(projected_completion - total_points, 1)
    }


@tool
def nps_calculator(promoters: int, passives: int, detractors: int) -> Dict[str, Any]:
    """Calculate Net Promoter Score and analyze customer sentiment"""
    total = promoters + passives + detractors
    if total == 0:
        return {"error": "No responses provided"}
    
    nps = ((promoters - detractors) / total) * 100
    
    return {
        "nps_score": round(nps, 1),
        "promoter_percentage": round((promoters / total) * 100, 1),
        "passive_percentage": round((passives / total) * 100, 1),
        "detractor_percentage": round((detractors / total) * 100, 1),
        "total_responses": total,
        "category": "Excellent" if nps > 70 else "Good" if nps > 30 else "Needs Improvement" if nps > 0 else "Poor"
    }


@tool
def churn_rate_analyzer(customers_lost: int, customers_start: int, time_period: str = "monthly") -> Dict[str, Any]:
    """Analyze customer churn rate and retention metrics"""
    if customers_start == 0:
        return {"error": "Starting customer count cannot be zero"}
    
    churn_rate = (customers_lost / customers_start) * 100
    retention_rate = 100 - churn_rate
    
    # Annual projection
    if time_period == "monthly":
        annual_churn = 1 - pow(1 - churn_rate/100, 12)
        annual_churn_rate = annual_churn * 100
    else:
        annual_churn_rate = churn_rate
    
    return {
        "churn_rate": round(churn_rate, 2),
        "retention_rate": round(retention_rate, 2),
        "customers_lost": customers_lost,
        "customers_retained": customers_start - customers_lost,
        "annual_churn_projection": round(annual_churn_rate, 2),
        "period": time_period
    }


@tool
def ltv_calculator(arpu: float, churn_rate: float, margin: float = 0.7) -> Dict[str, float]:
    """Calculate customer Lifetime Value (LTV)"""
    if churn_rate == 0:
        return {"error": "Churn rate cannot be zero"}
    
    # LTV = ARPU * Gross Margin % / Churn Rate
    ltv = (arpu * margin) / (churn_rate / 100)
    
    return {
        "ltv": round(ltv, 2),
        "arpu": arpu,
        "margin_percentage": margin * 100,
        "churn_rate": churn_rate,
        "months_to_recover_cac": round(1 / (churn_rate / 100), 1)
    }


@tool
def cac_payback_calculator(cac: float, mrr_per_customer: float, margin: float = 0.7) -> Dict[str, Any]:
    """Calculate Customer Acquisition Cost payback period"""
    if mrr_per_customer * margin == 0:
        return {"error": "Monthly recurring revenue cannot be zero"}
    
    payback_months = cac / (mrr_per_customer * margin)
    
    return {
        "cac": cac,
        "payback_months": round(payback_months, 1),
        "payback_days": round(payback_months * 30, 0),
        "mrr_per_customer": mrr_per_customer,
        "gross_margin": margin * 100,
        "healthy_payback": payback_months <= 12
    }


@tool
def feature_prioritizer(impact: int, confidence: float, ease: int, reach: int) -> Dict[str, Any]:
    """Calculate RICE score for feature prioritization"""
    # RICE = (Reach * Impact * Confidence) / Effort
    rice_score = (reach * impact * confidence) / ease
    
    return {
        "rice_score": round(rice_score, 1),
        "reach": reach,
        "impact": impact,
        "confidence": confidence,
        "ease": ease,
        "priority": "High" if rice_score > 100 else "Medium" if rice_score > 50 else "Low"
    }


@tool
def ab_test_calculator(control_conversions: int, control_visitors: int, 
                      treatment_conversions: int, treatment_visitors: int) -> Dict[str, Any]:
    """Calculate A/B test results and statistical significance"""
    import math
    
    # Calculate conversion rates
    control_rate = control_conversions / control_visitors if control_visitors > 0 else 0
    treatment_rate = treatment_conversions / treatment_visitors if treatment_visitors > 0 else 0
    
    # Calculate lift
    if control_rate > 0:
        lift = ((treatment_rate - control_rate) / control_rate) * 100
    else:
        lift = 0
    
    # Simple significance test (z-test for proportions)
    pooled_rate = (control_conversions + treatment_conversions) / (control_visitors + treatment_visitors)
    se = math.sqrt(pooled_rate * (1 - pooled_rate) * (1/control_visitors + 1/treatment_visitors))
    
    if se > 0:
        z_score = (treatment_rate - control_rate) / se
        # Simplified p-value approximation
        p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(z_score) / math.sqrt(2))))
        significant = p_value < 0.05
    else:
        z_score = 0
        p_value = 1
        significant = False
    
    return {
        "control_rate": round(control_rate * 100, 2),
        "treatment_rate": round(treatment_rate * 100, 2),
        "lift_percentage": round(lift, 2),
        "p_value": round(p_value, 4),
        "statistically_significant": significant,
        "confidence_level": round((1 - p_value) * 100, 1),
        "winner": "Treatment" if significant and lift > 0 else "Control" if significant else "No clear winner"
    }


@tool
def cohort_retention_analyzer(month_0: int, month_1: int, month_2: int, month_3: int) -> Dict[str, Any]:
    """Analyze cohort retention over time"""
    cohort_data = [month_0, month_1, month_2, month_3]
    
    retention_rates = []
    for i, users in enumerate(cohort_data):
        if i == 0:
            retention_rates.append(100.0)
        else:
            rate = (users / month_0) * 100 if month_0 > 0 else 0
            retention_rates.append(round(rate, 1))
    
    # Calculate month-over-month retention
    mom_retention = []
    for i in range(1, len(cohort_data)):
        if cohort_data[i-1] > 0:
            mom = (cohort_data[i] / cohort_data[i-1]) * 100
            mom_retention.append(round(mom, 1))
    
    return {
        "retention_curve": retention_rates,
        "month_over_month": mom_retention,
        "month_3_retention": retention_rates[3] if len(retention_rates) > 3 else 0,
        "total_churn": round(100 - retention_rates[-1], 1),
        "average_mom_retention": round(sum(mom_retention) / len(mom_retention), 1) if mom_retention else 0
    }


class PMToolLoadoutAgent:
    """
    Product Management agent with dynamic tool selection using semantic search.
    """
    
    def __init__(self, max_tools: int = 5):
        """Initialize agent with tool store and LLM"""
        
        # Initialize LLM
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        
        # Create in-memory store for tools
        self.store = InMemoryStore(
            index={
                "embed": self.embeddings,
                "dims": 1536,  # OpenAI embedding dimensions
                "fields": ["description"],
            }
        )
        
        # All available tools
        self.all_tools = [
            sprint_velocity_calculator,
            story_point_estimator,
            burndown_tracker,
            nps_calculator,
            churn_rate_analyzer,
            ltv_calculator,
            cac_payback_calculator,
            feature_prioritizer,
            ab_test_calculator,
            cohort_retention_analyzer
        ]
        
        # Create tool registry
        self.tool_registry = {
            str(uuid.uuid4()): tool
            for tool in self.all_tools
        }
        
        # Index tools in store
        for tool_id, tool_func in self.tool_registry.items():
            self.store.put(
                ("tools",),  # Namespace
                tool_id,
                {
                    "description": f"{tool_func.name}: {tool_func.description}",
                    "name": tool_func.name
                }
            )
        
        self.max_tools = max_tools
        
        # System prompt
        self.system_prompt = """You are a Product Management assistant with access to specialized calculation tools.

You can search for and use relevant tools to solve PM problems including:
- Sprint planning and velocity calculations
- Metrics analysis (NPS, churn, LTV, CAC)
- Feature prioritization (RICE scoring)
- A/B testing and cohort analysis

When you need to perform calculations:
1. Identify the type of calculation needed
2. Use the appropriate tools from your available set
3. Provide clear, actionable insights based on the results

Always use tools for calculations rather than computing manually."""
        
        # Build workflow
        self.agent = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow with dynamic tool selection"""
        
        # Store reference for closure
        store = self.store
        max_tools = self.max_tools
        tool_registry = self.tool_registry
        llm = self.llm
        system_prompt = self.system_prompt
        
        def llm_call(state: ToolLoadoutState) -> dict:
            """LLM call with dynamically selected tools"""
            
            # Extract query from last message
            messages = state["messages"]
            if messages and isinstance(messages[-1], HumanMessage):
                query = messages[-1].content
            else:
                query = "product management calculation"
            
            # Search for relevant tools
            search_results = store.search(("tools",), query=query, limit=max_tools)
            
            # Build focused tool set
            relevant_tools = []
            tools_by_name = {}
            
            for result in search_results:
                tool_id = result.key
                if tool_id in tool_registry:
                    tool_func = tool_registry[tool_id]
                    relevant_tools.append(tool_func)
                    tools_by_name[tool_func.name] = tool_func
            
            # Bind relevant tools to LLM
            if relevant_tools:
                llm_with_tools = llm.bind_tools(relevant_tools)
            else:
                llm_with_tools = llm
            
            # Generate response
            response = llm_with_tools.invoke(
                [SystemMessage(content=system_prompt)] + state["messages"]
            )
            
            return {
                "messages": [response],
                "tools_by_name": tools_by_name
            }
        
        def tool_node(state: ToolLoadoutState) -> dict:
            """Execute tool calls using dynamically selected tools"""
            results = []
            for tool_call in state["messages"][-1].tool_calls:
                tool = state["tools_by_name"][tool_call["name"]]
                observation = tool.invoke(tool_call["args"])
                results.append(
                    ToolMessage(
                        content=str(observation),
                        tool_call_id=tool_call["id"]
                    )
                )
            return {"messages": results}
        
        def should_continue(state: ToolLoadoutState) -> Literal["tool_node", "__end__"]:
            """Determine if we should continue with tool calls"""
            last_message = state["messages"][-1]
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                return "tool_node"
            return END
        
        # Build workflow
        workflow = StateGraph(ToolLoadoutState)
        
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
        
        # Compile with store
        return workflow.compile(store=self.store)
    
    def query(self, question: str) -> Dict[str, Any]:
        """Query the agent with dynamic tool selection"""
        
        result = self.agent.invoke({
            "messages": [HumanMessage(content=question)]
        })
        
        # Extract response
        final_message = result["messages"][-1]
        
        # Find which tools were used
        tools_used = []
        for msg in result["messages"]:
            if hasattr(msg, 'tool_calls'):
                for tool_call in msg.tool_calls:
                    tools_used.append(tool_call["name"])
        
        return {
            "answer": final_message.content if hasattr(final_message, 'content') else str(final_message),
            "tools_used": list(set(tools_used)),
            "full_conversation": result["messages"]
        }


def demo_tool_loadout():
    """Demonstrate dynamic tool selection for PM tasks"""
    
    print("🚀 Dynamic Tool Loadout Demo for Product Management")
    print("=" * 60)
    
    # Initialize agent
    agent = PMToolLoadoutAgent(max_tools=3)
    
    # Test queries that require different tools
    test_queries = [
        "Calculate the sprint velocity if we completed 45 story points in a 10-day sprint",
        "What's the NPS score if we have 150 promoters, 50 passives, and 30 detractors?",
        "Calculate the LTV if ARPU is $50, churn rate is 5%, and margin is 70%",
        "Analyze an A/B test: control had 1000 visitors with 50 conversions, treatment had 1000 visitors with 65 conversions",
        "What's the RICE score for a feature with reach=5000, impact=3, confidence=0.8, ease=5?",
        "Calculate customer churn if we lost 25 customers out of 500 at the start of the month"
    ]
    
    for query in test_queries:
        print(f"\n❓ Query: {query}")
        result = agent.query(query)
        print(f"\n📝 Answer: {result['answer']}")
        print(f"🔧 Tools Used: {', '.join(result['tools_used']) if result['tools_used'] else 'None'}")
        print("-" * 40)


if __name__ == "__main__":
    demo_tool_loadout()