"""Main entrypoint for script to run Gdoc Summaries"""

import logging
import os
from datetime import datetime, timedelta

import markdown
import pyjokes
import requests
from azure.identity import DefaultAzureCredential
from google import auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient import discovery
from googleapiclient.errors import HttpError
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from gdoc_summaries.libs import constants, db

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


def get_doc_ids_dates_from_drive(creds: Credentials) -> list[tuple[str, str]]:
    """
    This function gets all relevant Google Docs that it has access to
    from the Google Drive API

    The Drive API gives date_created information as well.
    Which does not exist in the Docs API.
    """
    past_date = datetime.now() - timedelta(days=120)
    past_date_str = (
        past_date.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    )  # Format it as RFC 3339 timestamp

    doc_infos = []
    try:
        # Call the Drive v3 API
        service = discovery.build("drive", "v3", credentials=creds)
        request = service.files().list(
            q=f"mimeType='application/vnd.google-apps.document' and createdTime >= '{past_date_str}'",
            pageSize=100,
            orderBy="createdTime desc",
            fields="nextPageToken, files(id, name, createdTime)",
        )

        while request is not None:
            results = request.execute()
            items: list[dict] = results.get("files", [])

            if items:
                doc_infos.extend([(item["id"], item["createdTime"]) for item in items])

            request = service.files().list_next(request, results)
    except HttpError as error:
        print(f"An error occurred: {error}")
        raise

    if not doc_infos:
        LOGGER.warning("No files found.")

    return doc_infos


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


def generate_llm_summary(contents: list[dict]) -> str:
    """Generate a summary of the document content using Azure OpenAI"""

    prompt = (
        "As a professional summarizer, create a concise and comprehensive "
        "summary of the provided text while adhering to these guidelines:\n"
        "If there is an author, before the summary, add: Author(s): Name(s)\n"
        "Craft a summary that is detailed, thorough, in-depth, and complex, "
        "while maintaining clarity and conciseness.\n"
        "Incorporate main ideas and essential information, eliminating extraneous "
        "language and focusing on critical aspects.\n"
        "Rely strictly on the provided text, without including external information.\n"
        "Utilize markdown to cleanly format your output. " 
        "Example: Bold key subject matter and potential areas that may need expanded information.\n"
        "Content is as follows:\n"
        + str(contents)
    )

    # Prepare the prompt data for the ChatGPT model
    data = {
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 500
    }

    # Fetch token using Azure credential
    credential = DefaultAzureCredential()
    token = credential.get_token("https://cognitiveservices.azure.com/.default").token

    # Set headers for the Azure API request
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    # Make request to Azure OpenAI using the correct API format
    api_url = f"{constants.AZURE_API_BASE}/openai/deployments/{constants.AZURE_MODEL_ENGINE}/chat/completions?api-version={constants.AZURE_API_VERSION}"
    response = requests.post(api_url, headers=headers, json=data)

    if response.status_code == 200:
        print("Generated LLM Summary")
        markdown_content = response.json()["choices"][0]["message"]["content"].strip()
        html_content = markdown.markdown(markdown_content)
        return html_content
    else:
        print(f"Error in LLM request: {response.status_code}, {response.text}")
        return "Error generating summary."


def build_and_send_email(
    *, email_address: str, summaries: list[tuple[str, str, str, str]]
):
    """Use Sendgrid's API Client to send an email"""
    sender_email = "danny.vu@cloverhealth.com"
    subject = "Technical Documentation Summary"
    body_html = "<p>Greetings!</p><p>Here are summaries of recent documents to review:</p>"
    body_html += "<hr>"

    for doc_name, doc_id, created_time, summary in summaries:
        body_html += f'<h3>{doc_name}</h3>'
        body_html += f'<p><strong>Date Created:</strong> {created_time}</p>'
        if summary:
            body_html += "<p>" + summary + "</p>"
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

    # Set up the database
    db.setup_database()

    # Get the Creds and potential Google Doc IDs along with creation dates
    creds = get_credentials(creds_path=CREDS_PATH, scopes=SCOPES)
    doc_infos = get_doc_ids_dates_from_drive(creds)

    # Do the work for each GDoc
    summaries = []
    for doc_id, created_time in doc_infos:
        existing_summary = db.get_summary_from_db(doc_id)
        if existing_summary:
            print(f"Summary exists for {doc_id=}, skipping generation.")
            document = get_doc_from_id(creds, doc_id)
            summaries.append((document["title"], document["documentId"], created_time, existing_summary))
            continue

        document = get_doc_from_id(creds, doc_id)
        contents = document.get("body", {}).get("content", [])
        if not contents:
            print(f"No content found for {doc_id=}")
            continue

        llm_summary = generate_llm_summary(contents)
        db.save_summary_to_db(document["documentId"], document["title"], llm_summary)
        
        summaries.append((document["title"], document["documentId"], created_time, llm_summary))

    for email in constants.TDRB_SUBSCRIBERS:
        print(f"SENDING EMAIL TO: {email}")
        build_and_send_email(email_address=email, summaries=summaries)


if __name__ == "__main__":
    entrypoint()
