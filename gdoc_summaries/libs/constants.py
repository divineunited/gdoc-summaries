"""
Constants for gdoc summaries

- `tdd_documents.json` is a list of Google Docs that you want to summarize

The format of the JSON is:
{
    "document_data": [
        {
        "url": "https://docs.google.com/document/d/url_of_doc/edit?tab=t.0", 
        "date_published": "date_published_of_doc"
        },
        ...
    ]
}

- `tdd_subscribers.json` is a list of email addresses you want to send to

The format of the JSON is:
{
    "subscribers": [
        "email_address_1",
        "email_address_2",
        ...
    ]
}
"""
import dataclasses
import json
import os
import re
from enum import Enum

AZURE_API_BASE = "https://clover-openai-useast2.openai.azure.com/"
AZURE_API_VERSION = "2023-07-01-preview"
AZURE_MODEL_ENGINE = "gpt-4o"

# TODO: deployment considerations:
CREDS_PATH = os.path.expanduser("~/Downloads/gdoc_summary_files/eng-sandbox-30f6bd0e093d.json")

class SummaryType(Enum):
    TDD = "TDD"
    PRD = "PRD"
    BIWEEKLY = "BIWEEKLY"
    
    def __str__(self):
        return self.value


@dataclasses.dataclass
class DocumentInfo:
    """Contains metadata about a Google Document including its ID and publication date."""
    document_id: str
    date_published: str

@dataclasses.dataclass
class Summary:
    """Contains metadata about a summary including its ID, title, and content."""
    document_id: str
    title: str
    content: str
    date_published: str
    summary_type: SummaryType

def get_tdd_subscribers() -> list[str]:
    """Retrieve the list of subscribers from a JSON file with validation."""
    json_file_path = os.path.expanduser("~/Downloads/gdoc_summary_files/tdd_subscribers.json")

    if not os.path.exists(json_file_path):
        raise FileNotFoundError(f"The subscribers JSON file was not found at {json_file_path}.")

    try:
        with open(json_file_path, "r") as file:
            data = json.load(file)
    except json.JSONDecodeError as e:
        raise ValueError("The JSON file is not parsable. Please check its contents.") from e

    subscribers = data.get("subscribers", [])
    if not subscribers:
        raise ValueError("The subscribers list is empty. Please ensure the JSON file has valid entries.")

    return subscribers

def _extract_doc_info(doc_entry: dict) -> DocumentInfo:
    """Extract document ID and published date from a document entry."""
    url = doc_entry.get("url")
    date_published = doc_entry.get("date_published")
    
    if not url or not date_published:
        raise ValueError(f"Invalid document entry format: {doc_entry}")
    
    if not url.startswith("https://docs.google.com/document/"):
        raise ValueError(f"Invalid Google Docs URL format: {url}")
        
    pattern = r"/document/d/([a-zA-Z0-9_-]+)"
    match = re.search(pattern, url)
    if match:
        return DocumentInfo(document_id=match.group(1), date_published=date_published)
    raise ValueError(f"Could not extract document ID from URL: {url}")

def get_tdd_document_id_and_date() -> list[DocumentInfo]:
    """
    Retrieve document IDs and published dates from a JSON configuration file.
    
    Returns:
        list[DocumentInfo]: List of document metadata including IDs and publication dates
    """
    json_file_path = os.path.expanduser("~/Downloads/gdoc_summary_files/tdd_documents.json")

    if not os.path.exists(json_file_path):
        raise FileNotFoundError(f"The document IDs JSON file was not found at {json_file_path}.")

    try:
        with open(json_file_path, "r") as file:
            data = json.load(file)
    except json.JSONDecodeError as e:
        raise ValueError("The JSON file is not parsable. Please check its contents.") from e

    doc_data = data.get("document_data", [])
    if not doc_data:
        raise ValueError("The documents list is empty. Please ensure the JSON file has valid entries.")

    return [_extract_doc_info(doc) for doc in doc_data]
