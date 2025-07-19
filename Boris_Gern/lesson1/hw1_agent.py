import typer
from dotenv import load_dotenv

load_dotenv()

import asyncio
import time
import json
from typing import Optional, List, Tuple
from openai import OpenAI

# Import local tools
from tools.io import load_reviews, filter_version, calc_share
from tools.summarise import textrank_summary, chunk_texts, abstractive_summary_chunk, reduce_summaries
from tools.themes import theme_extract, extract_themes_by_keywords, calculate_theme_distribution_by_keywords
from tools.metrics import metric_rouge
from tools.html import build_html
from schema import ReportPayload

# --- Pricing Constants ---
# Prices for gpt-4.1-mini per 1M tokens
PRICE_INPUT_PER_1M = 0.15
PRICE_OUTPUT_PER_1M = 0.60

# --- Agent State ---
class AgentState:
    def __init__(self, csv_path):
        print("Loading and preparing data...")
        self.df_all = load_reviews(csv_path)
        if self.df_all is None:
            raise ValueError(f"Could not load reviews from {csv_path}")
        self.df_ver = None
        self.version = None
        self.reviews_text = None
        self.full_text = None
        self.extractive_sum = None
        self.abstractive_result = None
        self.themes = None # Top-level themes
        self.extractive_themes = None
        self.extractive_theme_distribution = None
        self.abstractive_theme_distribution = None
        # Abstractive themes are now part of abstractive_result
        self.share = None
        self.rouge_extractive = 0.0
        self.rouge_abstractive = 0.0
        self.total_cost_usd = 0.0 # To accumulate cost

state: Optional[AgentState] = None

# --- Tool Functions ---
def filter_and_prep_data(version: str):
    global state
    state.version = version
    state.df_ver = filter_version(state.df_all, version)
    if state.df_ver.empty:
        return f"Error: No reviews found for version '{version}'."
    state.reviews_text = state.df_ver['Review Text'].dropna().tolist()
    state.full_text = " ".join(state.reviews_text)
    return f"Successfully filtered for version {version}. Found {len(state.df_ver)} reviews."

def run_extractive_summary():
    global state
    if state.full_text is None: return "Error: Data not prepped."
    state.extractive_sum = textrank_summary(state.full_text)
    return "Extractive summary generated."

async def run_abstractive_summary():
    global state
    if state.reviews_text is None: return "Error: Data not prepped."

    chunks = chunk_texts(state.reviews_text)
    tasks = [abstractive_summary_chunk(chunk) for chunk in chunks]
    results = await asyncio.gather(*tasks)

    # 1. Process chunk results
    mini_summaries, praises, pains, requests = [], [], [], []
    distributions = []
    total_chunk_reviews = 0
    chunk_input_tokens, chunk_output_tokens = 0, 0

    for i, res in enumerate(results):
        content, input_tokens, output_tokens = res
        chunk_len = len(chunks[i])
        total_chunk_reviews += chunk_len

        mini_summaries.append(content.get("summary", ""))
        praises.append(content.get("praise", ""))
        pains.append(content.get("pain", ""))
        requests.append(content.get("request", ""))
        
        # Store distribution with chunk length for weighting
        dist = content.get("distribution", {})
        if dist:
            distributions.append((dist, chunk_len))

        chunk_input_tokens += input_tokens
        chunk_output_tokens += output_tokens

    input_cost = (chunk_input_tokens / 1_000_000) * PRICE_INPUT_PER_1M
    output_cost = (chunk_output_tokens / 1_000_000) * PRICE_OUTPUT_PER_1M
    state.total_cost_usd += (input_cost + output_cost)

    # 2. Reduce summaries and themes in parallel
    final_summary_task = reduce_summaries(mini_summaries)
    final_praise_task = reduce_summaries(praises, "Synthesize these praises into one final, fluent paragraph in Russian.")
    final_pain_task = reduce_summaries(pains, "Synthesize these pains into one final, fluent paragraph in Russian.")
    final_request_task = reduce_summaries(requests, "Synthesize these requests into one final, fluent paragraph in Russian.")

    final_results = await asyncio.gather(
        final_summary_task, final_praise_task, final_pain_task, final_request_task
    )

    final_summary, final_praise, final_pain, final_request = [res[0] for res in final_results]
    reduce_input_tokens = sum(res[1] for res in final_results)
    reduce_output_tokens = sum(res[2] for res in final_results)

    reduce_input_cost = (reduce_input_tokens / 1_000_000) * PRICE_INPUT_PER_1M
    reduce_output_cost = (reduce_output_tokens / 1_000_000) * PRICE_OUTPUT_PER_1M
    state.total_cost_usd += (reduce_input_cost + reduce_output_cost)

    # 3. Calculate weighted average of distributions
    if distributions and total_chunk_reviews > 0:
        weighted_sums = {"Praise": 0, "Pain": 0, "Request": 0}
        for dist, weight in distributions:
            weighted_sums["Praise"] += dist.get("praise_percentage", 0) * weight
            weighted_sums["Pain"] += dist.get("pain_percentage", 0) * weight
            weighted_sums["Request"] += dist.get("request_percentage", 0) * weight
        
        state.abstractive_theme_distribution = {
            theme: total / total_chunk_reviews for theme, total in weighted_sums.items()
        }

    # 4. Store results in state
    state.abstractive_result = {
        "final_summary": final_summary,
        "mini_summaries": mini_summaries,
        "themes": [
            {"name": "Praise", "quote": final_praise},
            {"name": "Pain", "quote": final_pain},
            {"name": "Request", "quote": final_request},
        ]
    }
    return "Abstractive summary and themes generated."

