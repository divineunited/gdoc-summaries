"""Unit tests for the email client"""
import os
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

import gdoc_summaries.libs.constants as constants
import gdoc_summaries.libs.email_client as email_client


@pytest.fixture
def mock_summaries():
    """Mock summaries for testing"""
    return [
        constants.Summary(
            document_id="123abc",
            title="Test Document 1",
            content="This is a test summary",
            date_published="2024-03-15",
            summary_type=constants.SummaryType.TDD
        ),
        constants.Summary(
            document_id="456def",
            title="Test Document 2",
            content="This is another test summary",
            date_published="2024-03-16",
            summary_type=constants.SummaryType.TDD
        )
    ]

@pytest.fixture
def expected_email_content(mock_summaries):
    """Helper fixture to generate expected email content"""
    current_date = datetime.now().strftime('%Y-%m-%d')
    content = "<p>Hi everyone!</p><p>Here are AI generated summaries of recent documents to review:</p><hr>"
    
    for summary in mock_summaries:
        content += f'<h3>{summary.title}</h3>'
        content += f'<p><em>Published: {summary.date_published}</em></p>'
        content += f'<p>{summary.content}</p>'
        content += f'<p>Click <a href="https://docs.google.com/document/d/{summary.document_id}">here</a> to read.</p>'
        content += "<hr>"
    
    content += '<p>If a summary was sent. It will not be sent again. </p>'
    content += '<p>See <a href="https://cloverhealth.atlassian.net/wiki/x/CACt0Q">previously sent TDDs</a>'
    content += ' | <a href="https://cloverhealth.atlassian.net/wiki/x/kADt0w">previously sent PRDs</a>'
    content += ' | <a href="https://cloverhealth.atlassian.net/wiki/x/cIDs0w">previously sent Biweekly Summaries</a></p>'
    content += "<p>Also, enjoy this randomly generated joke:</p>"
    
    return content

class TestBuildAndSendEmail:
    @patch('gdoc_summaries.libs.email_client.SendGridAPIClient')
    @patch('gdoc_summaries.libs.email_client.Mail')
    @patch('gdoc_summaries.libs.email_client.pyjokes.get_joke')
    def test_successful_email_send(self, mock_joke, mock_mail, mock_sendgrid, mock_summaries, expected_email_content):
        # Setup
        mock_joke.return_value = "Test joke"
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_response.body = "test"
        mock_response.headers = {}
        
        mock_sendgrid_instance = mock_sendgrid.return_value
        mock_sendgrid_instance.send.return_value = mock_response
        
        test_email = "test@example.com"
        
        # Execute
        email_client.build_and_send_email(
            email_address=test_email,
            summaries=mock_summaries,
            summary_type=constants.SummaryType.TDD
        )
        
        # Verify
        mock_mail.assert_called_once()
        call_kwargs = mock_mail.call_args.kwargs
        assert call_kwargs['from_email'] == "danny.vu@cloverhealth.com"
        assert call_kwargs['to_emails'] == test_email
        assert expected_email_content in call_kwargs['html_content']
        assert "Test joke" in call_kwargs['html_content']
        
        mock_sendgrid_instance.send.assert_called_once()

    @patch('gdoc_summaries.libs.email_client.SendGridAPIClient')
    @patch('gdoc_summaries.libs.email_client.Mail')
    def test_email_send_failure(self, mock_mail, mock_sendgrid, mock_summaries):
        # Setup
        mock_sendgrid_instance = mock_sendgrid.return_value
        mock_sendgrid_instance.send.side_effect = Exception("Failed to send email")
        
        # Execute and verify
        with pytest.raises(Exception, match="Failed to send email"):
            email_client.build_and_send_email(
                email_address="test@example.com",
                summaries=mock_summaries,
                summary_type=constants.SummaryType.TDD
            )

    @patch('gdoc_summaries.libs.email_client.SendGridAPIClient')
    @patch('gdoc_summaries.libs.email_client.Mail')
    @patch.dict(os.environ, {'SENDGRID_API_KEY': 'test_api_key'})
    def test_sendgrid_api_key_usage(self, mock_mail, mock_sendgrid, mock_summaries):
        # Execute
        email_client.build_and_send_email(
            email_address="test@example.com",
            summaries=mock_summaries,
            summary_type=constants.SummaryType.TDD
        )
        
        # Verify
        mock_sendgrid.assert_called_once_with('test_api_key')
