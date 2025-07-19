import asyncio
import json
from typing import List, Tuple, Dict, Any
from openai import AsyncOpenAI
from summa.summarizer import summarize as textrank

client = AsyncOpenAI()
MODEL = "gpt-4.1-mini"

def textrank_summary(text: str, max_chars: int = 1200) -> str:
    """Generates an extractive summary using TextRank with a character limit."""
    if not text or len(text) < max_chars:
        return text

    # Generate a summary using a ratio, then truncate. 0.2 is a heuristic.
    summary = textrank(text, ratio=0.2) or text

    if len(summary) > max_chars:
        # Find the last sentence end before the limit to avoid cutting mid-sentence
        end_pos = summary.rfind('.', 0, max_chars)
        if end_pos != -1:
            summary = summary[:end_pos + 1]
        else:
            # If no sentence end is found, just truncate hard
            summary = summary[:max_chars].rsplit(' ', 1)[0] + "..."

    return summary

def chunk_texts(texts: List[str], chunk_size: int = 10) -> List[List[str]]:
    return [texts[i:i + chunk_size] for i in range(0, len(texts), chunk_size)]

async def abstractive_summary_chunk(chunk: List[str]) -> Tuple[Dict[str, Any], int, int]:
    prompt_text = "\n\n---\n\n".join(chunk)

    system_prompt = """
    Analyze user reviews in Russian. Provide a concise summary and extract one representative quote for each category: Praise, Pain, and Request.
    Format your response as a single JSON object with five keys: "summary", "praise", "pain", "request", "distribution".
    The response must be a valid JSON.
    Example:
    {
      "summary": "<one-paragraph summary of the reviews in Russian>",
      "praise": "<a single, fluent, representative quote for praise in Russian>",
      "pain": "<a single, fluent, representative quote for pain in Russian>",
      "request": "<a single, fluent, representative quote for requests in Russian>",
      "distribution": {
        "praise_percentage": <int, 0-100>,
        "pain_percentage": <int, 0-100>,
        "request_percentage": <int, 0-100>
      }
    }
    """

    response = await client.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt_text}
        ],
        max_tokens=400,
        temperature=0.5,
    )

    try:
        content = json.loads(response.choices[0].message.content)
    except (json.JSONDecodeError, KeyError):
        content = {"summary": "", "praise": "", "pain": "", "request": ""}

    usage = response.usage
    return (content, usage.prompt_tokens, usage.completion_tokens)

async def reduce_summaries(items: List[str], system_prompt: str = None) -> Tuple[str, int, int]:
    if not items:
        return "", 0, 0

    # Default prompt for backward compatibility
    if system_prompt is None:
        system_prompt = "Synthesize these mini-summaries into one final, fluent summary in Russian (max 200 words)."

    combined_text = "\n\n---\n\n".join(filter(None, items)) # Filter out empty strings
    if not combined_text:
        return "", 0, 0

    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": combined_text}
        ],
        max_tokens=400,
        temperature=0.5,
    )
    final_summary = response.choices[0].message.content
    usage = response.usage
    return (final_summary.strip() if final_summary else "", usage.prompt_tokens, usage.completion_tokens)