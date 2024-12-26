"""Unit tests for the Google Doc client"""
from unittest.mock import MagicMock, patch

import pytest
from google.oauth2.credentials import Credentials

import gdoc_summaries.libs.gdoc_client as gdoc_client


@pytest.fixture
def mock_credentials():
    return MagicMock(spec=Credentials)

@pytest.fixture
def mock_document():
    return {
        "title": "Test Document",
        "body": {
            "content": [
                {
                    "paragraph": {
                        "elements": [
                            {
                                "textRun": {
                                    "content": "First paragraph content.\n"
                                }
                            }
                        ]
                    }
                },
                {
                    "paragraph": {
                        "elements": [
                            {
                                "textRun": {
                                    "content": "Second paragraph content.\n"
                                }
                            }
                        ]
                    }
                }
            ]
        }
    }

class TestGetCredentials:
    @patch('gdoc_summaries.libs.gdoc_client.auth')
    def test_valid_credentials(self, mock_auth, mock_credentials):
        # Setup
        mock_auth.load_credentials_from_file.return_value = (mock_credentials, None)
        mock_credentials.valid = True
        
        # Execute
        creds = gdoc_client.get_credentials("fake/path", gdoc_client.SCOPES)
        
        # Verify
        assert creds == mock_credentials
        mock_auth.load_credentials_from_file.assert_called_once_with(
            "fake/path", 
            scopes=gdoc_client.SCOPES
        )
        mock_credentials.refresh.assert_not_called()

    @patch('gdoc_summaries.libs.gdoc_client.auth')
    @patch('gdoc_summaries.libs.gdoc_client.Request')
    def test_expired_credentials(self, mock_request, mock_auth, mock_credentials):
        # Setup
        mock_auth.load_credentials_from_file.return_value = (mock_credentials, None)
        mock_credentials.valid = False
        mock_credentials.expired = True
        mock_credentials.refresh_token = True
        
        # Execute
        creds = gdoc_client.get_credentials("fake/path", gdoc_client.SCOPES)
        
        # Verify
        assert creds == mock_credentials
        mock_credentials.refresh.assert_called_once()

    @patch('gdoc_summaries.libs.gdoc_client.auth')
    def test_no_credentials(self, mock_auth):
        # Setup
        mock_auth.load_credentials_from_file.return_value = (None, None)
        
        # Execute
        creds = gdoc_client.get_credentials("fake/path", gdoc_client.SCOPES)
        
        # Verify
        assert creds is None


class TestGetDocumentFromId:
    def test_successful_document_retrieval(self, mock_document):
        # Setup
        mock_service = MagicMock()
        mock_service.documents().get().execute.return_value = mock_document
        
        # Execute
        result = gdoc_client.get_document_from_id(mock_service, "test_doc_id")
        
        # Verify
        assert result == mock_document
        mock_service.documents().get.assert_called_with(documentId="test_doc_id")

    def test_failed_document_retrieval(self):
        # Setup
        mock_service = MagicMock()
        mock_service.documents().get().execute.side_effect = Exception("API Error")
        
        # Execute and verify
        with pytest.raises(Exception, match="API Error"):
            gdoc_client.get_document_from_id(mock_service, "test_doc_id")


class TestExtractDocumentContent:
    def test_extract_simple_content(self, mock_document):
        # Execute
        content = gdoc_client.extract_document_content(mock_document)
        
        # Verify
        expected_content = "First paragraph content.\nSecond paragraph content.\n"
        assert content == expected_content

    def test_extract_empty_document(self):
        # Setup
        empty_document = {"body": {"content": []}}
        
        # Execute
        content = gdoc_client.extract_document_content(empty_document)
        
        # Verify
        assert content == ""

    def test_extract_missing_elements(self):
        # Setup
        document = {
            "body": {
                "content": [
                    {"paragraph": {}},  # Missing elements
                    {"paragraph": {"elements": []}}  # Empty elements
                ]
            }
        }
        
        # Execute
        content = gdoc_client.extract_document_content(document)
        
        # Verify
        assert content == ""

    def test_extract_mixed_content(self):
        # Setup
        document = {
            "body": {
                "content": [
                    {
                        "paragraph": {
                            "elements": [
                                {"textRun": {"content": "Text content.\n"}},
                                {"other_element": {"content": "Should be ignored"}}
                            ]
                        }
                    },
                    {"non_paragraph": {"should": "be ignored"}},
                    {
                        "paragraph": {
                            "elements": [
                                {"textRun": {"content": "More text.\n"}}
                            ]
                        }
                    }
                ]
            }
        }
        
        # Execute
        content = gdoc_client.extract_document_content(document)
        
        # Verify
        expected_content = "Text content.\nMore text.\n"
        assert content == expected_content
