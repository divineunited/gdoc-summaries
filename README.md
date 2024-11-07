# gdoc-summaries
Send emails with LLM Summaries of Google Documentations from your Org.

- This script scans Google Docs that it has been given access to.
- It will summarize the document using an LLM. - TODO
- It will also summarize the conversation happening in the document. - TODO
- It saves previous summaries into a SQLLite DB so it doesn't have to continue regenerating the same summary. - TODO
- This can be run on a daily Cron Job to help folks keep up to date with newly written documentation


## For Developers
- Create a python virtual env
- then: `pip install -r requirements.txt`
- to run tests: `pytest -k test_run`

## Running it:
- ensure you have the SENDGRID_API_KEY in your env variables
- have your google service credentials available to the script
- Add the service account to the SHARING
- Run it via: `PYTHONPATH=. python gdoc_summaries/run.py`
