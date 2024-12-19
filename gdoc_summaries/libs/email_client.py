"""LLM Based tooling"""

import logging
import os

import pyjokes
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

LOGGER = logging.getLogger(__name__)


def build_and_send_email(
    *, email_address: str, summaries: list[tuple[str, str, str, str]]
):
    """Use Sendgrid's API Client to send an email"""
    sender_email = "danny.vu@cloverhealth.com"
    subject = "Technical Documentation Summary"
    body_html = "<p>Hi everyone!</p><p>Here are summaries of recent technical documents to review:</p>"
    body_html += "<hr>"

    for doc_name, doc_id, summary, date_published in summaries:
        body_html += f'<h3>{doc_name}</h3>'
        body_html += f'<p><em>Published: {date_published}</em></p>'
        if summary:
            body_html += "<p>" + summary + "</p>"
        body_html += f'<p>Click <a href="https://docs.google.com/document/d/{doc_id}">here</a> to read.</p>'
        body_html += "<hr>"

    body_html += '<p>--If a summary was sent. It will not be sent again. See <a href="https://cloverhealth.atlassian.net/wiki/x/CACt0Q">here</a> for previously sent TDDs--</p>'
    body_html += "<p>--Also, enjoy this randomly generated joke:--</p>"
    body_html += f"<p>{pyjokes.get_joke(language='en', category='neutral')}</p>"

    message = Mail(
        from_email=sender_email,
        to_emails=email_address,
        subject=subject,
        html_content=body_html,
    )
    try:
        sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(f"Error sending email! Error: {e}")
        raise e