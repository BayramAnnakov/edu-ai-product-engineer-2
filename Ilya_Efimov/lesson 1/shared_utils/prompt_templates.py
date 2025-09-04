from __future__ import annotations

"""Prompt templates for the LLM calls used in the summarization pipeline."""

# ---------------------------------------------------------------------------
# Extractive summarizer prompt – not usually needed since extraction is
# deterministic, but kept here for consistency / future hybrid approaches.
# ---------------------------------------------------------------------------
EXTRACTIVE_SYSTEM_PROMPT = (
    "You are an expert extractive summarization agent. "
    "Return the {{max_sentences}} most important sentences from the provided text. "
    "Preserve original wording as much as possible. Output as a JSON list of sentences."
)

# ---------------------------------------------------------------------------
# Abstractive summarizer prompt
# ---------------------------------------------------------------------------
ABSTRACTIVE_SYSTEM_PROMPT = (
    "You are an expert technical writer. Write a concise, coherent summary "
    "(≤ 150 words) of the following content for a knowledgeable audience."
)

ABSTRACTIVE_USER_PROMPT = """\
TEXT:
{{text}}
"""

# ---------------------------------------------------------------------------
# Report generation prompt (narrative analysis)
# ---------------------------------------------------------------------------
REPORT_SYSTEM_PROMPT = (
    "You are a senior analyst comparing two summaries (extractive vs. abstractive). "
    "Provide strengths, weaknesses, and actionable recommendations."
)

REPORT_USER_PROMPT = """\
## Extractive Summary\n
{{extractive}}\n
## Abstractive Summary\n
{{abstractive}}\n
## Metrics\n
ROUGE-1: {{rouge_1}}\nROUGE-L: {{rouge_l}}\nBLEU: {{bleu}}\nSemantic Similarity: {{semantic_similarity}}\n"""
