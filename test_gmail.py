import pickle
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

def get_gmail_service():
    with open('token.pickle', 'rb') as f:
        creds = pickle.load(f)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build('gmail', 'v1', credentials=creds)

service = get_gmail_service()
results = service.users().messages().list(userId='me', q='label:Receipts has:attachment').execute()
messages = results.get('messages', [])
print(f"Found {len(messages)} labeled receipt emails")
for m in messages[:5]:
    msg = service.users().messages().get(userId='me', id=m['id']).execute()
    subject = next((h['value'] for h in msg['payload']['headers'] if h['name'] == 'Subject'), '(no subject)')
    print(f" - {subject}")
    