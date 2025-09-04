"""Batch CSV summarization pipeline.

Reads a CSV file containing free-form text reviews, generates both extractive
and abstractive summaries for each record, computes quantitative metrics, and
saves the side-by-side comparison to a new CSV.

Example
-------
$ python -m pipelines.csv_pipeline data/Reviews.csv review_text \
        --output outputs/reviews_summaries.csv --max-rows 1000

All configurable arguments can also be supplied via the CLI (see --help).
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Dict

import pandas as pd
from tqdm import tqdm

from shared_utils.data_models import TextInput
from shared_utils.logging import get_logger
from agents.extractive import ExtractiveSummarizer
from agents.abstractive import AbstractiveSummarizer
from reporting.metrics import MetricsComputer

_LOGGER = get_logger(__name__)


# ---------------------------------------------------------------------------
# Pipeline core
# ---------------------------------------------------------------------------

def summarize_rows(texts: List[str]) -> List[Dict[str, str | float]]:  # noqa: D401
    """Run both summarizers + metrics on an iterable of texts."""
    extractor = ExtractiveSummarizer()
    abstracter = AbstractiveSummarizer()
    metrics_comp = MetricsComputer()

    results: List[Dict[str, str | float]] = []
    for text in tqdm(texts, desc="Summarizing"):
        if not isinstance(text, str) or not text.strip():
            # Skip empty / non-string records
            continue
        try:
            text_input = TextInput(text=text)
        except ValueError:  # empty after stripping or other validation issue
            continue

        ext_summary = extractor(text_input)
        abs_summary = abstracter(text_input)
        metrics = metrics_comp(ext_summary, abs_summary)

        results.append(
            {
                "original_text": text,
                "extractive_summary": " ".join(ext_summary.sentences),
                "abstractive_summary": abs_summary.summary,
                "rouge_1": metrics.rouge_1,
                "rouge_l": metrics.rouge_l,
                "bleu": metrics.bleu,
                "semantic_similarity": metrics.semantic_similarity,
            }
        )
    return results


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch summarization for CSV files.")
    parser.add_argument("csv_path", type=Path, help="Input CSV file path")
    parser.add_argument(
        "column", type=str, help="Name of the column containing free-form text"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("outputs/csv_summaries.csv"),
        help="Destination CSV with summaries & metrics",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=None,
        help="Optional cap on number of rows to process (for quick tests)",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main() -> None:  # noqa: D401
    args = _parse_args()

    if not args.csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {args.csv_path}")

    _LOGGER.info("Reading CSV: %s", args.csv_path.resolve())
    df = pd.read_csv(args.csv_path)
    if args.column not in df.columns:
        raise ValueError(
            f"Column '{args.column}' not found in CSV. Available: {list(df.columns)}"
        )

    if args.max_rows:
        df = df.head(args.max_rows)
        _LOGGER.info("Processing first %d rows", len(df))
    else:
        _LOGGER.info("Processing %d rows", len(df))

    results = summarize_rows(df[args.column].tolist())
    if not results:
        _LOGGER.warning("No valid rows processed – nothing to write.")
        return

    out_df = pd.DataFrame(results)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Save CSV (machine-readable)
    out_df.to_csv(args.output, index=False)
    _LOGGER.info("Written output to %s", args.output.resolve())

    # ------------------------------------------------------------------
    # Optional: human-friendly Markdown file alongside the CSV
    # ------------------------------------------------------------------
    md_path = args.output.with_suffix(".md")
    with md_path.open("w", encoding="utf-8") as md_file:
        for i, row in out_df.iterrows():
            md_file.write(f"## Record {i+1}\n\n")
            md_file.write("**Original Text**\n\n" + row["original_text"] + "\n\n")
            md_file.write("**Extractive Summary**\n\n" + row["extractive_summary"] + "\n\n")
            md_file.write("**Abstractive Summary**\n\n" + row["abstractive_summary"] + "\n\n")
            md_file.write("**Metrics**\n\n")
            md_file.write(
                f"ROUGE-1: {row['rouge_1']:.3f} | ROUGE-L: {row['rouge_l']:.3f} | "
                f"BLEU: {row['bleu']:.3f} | Semantic similarity: {row['semantic_similarity']:.3f}\n\n"
            )
            md_file.write("---\n\n")
    _LOGGER.info("Written Markdown report to %s", md_path.resolve())


if __name__ == "__main__":  # pragma: no cover
    main()