def run_extractive_theme_extraction():
    """Extracts themes from the full text using keyword matching for the Extractive approach."""
    global state
    if state.full_text is None: return "Error: Data not prepped."
    state.extractive_themes = extract_themes_by_keywords(state.full_text)
    return f"Extracted {len(state.extractive_themes)} themes for Extractive part."

def run_extractive_theme_distribution():
    """Calculates theme distribution for the Extractive approach using keywords."""
    global state
    if state.full_text is None: return "Error: Data not prepped."
    state.extractive_theme_distribution = calculate_theme_distribution_by_keywords(state.full_text)
    return "Calculated Extractive theme distribution."

def run_share_calculation():
    global state
    if state.df_ver is None: return "Error: Data not filtered."
    state.share = calc_share(state.df_all, state.df_ver)
    return f"Calculated share: {state.share:.2%}"

def run_rouge_metric_calculation():
    global state
    if state.full_text is None or state.extractive_sum is None or state.abstractive_result is None:
        return "Error: Summaries not generated yet."
    state.rouge_extractive = metric_rouge(state.full_text, state.extractive_sum)
    state.rouge_abstractive = metric_rouge(state.full_text, state.abstractive_result["final_summary"])
    return f"Calculated ROUGE-L: extractive={state.rouge_extractive:.2f}, abstractive={state.rouge_abstractive:.2f}"

TOOL_MAPPING = {
    "filter_and_prep_data": filter_and_prep_data,
    "run_extractive_summary": run_extractive_summary,
    "run_abstractive_summary": run_abstractive_summary,
    "run_extractive_theme_extraction": run_extractive_theme_extraction,
    "run_extractive_theme_distribution": run_extractive_theme_distribution,
    "run_share_calculation": run_share_calculation,
    "run_rouge_metric_calculation": run_rouge_metric_calculation,
}

