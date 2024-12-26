"""Unit tests for the LLM client"""
from unittest.mock import MagicMock, patch

import pytest

import gdoc_summaries.libs.llm as llm


class TestRetryWithBackoff:
    def test_successful_execution(self):
        mock_function = MagicMock()
        mock_function.return_value = "success"
        
        decorated = llm.retry_with_backoff(retries=2, backoff_in_seconds=[1, 2])(mock_function)
        result = decorated()
        
        assert result == "success"
        mock_function.assert_called_once()

    def test_retry_on_failure(self):
        mock_function = MagicMock()
        mock_function.side_effect = [ValueError("Error"), ValueError("Error"), "success"]
        
        decorated = llm.retry_with_backoff(retries=2, backoff_in_seconds=[0.1, 0.1])(mock_function)
        result = decorated()
        
        assert result == "success"
        assert mock_function.call_count == 3

    def test_context_length_error_no_retry(self):
        mock_function = MagicMock()
        mock_function.side_effect = ValueError("context_length_exceeded error")
        
        decorated = llm.retry_with_backoff(retries=2, backoff_in_seconds=[0.1, 0.1])(mock_function)
        
        with pytest.raises(ValueError, match="context_length_exceeded error"):
            decorated()
        
        mock_function.assert_called_once()

    def test_max_retries_exceeded(self):
        mock_function = MagicMock()
        mock_function.side_effect = ValueError("Error")
        
        decorated = llm.retry_with_backoff(retries=2, backoff_in_seconds=[0.1, 0.1])(mock_function)
        
        with pytest.raises(ValueError, match="Error"):
            decorated()
        
        assert mock_function.call_count == 3


# TODO: Add tests for the LLM client
