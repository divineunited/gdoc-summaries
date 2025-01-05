"""
Main entrypoint for script to run Gdoc Summaries for Biweekly updates

The logic is as follows:
1. Get the latest section from each document;
    the section is required to be in the format of "--- UPDATE YYYY-MM-DD --- ... "
2. If the section is newer than the last processed section, generate a summary
3. Save the new section and summary to the database
4. Send an email with the new summary
5. Mark the section as sent

This is different than other summaries because it uses the same biweekly documents for all updates.
"""

import logging
from typing import List

from googleapiclient import discovery

from gdoc_summaries.libs import (
    constants,
    db,
    gdoc_client,
    llm,
    section_parser,
    summary_processor,
)

LOGGER = logging.getLogger(__name__)

def _process_document_sections(service, doc_info: constants.DocumentInfo) -> List[str]:
    """Process sections for a single document and return document ID if updated"""
    try:
        document = gdoc_client.get_document_from_id(service, doc_info.document_id)
        latest_section = section_parser.extract_latest_section(document)
        
        if not latest_section:
            raise ValueError(f"No sections found in document {doc_info.document_id}")
            
        last_processed_date = db.get_latest_section_date(doc_info.document_id)
        has_unsent_sections = bool(db.get_unsent_sections(doc_info.document_id))
        has_new_section = not last_processed_date or latest_section.section_date > last_processed_date
        
        if has_new_section:
            print(f"Found new section for document {doc_info.document_id}, generating summary for section:", latest_section.section_date)
            section_summary = llm.generate_llm_summary(latest_section.content)
            db.save_section_to_db(
                document_id=doc_info.document_id,
                section_date=latest_section.section_date,
                section_content=latest_section.raw_content,
                section_summary=section_summary
            )
            
        if has_new_section or has_unsent_sections:
            status = []
            if has_new_section:
                status.append("new sections")
            if has_unsent_sections:
                status.append("unsent sections")
            print(f"Document {doc_info.document_id} has {' and '.join(status)}")
            return [doc_info.document_id]
            
        print(f"No new or unsent sections for document {doc_info.document_id}")
        return []
        
    except Exception as e:
        LOGGER.error(f"Error processing document {doc_info.document_id}: {e}")
        raise e

def _create_biweekly_summary(doc_id: str, document: dict) -> constants.Summary:
    """Create a summary object from unsent sections"""
    unsent_sections = db.get_unsent_sections(doc_id)
    if not unsent_sections:
        return None

    return constants.Summary(
        document_id=doc_id,
        title=document["title"],
        content="\n\n".join([
            f"Update {date}:\n{summary}" 
            for date, summary in unsent_sections
        ]),
        date_published=unsent_sections[0][0],
        summary_type=constants.SummaryType.BIWEEKLY
    )

def process_biweekly_summaries() -> None:
    """Process summaries for biweekly documents"""
    db.setup_database()

    creds = gdoc_client.get_credentials(
        creds_path=constants.CREDS_PATH,
        scopes=gdoc_client.SCOPES
    )
    service = discovery.build("docs", "v1", credentials=creds)
    
    document_infos = constants.get_doc_info(constants.SummaryType.BIWEEKLY)
    documents_with_updates = []

    # Process each document's sections
    for doc_info in document_infos:
        doc_updates = _process_document_sections(service, doc_info)
        documents_with_updates.extend(doc_updates)

    if not documents_with_updates:
        print("No new updates to send - all sections are either processed and sent or up to date")
        return

    # Create summaries for documents with updates
    all_summaries = []
    for doc_id in documents_with_updates:
        document = gdoc_client.get_document_from_id(service, doc_id)
        summary = _create_biweekly_summary(doc_id, document)
        if summary:
            all_summaries.append(summary)

    # Send summaries via email
    if summary_processor.send_summaries(all_summaries, constants.SummaryType.BIWEEKLY):
        for doc_id in documents_with_updates:
            db.mark_sections_as_sent(doc_id)

if __name__ == "__main__":
    process_biweekly_summaries()
