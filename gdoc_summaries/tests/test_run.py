"""Tests for our run function"""
import os
from unittest.mock import Mock, patch

import pytest
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError

from gdoc_summaries import run


def test_get_credentials_valid():
    """Test get_credentials returns valid credentials"""
    valid_creds = Mock(valid=True)
    with patch(
        "gdoc_summaries.run.auth.load_credentials_from_file",
        return_value=(valid_creds, None),
    ):
        creds = run.get_credentials("path/to/creds", ["scope1", "scope2"])
        assert creds == valid_creds


def test_get_credentials_invalid_no_refresh_token():
    """Test run.get_credentials with invalid credentials and no refresh token"""
    invalid_creds = Mock(valid=False, expired=True, refresh_token=None)
    with patch(
        "gdoc_summaries.run.auth.load_credentials_from_file",
        return_value=(invalid_creds, None),
    ):
        creds = run.get_credentials("path/to/creds", ["scope1", "scope2"])
        assert creds == invalid_creds


def test_get_credentials_refresh():
    """Test run.get_credentials refreshes expired credentials"""
    expired_creds = Mock(valid=False, expired=True, refresh_token="token")
    refreshed_creds = Mock(valid=True)
    expired_creds.refresh = Mock(return_value=refreshed_creds)

    with patch(
        "gdoc_summaries.run.auth.load_credentials_from_file",
        return_value=(expired_creds, None),
    ):
        creds = run.get_credentials("path/to/creds", ["scope1", "scope2"])
        expired_creds.refresh.assert_called_once()
        assert creds == expired_creds


def test_get_doc_ids_dates_from_drive_success():
    """Test get_doc_ids_dates_from_drive returns doc ids successfully"""
    mock_service = Mock()
    mock_service.files().list().execute.return_value = {
        "files": [{"id": "1"}, {"id": "2"}, {"id": "3"}],
        "nextPageToken": None,
    }

    mock_service.files().list_next.return_value = None

    with patch("gdoc_summaries.run.build", return_value=mock_service):
        doc_ids = run.get_doc_ids_dates_from_drive(Credentials)
        assert doc_ids == ["1", "2", "3"]


def test_get_doc_ids_dates_from_drive_no_files():
    """Test run.get_doc_ids_dates_from_drive returns empty list when no files found"""
    mock_service = Mock()
    mock_service.files().list().execute.return_value = {
        "files": [],
        "nextPageToken": None,
    }

    mock_service.files().list_next.return_value = None

    with patch("gdoc_summaries.run.build", return_value=mock_service):
        doc_ids = run.get_doc_ids_dates_from_drive(Credentials)
        assert doc_ids == []


def test_get_doc_ids_dates_from_drive_http_error():
    """Test run.get_doc_ids_dates_from_drive raises HttpError"""
    mock_service = Mock()
    mock_service.files().list().execute.side_effect = HttpError(Mock(), b"error")

    with patch("gdoc_summaries.run.build", return_value=mock_service):
        with pytest.raises(HttpError):
            run.get_doc_ids_dates_from_drive(Credentials)


def test_get_doc_from_id_success():
    """Test run.get_doc_from_id returns document successfully"""
    mock_service = Mock()
    mock_service.documents().get().execute.return_value = {"title": "Document 1"}

    with patch("gdoc_summaries.run.build", return_value=mock_service):
        doc = run.get_doc_from_id(Credentials, "document_id_1")
        assert doc == {"title": "Document 1"}


def test_get_doc_from_id_http_error():
    """Test run.get_doc_from_id raises HttpError"""
    mock_service = Mock()
    mock_service.documents().get().execute.side_effect = HttpError(Mock(), b"error")

    with patch("gdoc_summaries.run.build", return_value=mock_service):
        with pytest.raises(HttpError):
            run.get_doc_from_id(Credentials, "document_id_1")


def test_find_signoff_table_success():
    """Test run.find_signoff_table finds a signoff table successfully"""
    doc_contents = [
        {"paragraph": {"elements": [{"textRun": {"content": "Signoff"}}]}},
        {"table": "table_content"},
    ]
    table = run.find_signoff_table(doc_contents)
    assert table == "table_content"


def test_find_signoff_table_no_signoff():
    """Test run.find_signoff_table returns None when no signoff header is found"""
    doc_contents = [
        {"paragraph": {"elements": [{"textRun": {"content": "Not Signoff"}}]}},
        {"table": "table_content"},
    ]
    table = run.find_signoff_table(doc_contents)
    assert table is None


def test_find_signoff_table_no_table():
    """Test run.find_signoff_table returns None when no table is found after signoff header"""
    doc_contents = [
        {"paragraph": {"elements": [{"textRun": {"content": "Signoff"}}]}},
        {"not_table": "no_table_content"},
    ]
    table = run.find_signoff_table(doc_contents)
    assert table is None


