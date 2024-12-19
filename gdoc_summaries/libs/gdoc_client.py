"""Google Doc Wrapper"""

import logging

from google import auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

LOGGER = logging.getLogger(__name__)

# This script needs scope access to the Docs and Drive and Email APIs
SCOPES = [
    "https://www.googleapis.com/auth/documents.readonly",
    "https://www.googleapis.com/auth/drive.metadata.readonly",
]


def get_credentials(creds_path: str, scopes: list[str]) -> Credentials:
    """Get Google API Credentials"""
    creds, _ = auth.load_credentials_from_file(creds_path, scopes=scopes)

    # If the credentials are invalid (e.g., expired), refresh them
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

    return creds

def get_document_from_id(service, document_id) -> dict:
    """Gets the content and metadata of a Google Doc."""
    try:
        document = service.documents().get(documentId=document_id).execute()
        print(f"Retrieved Document: {document.get('title')}")
        return document

    except Exception as e:
        print(f"An error occurred: {e}")
        raise e
