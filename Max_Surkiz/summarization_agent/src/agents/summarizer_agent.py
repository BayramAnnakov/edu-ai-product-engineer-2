from agents import Agent, Tool, Runner
from summarization_agent.src.utils.download import fetch_and_process
from summarization_agent.src.pipelines.extractive import extractive_summary
from summarization_agent.src.pipelines.abstractive import abstractive_summary
import os

# --- Tool 1: FetchArticleTool ---
class FetchArticleTool(Tool):
    name = "fetch_article"
    description = "Скачивает и возвращает текст статьи по URL."

    def run(self, url: str) -> str:
        return fetch_and_process(url)

# --- Tool 2: ExtractiveTool ---
class ExtractiveTool(Tool):
    name = "extractive_summary"
    description = "Строит экстрактивное резюме текста."

    def run(self, text: str, ratio: float = 0.2) -> str:
        return extractive_summary(text, ratio=ratio)

# --- Tool 3: AbstractiveTool ---
class AbstractiveTool(Tool):
    name = "abstractive_summary"
    description = "Строит абстрактивное резюме текста."

    def run(self, text: str) -> str:
        return abstractive_summary(text)

# --- Tool 4: CompareTool ---
class CompareTool(Tool):
    name = "compare_summaries"
    description = "Сравнивает два резюме и считает метрики ROUGE."

    def run(self, original: str, extractive: str, abstractive: str) -> dict:
        from summarization_agent.src.evaluators.rouge_eval import compute_rouge
        rouge_scores = compute_rouge(extractive, abstractive)
        return rouge_scores

# --- Агент ---
class SummarizerAgent(Agent):
    name = "SummarizerAgent"
    instructions = "Ты — агент для суммаризации научных статей. Используй инструменты строго по порядку: fetch_article → extractive_summary → abstractive_summary → compare_summaries."
    tools = [FetchArticleTool(), ExtractiveTool(), AbstractiveTool(), CompareTool()]

# --- Пример запуска ---
if __name__ == "__main__":
    url = "https://www.anthropic.com/engineering/built-multi-agent-research-system"
    agent = SummarizerAgent()
    result = Runner.run_sync(agent, url)
    print(result.final_output) 