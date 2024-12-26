"""Integration tests for the summary processor"""
from unittest.mock import MagicMock, patch

import pytest

import gdoc_summaries.libs.constants as constants
import gdoc_summaries.libs.summary_processor as summary_processor


@pytest.fixture
def mock_document_info():
    return constants.DocumentInfo(
        document_id="test_doc_123",
        date_published="2024-03-15"
    )

@pytest.fixture
def mock_summary():
    return constants.Summary(
        document_id="test_doc_123",
        title="Test Document",
        content="<p>Test summary content</p>",
        date_published="2024-03-15",
        summary_type=constants.SummaryType.TDD
    )

@pytest.fixture
def mock_google_doc():
    return {
        "title": "Test Document",
        "body": {
            "content": [
                {
                    "paragraph": {
                        "elements": [
                            {
                                "textRun": {
                                    "content": "Test document content\n"
                                }
                            }
                        ]
                    }
                }
            ]
        }
    }


class TestProcessSummaries:
    @patch('gdoc_summaries.libs.summary_processor.db')
    @patch('gdoc_summaries.libs.summary_processor.gdoc_client')
    @patch('gdoc_summaries.libs.summary_processor.constants')
    @patch('gdoc_summaries.libs.summary_processor.discovery')
    @patch('gdoc_summaries.libs.summary_processor.llm')
    @patch('gdoc_summaries.libs.summary_processor.email_client')
    def test_process_new_summary(
        self, mock_email, mock_llm, mock_discovery, mock_constants, 
        mock_gdoc, mock_db, mock_document_info, mock_summary, mock_google_doc
    ):
        # Setup
        mock_db.get_summary_from_db.return_value = None
        mock_constants.get_doc_info.return_value = [mock_document_info]
        mock_constants.get_subscribers.return_value = ["test@example.com"]
        
        mock_service = MagicMock()
        mock_discovery.build.return_value = mock_service
        mock_gdoc.get_document_from_id.return_value = mock_google_doc
        mock_gdoc.extract_document_content.return_value = "Test document content"
        mock_llm.generate_llm_summary.return_value = "<p>Test summary content</p>"
        
        # Execute
        summary_processor.process_summaries(constants.SummaryType.TDD)
        
        # Verify
        mock_db.setup_database.assert_called_once()
        mock_gdoc.get_credentials.assert_called_once()
        mock_constants.get_doc_info.assert_called_once()
        mock_gdoc.get_document_from_id.assert_called_once()
        mock_llm.generate_llm_summary.assert_called_once()
        mock_db.save_summary_to_db.assert_called_once()
        mock_email.build_and_send_email.assert_called_once()
        mock_db.mark_summary_as_sent.assert_called_once()

    @patch('gdoc_summaries.libs.summary_processor.db')
    @patch('gdoc_summaries.libs.summary_processor.gdoc_client')
    @patch('gdoc_summaries.libs.summary_processor.constants')
    @patch('gdoc_summaries.libs.summary_processor.discovery')
    @patch('gdoc_summaries.libs.summary_processor.email_client')
    def test_process_existing_unsent_summary(
        self, mock_email, mock_discovery, mock_constants, 
        mock_gdoc, mock_db, mock_document_info, mock_summary
    ):
        # Setup
        mock_db.get_summary_from_db.return_value = mock_summary
        mock_db.get_summary_sent_status.return_value = 0
        mock_constants.get_doc_info.return_value = [mock_document_info]
        mock_constants.get_subscribers.return_value = ["test@example.com"]
        
        # Execute
        summary_processor.process_summaries(constants.SummaryType.TDD)
        
        # Verify
        mock_db.setup_database.assert_called_once()
        mock_gdoc.get_document_from_id.assert_not_called()  # Shouldn't process doc again
        mock_email.build_and_send_email.assert_called_once()
        mock_db.mark_summary_as_sent.assert_called_once()

    @patch('gdoc_summaries.libs.summary_processor.db')
    @patch('gdoc_summaries.libs.summary_processor.gdoc_client')
    @patch('gdoc_summaries.libs.summary_processor.constants')
    @patch('gdoc_summaries.libs.summary_processor.discovery')
    @patch('gdoc_summaries.libs.summary_processor.email_client')
    def test_skip_already_sent_summary(
        self, mock_email, mock_discovery, mock_constants, 
        mock_gdoc, mock_db, mock_document_info, mock_summary
    ):
        # Setup
        mock_db.get_summary_from_db.return_value = mock_summary
        mock_db.get_summary_sent_status.return_value = 1
        mock_constants.get_doc_info.return_value = [mock_document_info]
        
        # Execute
        summary_processor.process_summaries(constants.SummaryType.TDD)
        
        # Verify
        mock_db.setup_database.assert_called_once()
        mock_gdoc.get_document_from_id.assert_not_called()
        mock_email.build_and_send_email.assert_not_called()
        mock_db.mark_summary_as_sent.assert_not_called()

    @patch('gdoc_summaries.libs.summary_processor.db')
    @patch('gdoc_summaries.libs.summary_processor.gdoc_client')
    @patch('gdoc_summaries.libs.summary_processor.constants')
    @patch('gdoc_summaries.libs.summary_processor.discovery')
    @patch('gdoc_summaries.libs.summary_processor.llm')
    def test_handle_context_length_exceeded(
        self, mock_llm, mock_discovery, mock_constants, 
        mock_gdoc, mock_db, mock_document_info, mock_google_doc
    ):
        # Setup
        mock_db.get_summary_from_db.return_value = None
        mock_constants.get_doc_info.return_value = [mock_document_info]
        mock_gdoc.get_document_from_id.return_value = mock_google_doc
        mock_llm.generate_llm_summary.side_effect = RuntimeError("context_length_exceeded")
        
        # Execute
        summary_processor.process_summaries(constants.SummaryType.TDD)
        
        # Verify
        mock_db.save_summary_to_db.assert_not_called()
        mock_db.mark_summary_as_sent.assert_not_called()

    @patch('gdoc_summaries.libs.summary_processor.db')
    @patch('gdoc_summaries.libs.summary_processor.gdoc_client')
    @patch('gdoc_summaries.libs.summary_processor.constants')
    @patch('gdoc_summaries.libs.summary_processor.discovery')
    def test_no_summaries_to_process(
        self, mock_discovery, mock_constants, mock_gdoc, mock_db
    ):
        # Setup
        mock_constants.get_doc_info.return_value = []
        
        # Execute
        summary_processor.process_summaries(constants.SummaryType.TDD)
        
        # Verify
        mock_db.save_summary_to_db.assert_not_called()
        mock_db.mark_summary_as_sent.assert_not_called()

    @patch('gdoc_summaries.libs.summary_processor.db')
    @patch('gdoc_summaries.libs.summary_processor.gdoc_client')
    @patch('gdoc_summaries.libs.summary_processor.constants')
    @patch('gdoc_summaries.libs.summary_processor.discovery')
    @patch('gdoc_summaries.libs.summary_processor.llm')
    def test_handle_other_runtime_error(
        self, mock_llm, mock_discovery, mock_constants, 
        mock_gdoc, mock_db, mock_document_info, mock_google_doc
    ):
        # Setup
        mock_db.get_summary_from_db.return_value = None
        mock_constants.get_doc_info.return_value = [mock_document_info]
        mock_gdoc.get_document_from_id.return_value = mock_google_doc
        mock_llm.generate_llm_summary.side_effect = RuntimeError("Other error")
        
        # Execute and verify
        with pytest.raises(RuntimeError, match="Other error"):
            summary_processor.process_summaries(constants.SummaryType.TDD)
