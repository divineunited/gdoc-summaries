# gdoc-summaries
Send emails with LLM Summaries of Google Documentations from your Org.

- This script goes through Google Docs via a list of IDs in a file.
- It will summarize the document using an LLM.
- It saves previous summaries into a SQLLite DB so it doesn't have to continue regenerating the same summary.
- This can be run on a daily Cron Job to help folks keep up to date with newly written documentation
- It knows what has been sent already so it doesn't get sent again


## For Developers
- Create a python virtual env
- then: `pip install -r requirements.txt`

## Running it:
- ensure you have the SENDGRID_API_KEY in your env variables
- have a service account and the google service credentials available to the script
- Share each doc to the service account in the `Share` UX for the Google Doc
- Run it via: `PYTHONPATH=. python gdoc_summaries/tdd_summaries.py`
- To reset your DB: `PYTHONPATH=. python gdoc_summaries/reset_database.py`
