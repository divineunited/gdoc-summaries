"""Constants for gdoc summaries"""
import json
import os

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
