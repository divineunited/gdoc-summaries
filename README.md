# gdoc-summaries
Send emails with LLM Summaries of Google Documentations from your Org.

- This script goes through Google Docs via a list of IDs in a file.
- It will summarize the document using an LLM.
- It saves previous summaries into a SQLLite DB so it doesn't have to continue regenerating the same summary.
- This can be run on a daily Cron Job to help folks keep up to date with newly written documentation
- It knows what has been sent already so it doesn't get sent again

- It can send various types of summaries to different groups of people


## For Developers
- Create a python virtual env
- then: `pip install -r requirements.txt`

### Running tests:
- `pytest`

## Running it:
- ensure you have the SENDGRID_API_KEY in your env variables
- have a service account and the google service credentials available to the script
- To reset your DB: `PYTHONPATH=. python gdoc_summaries/reset_database.py`

### TDD Summaries:
- populate the `gdoc_summaries/tdd_documents.json` with the document IDs and publication dates you want to summarize
- populate the `gdoc_summaries/tdd_subscribers.json` with the email addresses you want to send to
- Run it via: `PYTHONPATH=. python gdoc_summaries/tdd_summaries.py`

### PRD Summaries:
- populate the `gdoc_summaries/prd_documents.json` with the document IDs and publication dates you want to summarize
- populate the `gdoc_summaries/prd_subscribers.json` with the email addresses you want to send to
- Run it via: `PYTHONPATH=. python gdoc_summaries/prd_summaries.py`

### Biweekly Summaries:
- populate the `gdoc_summaries/biweekly_documents.json` with the document IDs you want to summarize
- each biweekly document has sections that start with `--- UPDATE YYYY-MM-DD ---`
- the latest section is the one that will be summarized
- populate the `gdoc_summaries/biweekly_subscribers.json` with the email addresses you want to send to
- Run it via: `PYTHONPATH=. python gdoc_summaries/biweekly_summaries.py`
