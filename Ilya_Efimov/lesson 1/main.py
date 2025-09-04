from __future__ import annotations

"""Entry point: Windsurf Summarization Agent Orchestrator."""

import argparse
from pathlib import Path

from shared_utils.config import auto_env_settings as settings
from shared_utils.logging import get_logger
from shared_utils.data_models import (
    TextInput,
    ComparisonReport,
)

from agents.extractive import ExtractiveSummarizer
from agents.abstractive import AbstractiveSummarizer
from reporting.metrics import MetricsComputer
from reporting.analysis import QualitativeAnalyzer

# Initialize global logging immediately
get_logger().info("Windsurf Summarization Agent starting …")
_LOGGER = get_logger(__name__)


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run summarization pipeline.")
    parser.add_argument("input_file", type=Path, help="Path to text file to summarize")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("reporting/comparison_report.md"),
        help="Path to save comparison report (markdown)",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Pipeline orchestration
# ---------------------------------------------------------------------------

def run_pipeline(text: str, output_path: Path) -> ComparisonReport:  # noqa: D401
    text_input = TextInput(text=text)

    # --- Run agents in parallel (simple sequential fallback for now) ---
    _LOGGER.info("Running extractive summarizer …")
    extractive = ExtractiveSummarizer()(text_input)

    _LOGGER.info("Running abstractive summarizer …")
    abstractive = AbstractiveSummarizer()(text_input)

    # --- Metrics & qualitative analysis ---
    metrics = MetricsComputer()(extractive, abstractive)

    analyzer = QualitativeAnalyzer()
    qualitative = analyzer(extractive, abstractive, metrics)

    report = ComparisonReport(
        extractive=extractive,
        abstractive=abstractive,
        metrics=metrics,
        qualitative_analysis=qualitative,
    )

    # Persist report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_format_report_md(report))
    _LOGGER.info("Report saved to %s", output_path.resolve())

    return report


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------

def _format_report_md(report: ComparisonReport) -> str:  # noqa: D401
    return (
        "# Summarization Comparison Report\n\n"
        "## Extractive Summary\n\n"
        + "\n".join(f"- {s}" for s in report.extractive.sentences)
        + "\n\n## Abstractive Summary\n\n"
        + report.abstractive.summary
        + "\n\n## Metrics\n\n"
        + f"* ROUGE-1: {report.metrics.rouge_1:.3f}\n"
        + f"* ROUGE-L: {report.metrics.rouge_l:.3f}\n"
        + f"* BLEU: {report.metrics.bleu:.3f}\n"
        + f"* Semantic Similarity: {report.metrics.semantic_similarity:.3f}\n\n"
        + "## Qualitative Analysis\n\n"
        + report.qualitative_analysis
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:  # noqa: D401
    args = _parse_args()
    text = args.input_file.read_text()
    run_pipeline(text, args.output)


if __name__ == "__main__":  # pragma: no cover
    main()
