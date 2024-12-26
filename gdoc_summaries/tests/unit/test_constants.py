"""Unit tests for the constants module"""
import pytest

import gdoc_summaries.libs.constants as constants


class TestExtractDocInfo:
    def test_valid_url(self):
        doc_entry = {
            "url": "https://docs.google.com/document/d/abc123def456/edit",
            "date_published": "2024-03-15"
        }
        doc_info = constants._extract_doc_info(doc_entry)
        assert doc_info.document_id == "abc123def456"
        assert doc_info.date_published == "2024-03-15"

    def test_invalid_url_format(self):
        doc_entry = {
            "url": "https://invalid-url.com/doc",
            "date_published": "2024-03-15"
        }
        with pytest.raises(ValueError, match="Invalid Google Docs URL format"):
            constants._extract_doc_info(doc_entry)

    def test_unparseable_document_id(self):
        doc_entry = {
            "url": "https://docs.google.com/document/invalid",
            "date_published": "2024-03-15"
        }
        with pytest.raises(ValueError, match="Could not extract document ID"):
            constants._extract_doc_info(doc_entry)
