"""Common functionality for processing document summaries"""

import logging
from typing import List

from googleapiclient import discovery

from gdoc_summaries.libs import constants, db, email_client, gdoc_client, llm

LOGGER = logging.getLogger(__name__)

def preview_and_confirm_email(summaries: List[constants.Summary], recipients: List[str]) -> bool:
    """Show email preview and get user confirmation"""
    print("\n=== EMAIL PREVIEW ===")
    print(f"Would send {len(summaries)} summaries:")
    for summary in summaries:
        print(f"\nTitle: {summary.title}")
        print(f"Date: {summary.date_published}")
        print(f"Content preview: {summary.content[:200]}...")
    
    print("\nRecipients:")
    for email in recipients:
        print(f"- {email}")
    
    confirmation = input("\nSend these emails? (Y/N): ")
    return confirmation.strip().upper() == "Y"

def send_summaries(summaries: List[constants.Summary], summary_type: constants.SummaryType) -> bool:
    """Send summaries to all subscribers and mark as sent. Returns True if emails were sent."""
    if not summaries:
        print("No summaries to send.")
        return False

    recipients = constants.get_subscribers(summary_type)
    if not preview_and_confirm_email(summaries, recipients):
        print("Aborted sending emails.")
        return False

    for email_address in recipients:
        print(f"Sending email to: {email_address}")
        email_client.build_and_send_email(
            email_address=email_address,
            summaries=summaries,
            summary_type=summary_type
        )

    # Mark as sent after successful sending
    for summary in summaries:
        db.mark_summary_as_sent(summary.document_id)
        
    return True

def process_summaries(summary_type: constants.SummaryType) -> None:
    """Process summaries for a given summary type"""
    db.setup_database()

    creds = gdoc_client.get_credentials(creds_path=constants.CREDS_PATH, scopes=gdoc_client.SCOPES)
    document_infos: List[constants.DocumentInfo] = constants.get_doc_info(summary_type)
    service = discovery.build("docs", "v1", credentials=creds)

    # Do the work for each GDoc
    summaries: List[constants.Summary] = []
    for document_info in document_infos:
        existing_summary = db.get_summary_from_db(document_info.document_id)
        if existing_summary:
            sent_status = db.get_summary_sent_status(document_info.document_id)
            if sent_status == 1:
                print(f"Summary has already been sent for {document_info.document_id=}, skipping.")
                continue
            else:
                print(f"Summary has not been sent for {document_info.document_id=} but exists in the DB. Will send it.")
                summaries.append(existing_summary)
        else:
            try:
                document = gdoc_client.get_document_from_id(service, document_info.document_id)
                document_content = gdoc_client.extract_document_content(document)
                llm_summary = llm.generate_llm_summary(document_content)
                
                summary = constants.Summary(
                    document_id=document_info.document_id,
                    title=document["title"],
                    content=llm_summary,
                    date_published=document_info.date_published,
                    summary_type=summary_type,
                )
                db.save_summary_to_db(summary)
                summaries.append(summary)
            except RuntimeError as e:
                if "context_length_exceeded" in str(e):
                    print(f"Skipping document {document_info.document_id} due to context length exceeded")
                    continue
                raise  # Re-raise other RuntimeErrors

    send_summaries(summaries, summary_type)
