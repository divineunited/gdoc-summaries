"""Parser for biweekly document sections"""

import re
from datetime import datetime
from typing import Optional, Tuple

from gdoc_summaries.libs import constants, gdoc_client


def extract_latest_section(document: dict) -> Optional[constants.DocumentSection]:
    """
    Extract the most recent section from a document.
    
    Args:
        document: The Google Doc document dictionary
        
    Returns:
        Optional[constants.DocumentSection]: The latest section if found, None otherwise
        
    Raises:
        ValueError: If a section contains an invalid date format
    """
    content = gdoc_client.extract_document_content(document)
    if not content:
        return None

    # Find all sections using the custom date delimiter
    section_pattern = r"---\s*UPDATE\s+(\d{4}-\d{2}-\d{2})\s*---\s*(.*?)(?=---\s*UPDATE|\Z)"
    matches = re.finditer(section_pattern, content, re.DOTALL)
    
    latest_section = None
    latest_date = None
    
    for match in matches:
        date_str = match.group(1)
        section_content = match.group(2).strip()
        
        try:
            current_date = datetime.strptime(date_str, "%Y-%m-%d")
            if not latest_date or current_date > latest_date:
                latest_date = current_date
                latest_section = constants.DocumentSection(
                    section_date=date_str,
                    content=section_content,
                    raw_content=match.group(0)
                )
        except ValueError:
            raise ValueError(f"Invalid date format in section: {date_str}. Expected format: YYYY-MM-DD")
    
    return latest_section
