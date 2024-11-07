"""Main entrypoint for script to run Gdoc Summaries"""

import logging
import os.path
from datetime import datetime, timedelta

import pyjokes
from google import auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient import discovery
from googleapiclient.errors import HttpError
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from gdoc_summaries.lib import constants

LOGGER = logging.getLogger(__name__)

# This script needs scope access to the Docs and Drive and Email APIs
SCOPES = [
    "https://www.googleapis.com/auth/documents.readonly",
    "https://www.googleapis.com/auth/drive.metadata.readonly",
]

# TODO: deployment considerations:
CREDS_PATH = os.path.expanduser("~/Downloads/eng-sandbox-30f6bd0e093d.json")


def get_credentials(creds_path: str, scopes: list[str]) -> Credentials:
    """Get Google API Credentials"""
    creds, _ = auth.load_credentials_from_file(creds_path, scopes=scopes)

    # If the credentials are invalid (e.g., expired), refresh them
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

    return creds


def get_doc_ids_from_drive(creds: Credentials) -> list[str]:
    """
    This function gets all relevant Google Docs that it has access to
    from the Google Drive API
    """
    # Get the date 30 days ago
    past_date = datetime.now() - timedelta(days=30)
    past_date_str = (
        past_date.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    )  # Format it as RFC 3339 timestamp

    doc_ids = []
    try:
        # Call the Drive v3 API
        service = discovery.build("drive", "v3", credentials=creds)
        # Query for Google Docs modified or created in the last 30 days
        # -- change to createdTime if modified is too noisy
        # -- remove the q object if you dont want to filter at all
        request = service.files().list(
            q=f"mimeType='application/vnd.google-apps.document' and modifiedTime >= '{past_date_str}'",
            pageSize=100,
            fields="nextPageToken, files(id, name)",
        )

        while request is not None:
            results = request.execute()
            items: list[dict] = results.get("files", [])

            if items:
                doc_ids.extend([item["id"] for item in items])

            request = service.files().list_next(request, results)
    except HttpError as error:
        print(f"An error occurred: {error}")
        raise

    if not doc_ids:
        LOGGER.warning("No files found.")

    return doc_ids


def get_doc_from_id(creds: Credentials, document_id: str) -> dict:
    """
    Use the Google Docs API to return the GDoc as a dict
    given the Doc ID
    """
    try:
        # Retrieve the documents contents from the Docs service.
        service = discovery.build("docs", "v1", credentials=creds)
        document = service.documents().get(documentId=document_id).execute()
    except HttpError as err:
        print(err)
        raise

    print(f"---NEXT DOC: {document.get('title')}---")
    return document


def find_executive_summary(doc_contents: dict) -> str:
    """
    Given a the content of a GDoc represented as a Python Dict
    Find an Executive Summary.
    """
    exec_summary = ""
    exec_summary_index = None
    # Find the index of the sign off table:
    for i, content in enumerate(doc_contents):
        header_content = (
            content.get("paragraph", {})
            .get("elements", [{}])[0]
            .get("textRun", {})
            .get("content", "")
        )

        if not header_content:
            continue

        # If the header portion has the text "executive summary"
        if header_content.strip().lower() == "executive summary":
            # then the summary should be the content below it.
            exec_summary_index = i + 1
            break
    if exec_summary_index is None:
        return exec_summary

    for i in range(exec_summary_index, len(doc_contents) - exec_summary_index):
        # The executive summary is normal text that can be split up into paragraphs
        # each paragraph / new line is a new entry in the doc_contents
        if (
            doc_contents[i]["paragraph"]["paragraphStyle"]["namedStyleType"]
            == "NORMAL_TEXT"
        ):
            exec_summary += doc_contents[i]["paragraph"]["elements"][0]["textRun"][
                "content"
            ]
        else:  # We reached the next section.
            break
    return exec_summary


def build_and_send_email(
    *, email_address: str, summaries: list[tuple[str, str, str]]
):
    """Use Sendgrid's API Client to send an email"""
    sender_email = "danny.vu@cloverhealth.com"  # TODO: replace with prod email
    subject = "TDRB Summary" # TODO: include one liner
    body_html = "<p>Greetings!</p><p>Here are summaries of documents to review.</p>"

    for doc_name, doc_id, summary in summaries:
        body_html += f'<h3>{doc_name}</h3>'
        if summary:
            body_html += "<p><strong>Executive Summary:</strong> " + summary + "</p>"
        body_html += f'<p>Click <a href="https://docs.google.com/document/d/{doc_id}">here</a> to read.</p>'
        body_html += "<hr>"

    body_html += "<p>--This was an automated email. Please do not reply. However, enjoy this joke--</p>"
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



def entrypoint() -> None:
    """Entrypoint for GDoc Summaries"""

    # Get the Creds and potential Google Doc IDs
    creds = get_credentials(creds_path=CREDS_PATH, scopes=SCOPES)
    doc_ids = get_doc_ids_from_drive(creds)

    # Do the work for each GDoc
    summaries = []
    for doc_id in doc_ids:
        document = get_doc_from_id(creds, doc_id)
        contents = document.get("body", {}).get("content", [])
        if not contents:
            print(f"No content found for {doc_id=}")
            continue

        executive_summary = find_executive_summary(contents)
        summaries.append((document["title"], document["documentId"], executive_summary))

    for email in constants.TDRB_SUBSCRIBERS:
        print(f"SENDING EMAIL TO: {email}")
        build_and_send_email(email_address=email, summaries=summaries)


if __name__ == "__main__":
    entrypoint()
