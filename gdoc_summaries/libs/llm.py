"""LLM Based tooling"""

import logging

import markdown
import requests
from azure.identity import DefaultAzureCredential

from gdoc_summaries.libs import constants

LOGGER = logging.getLogger(__name__)


def generate_llm_summary(document: dict) -> str:
    """Generate a summary of the document content using Azure OpenAI"""

    print("Generating LLM Summary")
    contents = document.get('body', {}).get('content', [])
    if not contents:
        raise ValueError(f"No content found for doc: {document.get('title')}")

    prompt = (
        "As a professional summarizer, create a concise "
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
