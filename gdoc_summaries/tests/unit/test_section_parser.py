"""
Unit tests for section_parser.py
"""

from gdoc_summaries.libs import constants, section_parser


def test_extract_latest_section(biweekly_document):
    """Test extracting the latest section from a biweekly document"""
    result = section_parser.extract_latest_section(biweekly_document)
    
    assert isinstance(result, constants.DocumentSection)
    assert result.section_date == "2024-03-15"
    assert "Latest update content" in result.content
    assert "--- UPDATE 2024-03-15 ---" in result.raw_content

def test_extract_latest_section_empty_document():
    """Test handling empty document"""
    empty_doc = {"body": {"content": []}}
    result = section_parser.extract_latest_section(empty_doc)
    assert result is None
