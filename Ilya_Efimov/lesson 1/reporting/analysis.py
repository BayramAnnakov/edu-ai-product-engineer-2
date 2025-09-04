from __future__ import annotations

"""Generate qualitative analysis comparing extractive and abstractive summaries."""

from openai import OpenAI

from shared_utils.config import auto_env_settings as settings
from shared_utils.data_models import ExtractiveSummary, AbstractiveSummary, Metrics
from shared_utils.logging import get_logger
from shared_utils.prompt_templates import REPORT_SYSTEM_PROMPT, REPORT_USER_PROMPT

_LOGGER = get_logger(__name__)


class QualitativeAnalyzer:  # noqa: D101
    def __init__(self, model_name: str | None = None, timeout: int | None = None) -> None:
        timeout_val = timeout or settings.openai_timeout
        if settings.llm_provider == "openrouter":
            self.client = OpenAI(
                api_key=settings.openrouter_api_key,
                base_url=settings.openrouter_base_url,
                timeout=timeout_val,
            )
            self.model_name = model_name or settings.openrouter_model
        else:
            self.client = OpenAI(api_key=settings.openai_api_key, timeout=timeout_val)
            self.model_name = model_name or settings.openai_model

    def __call__(  # noqa: D401
        self,
        extractive: ExtractiveSummary,
        abstractive: AbstractiveSummary,
        metrics: Metrics,
    ) -> str:
        user_content = (
            REPORT_USER_PROMPT.replace("{{extractive}}", "\n".join(extractive.sentences))
            .replace("{{abstractive}}", abstractive.summary)
            .replace("{{rouge_1}}", f"{metrics.rouge_1:.3f}")
            .replace("{{rouge_l}}", f"{metrics.rouge_l:.3f}")
            .replace("{{bleu}}", f"{metrics.bleu:.3f}")
            .replace("{{semantic_similarity}}", f"{metrics.semantic_similarity:.3f}")
        )
        _LOGGER.debug("Generating qualitative analysis via LLM")
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": REPORT_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
            max_tokens=512,
        )
        return response.choices[0].message.content.strip()
