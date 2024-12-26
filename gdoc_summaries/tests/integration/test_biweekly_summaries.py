"""Integration tests for the biweekly summaries"""
from unittest.mock import patch

import pytest

import gdoc_summaries.biweekly_summaries as biweekly_summaries
import gdoc_summaries.libs.constants as constants


@pytest.fixture
def mock_document_info():
    return constants.DocumentInfo(
        document_id="test_doc_123",
        date_published="2024-03-15"
    )

@pytest.fixture
def mock_document_section():
    return constants.DocumentSection(
        section_date="2024-03-15",
        content="Test section content",
        raw_content="--- UPDATE 2024-03-15 ---\nTest section content"
    )

@pytest.fixture
def mock_google_doc():
    return {
        "title": "Test Biweekly Document",
        "body": {
            "content": [
                {
                    "paragraph": {
                        "elements": [
                            {
                                "textRun": {
                                    "content": "--- UPDATE 2024-03-15 ---\nLatest update content\n"
                                }
                            }
                        ]
                    }
                }
            ]
        }
    }


class TestProcessBiweeklySummaries:
    @patch('gdoc_summaries.biweekly_summaries.db')
    @patch('gdoc_summaries.biweekly_summaries.gdoc_client')
    @patch('gdoc_summaries.biweekly_summaries.constants')
    @patch('gdoc_summaries.biweekly_summaries.discovery')
    @patch('gdoc_summaries.biweekly_summaries.section_parser')
    @patch('gdoc_summaries.biweekly_summaries.llm')
    @patch('gdoc_summaries.biweekly_summaries.email_client')
    def test_process_new_section(
        self, mock_email, mock_llm, mock_parser, mock_discovery, 
        mock_constants, mock_gdoc, mock_db, 
        mock_document_info, mock_document_section, mock_google_doc
    ):
        # Setup
        mock_constants.get_doc_info.return_value = [mock_document_info]
        mock_constants.get_subscribers.return_value = ["test@example.com"]
        mock_gdoc.get_document_from_id.return_value = mock_google_doc
        mock_parser.extract_latest_section.return_value = mock_document_section
        mock_db.get_latest_section_date.return_value = "2024-03-01"  # Older date
        mock_db.get_unsent_sections.return_value = [
            ("2024-03-15", "<p>Test summary content</p>")
        ]
        mock_llm.generate_llm_summary.return_value = "<p>Test summary content</p>"
        
        # Execute
        biweekly_summaries.process_biweekly_summaries()
        
        # Verify
        mock_db.setup_database.assert_called_once()
        mock_gdoc.get_credentials.assert_called_once()
        mock_gdoc.get_document_from_id.assert_called_once()
        mock_parser.extract_latest_section.assert_called_once()
        mock_llm.generate_llm_summary.assert_called_once()
        mock_db.save_section_to_db.assert_called_once()
        mock_email.build_and_send_email.assert_called_once()
        mock_db.mark_sections_as_sent.assert_called_once()

    @patch('gdoc_summaries.biweekly_summaries.db')
    @patch('gdoc_summaries.biweekly_summaries.gdoc_client')
    @patch('gdoc_summaries.biweekly_summaries.constants')
    @patch('gdoc_summaries.biweekly_summaries.discovery')
    @patch('gdoc_summaries.biweekly_summaries.section_parser')
    def test_skip_old_section(
        self, mock_parser, mock_discovery, mock_constants, 
        mock_gdoc, mock_db, mock_document_info, mock_document_section
    ):
        # Setup
        mock_constants.get_doc_info.return_value = [mock_document_info]
        mock_parser.extract_latest_section.return_value = mock_document_section
        mock_db.get_latest_section_date.return_value = "2024-03-15"  # Same date
        
        # Execute
        biweekly_summaries.process_biweekly_summaries()
        
        # Verify
        mock_db.save_section_to_db.assert_not_called()
        mock_db.mark_sections_as_sent.assert_not_called()

    @patch('gdoc_summaries.biweekly_summaries.db')
    @patch('gdoc_summaries.biweekly_summaries.gdoc_client')
    @patch('gdoc_summaries.biweekly_summaries.constants')
    @patch('gdoc_summaries.biweekly_summaries.discovery')
    @patch('gdoc_summaries.biweekly_summaries.section_parser')
    def test_no_sections_found(
        self, mock_parser, mock_discovery, mock_constants, 
        mock_gdoc, mock_db, mock_document_info
    ):
        # Setup
        mock_constants.get_doc_info.return_value = [mock_document_info]
        mock_parser.extract_latest_section.return_value = None
        
        # Execute and verify
        with pytest.raises(ValueError, match=f"No sections found in document {mock_document_info.document_id}"):
            biweekly_summaries.process_biweekly_summaries()

    @patch('gdoc_summaries.biweekly_summaries.db')
    @patch('gdoc_summaries.biweekly_summaries.gdoc_client')
    @patch('gdoc_summaries.biweekly_summaries.constants')
    @patch('gdoc_summaries.biweekly_summaries.discovery')
    @patch('gdoc_summaries.biweekly_summaries.section_parser')
    @patch('gdoc_summaries.biweekly_summaries.llm')
    @patch('gdoc_summaries.biweekly_summaries.email_client')
    def test_multiple_documents_with_updates(
        self, mock_email, mock_llm, mock_parser, mock_discovery, 
        mock_constants, mock_gdoc, mock_db
    ):
        # Setup
        doc_infos = [
            constants.DocumentInfo(document_id=f"doc_{i}", date_published="2024-03-15")
            for i in range(2)
        ]
        sections = [
            constants.DocumentSection(
                section_date="2024-03-15",
                content=f"Test content {i}",
                raw_content=f"--- UPDATE 2024-03-15 ---\nTest content {i}"
            )
            for i in range(2)
        ]
        
        mock_constants.get_doc_info.return_value = doc_infos
        mock_constants.get_subscribers.return_value = ["test@example.com"]
        mock_parser.extract_latest_section.side_effect = sections
        mock_db.get_latest_section_date.return_value = "2024-03-01"
        mock_db.get_unsent_sections.return_value = [
            ("2024-03-15", "<p>Test summary content</p>")
        ]
        mock_llm.generate_llm_summary.return_value = "<p>Test summary content</p>"
        
        # Execute
        biweekly_summaries.process_biweekly_summaries()
        
        # Verify
        assert mock_db.save_section_to_db.call_count == 2
        assert mock_email.build_and_send_email.call_count == 1
        assert mock_db.mark_sections_as_sent.call_count == 2

    @patch('gdoc_summaries.biweekly_summaries.db')
    @patch('gdoc_summaries.biweekly_summaries.gdoc_client')
    @patch('gdoc_summaries.biweekly_summaries.constants')
    @patch('gdoc_summaries.biweekly_summaries.discovery')
    def test_no_documents_to_process(
        self, mock_discovery, mock_constants, mock_gdoc, mock_db
    ):
        # Setup
        mock_constants.get_doc_info.return_value = []
        
        # Execute
        biweekly_summaries.process_biweekly_summaries()
        
        # Verify
        mock_db.save_section_to_db.assert_not_called()
        mock_db.mark_sections_as_sent.assert_not_called()

    @patch('gdoc_summaries.biweekly_summaries.db')
    @patch('gdoc_summaries.biweekly_summaries.gdoc_client')
    @patch('gdoc_summaries.biweekly_summaries.constants')
    @patch('gdoc_summaries.biweekly_summaries.discovery')
    @patch('gdoc_summaries.biweekly_summaries.section_parser')
    def test_error_handling(
        self, mock_parser, mock_discovery, mock_constants, 
        mock_gdoc, mock_db, mock_document_info
    ):
        # Setup
        mock_constants.get_doc_info.return_value = [mock_document_info]
        mock_parser.extract_latest_section.side_effect = Exception("Test error")
        
        # Execute and verify
        with pytest.raises(Exception, match="Test error"):
            biweekly_summaries.process_biweekly_summaries()