def test_find_executive_summary_success():
    """Test run.find_executive_summary finds the executive summary successfully"""
    doc_contents = [
        {"paragraph": {"elements": [{"textRun": {"content": "Executive Summary"}}]}},
        {
            "paragraph": {
                "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                "elements": [{"textRun": {"content": "Summary content."}}],
            }
        },
        {
            "paragraph": {
                "paragraphStyle": {"namedStyleType": "NOT_NORMAL_TEXT"},
                "elements": [{"textRun": {"content": "Not part of summary."}}],
            }
        },
    ]
    exec_summary = run.find_executive_summary(doc_contents)
    assert exec_summary == "Summary content."


def test_find_executive_summary_no_exec_summary():
    """Test run.find_executive_summary returns empty string when no executive summary is found"""
    doc_contents = [
        {
            "paragraph": {
                "elements": [{"textRun": {"content": "Not Executive Summary"}}]
            }
        },
        {
            "paragraph": {
                "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                "elements": [{"textRun": {"content": "Not summary content."}}],
            }
        },
    ]
    exec_summary = run.find_executive_summary(doc_contents)
    assert exec_summary == ""


def test_find_executive_summary_no_normal_text():
    """Test run.find_executive_summary returns empty string when no normal text is found after executive summary"""
    doc_contents = [
        {"paragraph": {"elements": [{"textRun": {"content": "Executive Summary"}}]}},
        {
            "paragraph": {
                "paragraphStyle": {"namedStyleType": "NOT_NORMAL_TEXT"},
                "elements": [{"textRun": {"content": "Not summary content."}}],
            }
        },
    ]
    exec_summary = run.find_executive_summary(doc_contents)
    assert exec_summary == ""


def test_find_email_and_signoff_from_row_success():
    """Test run.find_email_and_signoff_from_row finds email and signoff successfully"""
    cells = [
        {
            "content": [
                {
                    "paragraph": {
                        "elements": [
                            {
                                "person": {
                                    "personProperties": {"email": "email@example.com"}
                                }
                            }
                        ]
                    }
                }
            ]
        },
        {},
        {
            "content": [
                {
                    "paragraph": {
                        "elements": [{"textRun": {"content": "Signoff content"}}]
                    }
                }
            ]
        },
    ]
    email, signoff = run.find_email_and_signoff_from_row(cells)
    assert email == "email@example.com"
    assert signoff == "Signoff content"


def test_find_email_and_signoff_from_row_no_email():
    """Test run.find_email_and_signoff_from_row returns empty strings when no email is found"""
    cells = [
        {"content": [{"paragraph": {"elements": [{}]}}]},
        {},
        {
            "content": [
                {
                    "paragraph": {
                        "elements": [{"textRun": {"content": "Signoff content"}}]
                    }
                }
            ]
        },
    ]
    email, signoff = run.find_email_and_signoff_from_row(cells)
    assert email == ""
    assert signoff == "Signoff content"


def test_find_email_and_signoff_from_row_no_signoff():
    """Test run.find_email_and_signoff_from_row returns empty strings when no signoff is found"""
    cells = [
        {
            "content": [
                {
                    "paragraph": {
                        "elements": [
                            {
                                "person": {
                                    "personProperties": {"email": "email@example.com"}
                                }
                            }
                        ]
                    }
                }
            ]
        },
        {},
        {"content": [{"paragraph": {"elements": [{}]}}]},
    ]
    email, signoff = run.find_email_and_signoff_from_row(cells)
    assert email == "email@example.com"
    assert signoff == ""


def test_find_email_and_signoff_from_row_no_cells():
    """Test run.find_email_and_signoff_from_row returns empty strings when no cells are given"""
    cells = []
    email, signoff = run.find_email_and_signoff_from_row(cells)
    assert email == ""
    assert signoff == ""


def test_build_and_send_email():
    # Set up
    mock_sendgrid = patch("gdoc_summaries.run.SendGridAPIClient")
    email_address = "test@test.com"
    doc_name = "Test Document"
    doc_id = "test123"
    summary = "This is a test summary"
    os.environ["SENDGRID_API_KEY"] = "test_api_key"

    # Execute
    with mock_sendgrid as mock_sg:
        mock_sg.return_value.send.return_value.status_code = 202
        run.build_and_send_email(
            email_address=email_address,
            doc_name=doc_name,
            doc_id=doc_id,
            summary=summary,
        )

        # Assert
        mock_sg.assert_called_once_with("test_api_key")
        mock_sg.return_value.send.assert_called_once()
        assert mock_sg.return_value.send.return_value.status_code == 202
