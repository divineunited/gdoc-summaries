# gdoc-summaries
Send emails with LLM Summaries of Google Documentations from your Org.

- This script scans Google Docs that it has been given access to.
- It will summarize the document using an LLM.
- It saves previous summaries into a SQLLite DB so it doesn't have to continue regenerating the same summary.
- It sends the most recent document first in the email and you can configure how recent the docs are.
- This can be run on a daily Cron Job to help folks keep up to date with newly written documentation


## For Developers
- Create a python virtual env
- then: `pip install -r requirements.txt`

## Running it:
- ensure you have the SENDGRID_API_KEY in your env variables
- have a service account and the google service credentials available to the script
- Share each doc to the service account in the `Share` UX for the Google Doc
- Run it via: `PYTHONPATH=. python gdoc_summaries/run.py`
