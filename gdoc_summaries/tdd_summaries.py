"""Main entrypoint for script to run Gdoc Summaries for TDDs"""

import logging

from googleapiclient import discovery

from gdoc_summaries.libs import constants, db, email_client, gdoc_client, llm

LOGGER = logging.getLogger(__name__)

def entrypoint() -> None:
    """Entrypoint for GDoc Summaries"""

    db.setup_database()

    creds = gdoc_client.get_credentials(creds_path=constants.CREDS_PATH, scopes=gdoc_client.SCOPES)
    document_ids = constants.get_document_ids()
    service = discovery.build("docs", "v1", credentials=creds)

    # Do the work for each GDoc
    summaries = []
    for document_id in document_ids:
        existing_summary = db.get_summary_from_db(document_id)
        if existing_summary:
            sent_status = db.get_summary_sent_status(document_id)
            if sent_status == 1:
                print(f"Summary has already been sent for {document_id=}, skipping.")
                continue
            else:
                raise RuntimeError(f"Summary has not been sent for {document_id=}, but it exists in the DB.")

        document = gdoc_client.get_document_from_id(service, document_id)
        llm_summary = llm.generate_llm_summary(document)
        
        db.save_summary_to_db(document["documentId"], document["title"], llm_summary)
        summaries.append((document["title"], document["documentId"], llm_summary))
    
    if not summaries:
        print("No new summaries to send.")
        return

    for email_address in constants.get_subscribers():
        print(f"SENDING EMAIL TO: {email_address}")
        email_client.build_and_send_email(email_address=email_address, summaries=summaries)

    # Mark all processed summaries as sent
    for document in summaries:
        db.mark_summary_as_sent(document[1])


if __name__ == "__main__":
    entrypoint()
