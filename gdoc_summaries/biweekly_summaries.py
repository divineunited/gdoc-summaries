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

from googleapiclient import discovery

from gdoc_summaries.libs import (
    constants,
    db,
    email_client,
    gdoc_client,
    llm,
    section_parser,
)

LOGGER = logging.getLogger(__name__)

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

    # Get the latest section from each document, check if it's new
    # if new generate a summary, save the new section and summary to the database
    for doc_info in document_infos:
        try:
            document = gdoc_client.get_document_from_id(service, doc_info.document_id)
            latest_section = section_parser.extract_latest_section(document)
            
            if not latest_section:
                raise ValueError(f"No sections found in document {doc_info.document_id}")
                
            last_processed_date = db.get_latest_section_date(doc_info.document_id)
            
            if last_processed_date and latest_section.section_date <= last_processed_date:
                print(f"No new sections for document {doc_info.document_id}")
                continue

            print("Found new section, generating summary for section:", latest_section.section_date)
            section_summary = llm.generate_llm_summary(latest_section.content)
            db.save_section_to_db(
                document_id=doc_info.document_id,
                section_date=latest_section.section_date,
                section_content=latest_section.raw_content,
                section_summary=section_summary
            )
            
            documents_with_updates.append(doc_info.document_id)
            
        except Exception as e:
            LOGGER.error(f"Error processing document {doc_info.document_id}: {e}")
            raise e

    if not documents_with_updates:
        print("No new updates to send")
        return

    # Send emails for documents with updates
    for email_address in constants.get_subscribers(constants.SummaryType.BIWEEKLY):
        summaries = []
        for doc_id in documents_with_updates:
            unsent_sections = db.get_unsent_sections(doc_id)
            if unsent_sections:
                summary = constants.Summary(
                    document_id=doc_id,
                    title=document["title"],
                    content="\n\n".join([
                        f"Update {date}:\n{summary}" 
                        for date, summary in unsent_sections
                    ]),
                    date_published=unsent_sections[0][0],  # Use latest section date
                    summary_type=constants.SummaryType.BIWEEKLY
                )
                print("Summarized section to send with title and date:", summary.title, summary.date_published)
                summaries.append(summary)

        if summaries:
            print(f"Sending email to: {email_address}")
            email_client.build_and_send_email(
                email_address=email_address,
                summaries=summaries,
                summary_type=constants.SummaryType.BIWEEKLY
            )

    # Finally, mark the sections as sent
    for doc_id in documents_with_updates:
        db.mark_sections_as_sent(doc_id)

if __name__ == "__main__":
    process_biweekly_summaries()
