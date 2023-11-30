"""Main entrypoint for script to run Gdoc Summaries"""

import logging
import os.path
from datetime import datetime, timedelta

from google import auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

LOGGER = logging.getLogger(__name__)

# This script needs scope access to the Docs and Drive and Email APIs
SCOPES = [
    "https://www.googleapis.com/auth/documents.readonly",
    "https://www.googleapis.com/auth/drive.metadata.readonly",
    "https://www.googleapis.com/auth/gmail.send",
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

    try:
        # Call the Drive v3 API
        service = build("drive", "v3", credentials=creds)
        # Query for Google Docs modified or created in the last 30 days
        # -- change to createdTime if modified is too noisy
        # -- remove the q object if you dont want to filter at all
        results: dict = (
            service.files()
            .list(
                q=f"mimeType='application/vnd.google-apps.document' and modifiedTime >= '{past_date_str}'",
                pageSize=10,
                fields="nextPageToken, files(id, name)",
            )
            .execute()
        )
        items: list[dict] = results.get("files", [])
    except HttpError as error:
        print(f"An error occurred: {error}")
        raise

    if not items:
        LOGGER.error("No files found.")
        return []

    doc_ids = [item["id"] for item in items]
    # doc_names = [item["name"] for item in items]
    # print(f"File IDs: {doc_ids}")
    # print(f"File Doc Names: {doc_names}")

    return doc_ids


def get_doc_from_id(creds: Credentials, document_id: str) -> dict:
    """
    Use the Google Docs API to return the GDoc as a dict
    given the Doc ID
    """
    try:
        # Retrieve the documents contents from the Docs service.
        service = build("docs", "v1", credentials=creds)
        document = service.documents().get(documentId=document_id).execute()
    except HttpError as err:
        print(err)
        raise

    print(f"---NEXT DOC: {document.get('title')}---")
    return document


def find_signoff_table(doc_contents: dict) -> dict | None:
    """
    Given a the content of a GDoc represented as a Python Dict
    Find the index where the SignOff table would be stored.
    """
    table_index = None
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

        # If the header portion has the text "Signoff"
        if header_content.strip().lower() in ("signoff", "sign-off"):
            # then the signoff table is the next content right below it.
            table_index = i + 1
            break
    if table_index is not None:
        try:
            # make sure the table exists:
            table = doc_contents[table_index]["table"]
            return table
        except KeyError:
            return None


def find_email_and_signoff_from_row(cells: list[str]) -> tuple[str, str]:
    """Extracts the email and signoff from a row of cells in a GDoc

    The table must be formatted such with 3 columns in the @NAME | RACI | DATE format
    Example: @DannyVu | R | 2023-12-25
    """
    # wrap this to defend against malformed tables
    try:
        email = (
            cells[0]
            .get("content", [{}])[0]
            .get("paragraph", {})
            .get("elements", [{}])[0]
            .get("person", {})
            .get("personProperties", {})
            .get("email", "")
        ).strip()

        # Check for sign off in the 3rd column
        signoff = (
            cells[2]
            .get("content", [{}])[0]
            .get("paragraph", {})
            .get("elements", [{}])[0]
            .get("textRun", {})
            .get("content", "")
        ).strip()
    except IndexError:
        print("Malformed table: no email / signoff found.")
        return "", ""

    return email, signoff


def send_email(*, email_address: str, doc_name: str, doc_id: str):
    """Use Sendgrid's API Client to send an email"""
    sender_email = "danny.vu@cloverhealth.com"  # TODO: replace with prod email
    subject = f"Sign-off Required: {doc_name}"
    message_text = f"Here is your document {doc_name} with id {doc_id}. Please sign off. This will expire in 30 days."  # TODO: Add executive summary + NLP
    message = Mail(
        from_email=sender_email,
        to_emails=email_address,
        subject=subject,
        plain_text_content=message_text,
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
    for doc_id in doc_ids:
        document = get_doc_from_id(creds, doc_id)
        contents = document.get("body", {}).get("content", [])
        if not contents:
            continue

        table = find_signoff_table(contents)
        if table is None:
            print(f"No signoff table was found for Doc ID: {doc_id}")
            continue

        # Extract signoff details from the table
        for row in table["tableRows"]:
            cells: list[dict] = row["tableCells"]
            email, signoff = find_email_and_signoff_from_row(cells=cells)
            if not email:
                continue
            if not signoff:  # not signed off, send email to remind for signoff.
                # TODO: Get Executive Summary (And possible NLP summary) to send along with email
                send_email(
                    email_address=email,
                    doc_name=document["title"],
                    doc_id=document["documentId"],
                )


if __name__ == "__main__":
    entrypoint()
