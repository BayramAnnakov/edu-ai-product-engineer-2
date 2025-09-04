from __future__ import annotations

"""Abstractive summarizer that calls OpenAI's GPT-4 model."""

from openai import OpenAI, BadRequestError  # type: ignore

from shared_utils.config import auto_env_settings as settings
from shared_utils.data_models import AbstractiveSummary, TextInput
from shared_utils.logging import get_logger
from shared_utils.prompt_templates import ABSTRACTIVE_SYSTEM_PROMPT, ABSTRACTIVE_USER_PROMPT

_LOGGER = get_logger(__name__)


class AbstractiveSummarizer:  # noqa: D101
    def __init__(self, model_name: str | None = None, timeout: int | None = None):
        # Determine provider and initialize client
        self.timeout = timeout or settings.openai_timeout
        if settings.llm_provider == "openrouter":
            self.model_name = model_name or settings.openrouter_model
            self.client = OpenAI(
                api_key=settings.openrouter_api_key,
                base_url=settings.openrouter_base_url,
                timeout=self.timeout,
            )
        else:
            self.model_name = model_name or settings.openai_model
            self.client = OpenAI(api_key=settings.openai_api_key, timeout=self.timeout)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def __call__(self, text_input: TextInput) -> AbstractiveSummary:  # noqa: D401
        content = ABSTRACTIVE_USER_PROMPT.replace("{{text}}", text_input.text)
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": ABSTRACTIVE_SYSTEM_PROMPT},
                    {"role": "user", "content": content},
                ],
                temperature=0.3,
                max_tokens=256,
            )
        except BadRequestError as exc:  # pragma: no cover
            _LOGGER.error("OpenAI request failed: %s", exc)
            raise
        summary_text = response.choices[0].message.content.strip()
        return AbstractiveSummary(summary=summary_text)