# --- Main Agent Logic ---
async def run_analysis(csv_path: str, version: Optional[str]):
    global state
    state = AgentState(csv_path)
    client = OpenAI()

    if not version:
        version = state.df_all['App Version Name'].value_counts().idxmax()
        print(f"No version specified. Using latest version: {version}")

    tools_schema = []
    for name, func in TOOL_MAPPING.items():
        if name == 'filter_and_prep_data':
            tools_schema.append({
                "type": "function",
                "function": {
                    "name": "filter_and_prep_data",
                    "description": "Filters reviews for a specific version and prepares the data for analysis.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "version": {
                                "type": "string",
                                "description": "The software version to filter reviews for."
                            }
                        },
                        "required": ["version"]
                    }
                }
            })
        else:
            tools_schema.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": func.__doc__ or "",
                    "parameters": {"type": "object", "properties": {}}
                }
            })

    assistant = client.beta.assistants.create(
        name="Review PM-Agent",
        instructions=(
            "You are a Review PM-Agent. Your goal is to analyze user reviews for a specific software version. "
            "First, call `filter_and_prep_data` with the version provided. "
            "Then, run the following analysis tools in parallel if possible: `run_share_calculation`, `run_extractive_summary`, `run_abstractive_summary`, `run_extractive_theme_extraction`, and `run_extractive_theme_distribution`. "
            "After the summaries are done, call `run_rouge_metric_calculation`. "
            "Once all tools have run, inform the user that the analysis is complete."
        ),
        model="gpt-4.1-mini",
        tools=tools_schema
    )

    thread = client.beta.threads.create()
    client.beta.threads.messages.create(thread_id=thread.id, role="user", content=f"Please analyze version '{version}'.")
    run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant.id)
    start_time = time.time()

    while run.status in ['queued', 'in_progress', 'requires_action']:
        if run.status == 'requires_action':
            tool_outputs = []
            for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                func_name = tool_call.function.name
                try:
                    func_args = json.loads(tool_call.function.arguments)
                    print(f"Assistant wants to call: {func_name}({func_args}) ...")
                    func = TOOL_MAPPING.get(func_name)
                    if not func:
                        raise ValueError(f"Tool '{func_name}' not found.")
                    
                    output = await func(**func_args) if asyncio.iscoroutinefunction(func) else func(**func_args)
                    tool_outputs.append({"tool_call_id": tool_call.id, "output": str(output)})

                except Exception as e:
                    print(f"Error calling tool {func_name}: {e}")
                    tool_outputs.append({"tool_call_id": tool_call.id, "output": f"Error: {e}"})
            
            run = client.beta.threads.runs.submit_tool_outputs(thread_id=thread.id, run_id=run.id, tool_outputs=tool_outputs)
        
        await asyncio.sleep(1)
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        
        if run.usage:
            input_cost = (run.usage.prompt_tokens / 1_000_000) * PRICE_INPUT_PER_1M
            output_cost = (run.usage.completion_tokens / 1_000_000) * PRICE_OUTPUT_PER_1M
            state.total_cost_usd += (input_cost + output_cost)


    if run.status == 'completed':
        print("\nAnalysis complete. Generating report...")
        latency_ms = (time.time() - start_time) * 1000

        payload = ReportPayload(
            version=state.version,
            share_percentage=state.share * 100,
            extractive_summary=state.extractive_sum,
            abstractive_summary=state.abstractive_result["final_summary"],
            extractive_themes=state.extractive_themes,
            abstractive_themes=state.abstractive_result["themes"],
            extractive_theme_distribution=state.extractive_theme_distribution,
            abstractive_theme_distribution=state.abstractive_theme_distribution,
            rouge_l_extractive=state.rouge_extractive,
            rouge_l_abstractive=state.rouge_abstractive,
            latency_ms=latency_ms,
            cost_usd=state.total_cost_usd,
            mini_summaries=state.abstractive_result["mini_summaries"]
        )
        result_message = build_html(payload)
        print(result_message)
    else:
        print(f"\nRun failed with status: {run.status}")
        if run.last_error:
            print(f"Error: {run.last_error.message}")

# --- CLI Entrypoint ---
def main(csv: str = typer.Option(..., "--csv", help="Path to the reviews CSV file."),
         version: Optional[str] = typer.Option(None, "--version", help="Target version to analyze.")):
    try:
        asyncio.run(run_analysis(csv, version))
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        print("Agent stopped due to a critical error.")

if __name__ == "__main__":
    typer.run(main)
