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

def extract_document_content(document: dict) -> str:
    """
    Extract plain text content from a Google Doc document structure.
    
    Args:
        document: The Google Doc document dictionary
        
    Returns:
        str: Plain text content of the document
    """
    content = []
    for element in document.get("body", {}).get("content", []):
        if "paragraph" in element:
            for item in element["paragraph"].get("elements", []):
                if "textRun" in item:
                    content.append(item["textRun"].get("content", ""))
    
    return "".join(content)
