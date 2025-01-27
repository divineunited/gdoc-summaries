"""LLM Based tooling"""

import logging
import time
from functools import wraps
from typing import Callable

import markdown
import requests
from azure.identity import DefaultAzureCredential

from gdoc_summaries.libs import constants

LOGGER = logging.getLogger(__name__)


def retry_with_backoff(retries: int, backoff_in_seconds: list[int]) -> Callable:
    """
    Retry decorator with specified backoff times
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for i in range(retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # Don't retry if it's a context length error
                    if "context_length_exceeded" in str(e):
                        raise e
                    
                    if i == retries:  # Last attempt
                        raise e
                    wait_time = backoff_in_seconds[i]
                    print("There was an error:", e)
                    print(f"Attempt {i + 1} failed. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
            return None  # Should never reach here
        return wrapper
    return decorator


@retry_with_backoff(retries=2, backoff_in_seconds=[35, 65])
def _generate_tldr(summary: str) -> str:
    """
    Generate a one-sentence TLDR from a summary using Azure OpenAI.
    
    Args:
        summary: The summary text to create a TLDR from
        
    Returns:
        str: One sentence TLDR
    """
    print("Generating TLDR")
    
    prompt = (
        "Create a single sentence TLDR that captures the most important aspects "
        "of this summary. Keep it concise but informative. The summary is:\n"
        + summary
    )

    data = {
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 100
    }

    credential = DefaultAzureCredential()
    token = credential.get_token("https://cognitiveservices.azure.com/.default").token

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    api_url = f"{constants.AZURE_API_BASE}/openai/deployments/{constants.AZURE_MODEL_ENGINE}/chat/completions?api-version={constants.AZURE_API_VERSION}"
    response = requests.post(api_url, headers=headers, json=data)

    if response.status_code == 200:
        print("Generated TLDR")
        return response.json()["choices"][0]["message"]["content"].strip()
    else:
        print(f"Error in TLDR request: {response.status_code}, {response.text}")
        raise RuntimeError(f"Error in TLDR request: {response.status_code}, {response.text}")


@retry_with_backoff(retries=2, backoff_in_seconds=[35, 65])
def generate_llm_summary(content: str) -> str:
    """
    Generate a summary using Azure OpenAI.
    
    Args:
        content: The text content to summarize
        
    Returns:
        str: HTML formatted summary with TLDR
    """
    print("Generating LLM Summary")
    if not content.strip():
        raise ValueError("No content provided to summarize")

    # Generate main summary first
    prompt = (
        "As a professional summarizer, create a concise "
        "summary of the provided text while adhering to these guidelines:\n"
        "Craft a summary that is detailed, thorough, in-depth, and complex, "
        "while maintaining clarity and conciseness.\n"
        "Incorporate main ideas and essential information, eliminating extraneous "
        "language and focusing on critical aspects.\n"
        "Rely strictly on the provided text, without including external information.\n"
        "Utilize markdown to cleanly format your output. Do not use any header markdowns. " 
        "Only use Bold or Italics for key subject matters that require emphasis.\n"
        "Content is as follows:\n"
        + content
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
        
        # Generate TLDR from the summary
        tldr = _generate_tldr(markdown_content)
        
        # Combine TLDR and summary
        full_content = f"**TLDR:** {tldr}\n\n **Full Summary:** {markdown_content}"
        
        html_content = markdown.markdown(full_content)
        return html_content
    else:
        print(f"Error in LLM request: {response.status_code}, {response.text}")
        raise RuntimeError(f"Error in LLM request: {response.status_code}, {response.text}")
