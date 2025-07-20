import pytest
from unittest.mock import patch
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from summarization_agent.src.pipelines.extractive import extractive_summary
from summarization_agent.src.pipelines.abstractive import abstractive_summary

def test_agent_pipeline_smoke():
    text = "Test article for summarization."
    with patch('summarization_agent.src.pipelines.abstractive.abstractive_summary', return_value="Abstractive summary."):
        extractive = extractive_summary(text, ratio=0.5)
        abstractive = abstractive_summary(text)
        assert isinstance(extractive, str)
        assert isinstance(abstractive, str) 