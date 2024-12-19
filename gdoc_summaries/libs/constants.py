"""Constants for gdoc summaries"""
import json
import os
import re

AZURE_API_BASE = "https://clover-openai-useast2.openai.azure.com/"
AZURE_API_VERSION = "2023-07-01-preview"
AZURE_MODEL_ENGINE = "gpt-4o"

# TODO: deployment considerations:
CREDS_PATH = os.path.expanduser("~/Downloads/gdoc_summary_files/eng-sandbox-30f6bd0e093d.json")

def get_subscribers() -> list[str]:
    """Retrieve the list of subscribers from a JSON file with validation."""
    json_file_path = os.path.expanduser("~/Downloads/gdoc_summary_files/subscribers.json")

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

def _extract_doc_info(doc_entry: dict) -> tuple[str, str]:
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
        return match.group(1), date_published
    raise ValueError(f"Could not extract document ID from URL: {url}")

def get_document_id_and_date() -> list[tuple[str, str]]:
    """Retrieve the list of document IDs and their published dates from a JSON file."""
    json_file_path = os.path.expanduser("~/Downloads/gdoc_summary_files/documents.json")

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
