from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

creds = None
# Load your credentials from the 'token.json' file
creds = Credentials.from_authorized_user_file("token.json")

# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    flow = InstalledAppFlow.from_client_secrets_file("your_credentials.json", SCOPES)
    creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
        token.write(creds.to_json())

# Call the Docs API
service = build("docs", "v1", credentials=creds)
document = service.documents().get(documentId=document_id).execute()

# Assume the structure of the document is as expected
# (a Heading 2 followed by a Table)
header = document["body"]["content"][1]["paragraph"]["elements"][0]["textRun"][
    "content"
]
table = document["body"]["content"][2]["table"]

# Extract signoff details from the table
for row in table["tableRows"]:
    cells = row["tableCells"]
    name = cells[0]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"]
    signoff = cells[2]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"]

    # If the signoff cell is empty, send an email
    if not signoff.strip():
        email_address = name.split("@")[1]
        send_email(email_address, document["title"], document["documentId"])


def send_email(to, doc_name, doc_id):
    # Use the Gmail API to send an email
    pass
