import pickle
import base64
import os
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from config import RECEIPTS_LABEL, UPI_LABEL, PROCESSED_LABEL
import mimetypes
from html.parser import HTMLParser

class _HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []

    def handle_data(self, data):
        stripped = data.strip()
        if stripped:
            self.text_parts.append(stripped)

    def get_text(self):
        return ' '.join(self.text_parts)


def _strip_html(html_content: str) -> str:
    parser = _HTMLTextExtractor()
    parser.feed(html_content)
    return parser.get_text()

def _guess_mime_type(filename: str, reported_mime: str) -> str:
    """Gmail sometimes reports generic mime types; infer from extension as a fallback."""
    if reported_mime and reported_mime != 'application/octet-stream':
        return reported_mime
    guessed, _ = mimetypes.guess_type(filename)
    return guessed or 'application/pdf'  # default to pdf since that's your common case


def get_gmail_service():
    """
    Local development: reads token.pickle from disk (fast, no cloud round-trip).
    Cloud Function: falls back to Secret Manager, since no local file exists there.
    """
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as f:
            creds = pickle.load(f)
    else:
        from google.cloud import secretmanager
        client = secretmanager.SecretManagerServiceClient()
        name = "projects/receiptrunner-hackathon/secrets/gmail-oauth-token/versions/latest"
        response = client.access_secret_version(request={"name": name})
        creds = pickle.loads(response.payload.data)

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    return build('gmail', 'v1', credentials=creds)


def _get_or_create_label_id(service, label_name: str) -> str:
    """Finds a Gmail label by name, creating it if it doesn't exist yet."""
    labels = service.users().labels().list(userId='me').execute().get('labels', [])
    for lbl in labels:
        if lbl['name'] == label_name:
            return lbl['id']
    new_label = service.users().labels().create(
        userId='me',
        body={'name': label_name, 'labelListVisibility': 'labelShow', 'messageListVisibility': 'show'}
    ).execute()
    return new_label['id']


def mark_as_processed(service, message_id: str):
    """Tags a message so future runs skip it — this is what makes reruns cheap and idempotent."""
    label_id = _get_or_create_label_id(service, PROCESSED_LABEL)
    service.users().messages().modify(
        userId='me', id=message_id,
        body={'addLabelIds': [label_id]}
    ).execute()


def fetch_receipt_attachments(service):
    """Pulls attachment files from emails labeled 'Receipts' that haven't been processed yet."""
    query = f'label:{RECEIPTS_LABEL} has:attachment -label:{PROCESSED_LABEL}'
    results = service.users().messages().list(userId='me', q=query).execute()
    messages = results.get('messages', [])

    items = []
    for msg_meta in messages:
        msg = service.users().messages().get(userId='me', id=msg_meta['id']).execute()
        for part in msg['payload'].get('parts', []) or []:
            if part.get('filename') and part.get('body', {}).get('attachmentId'):
                att = service.users().messages().attachments().get(
                    userId='me', messageId=msg_meta['id'], id=part['body']['attachmentId']
                ).execute()
                file_bytes = base64.urlsafe_b64decode(att['data'])
                items.append({
                        'message_id': msg_meta['id'],
                        'filename': part['filename'],
                        'mime_type': _guess_mime_type(part['filename'], part['mimeType']),
                        'data': file_bytes,
                    })
    return items


def _get_email_body_text(msg):
    payload = msg['payload']
    parts = payload.get('parts', [payload])

    for part in parts:
        mime = part.get('mimeType', '')
        body_data = part.get('body', {}).get('data')
        if body_data and mime in ('text/plain', 'text/html'):
            decoded = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
            if mime == 'text/html':
                decoded = _strip_html(decoded)
            return decoded

    for part in parts:
        if 'parts' in part:
            for sub in part['parts']:
                body_data = sub.get('body', {}).get('data')
                mime = sub.get('mimeType', '')
                if body_data and mime in ('text/plain', 'text/html'):
                    decoded = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
                    if mime == 'text/html':
                        decoded = _strip_html(decoded)
                    return decoded
    return None


def fetch_upi_transaction_emails(service):
    """Pulls body text from emails labeled 'UPI-Transactions' that haven't been processed yet."""
    query = f'label:{UPI_LABEL} -label:{PROCESSED_LABEL}'
    results = service.users().messages().list(userId='me', q=query).execute()
    messages = results.get('messages', [])

    items = []
    for msg_meta in messages:
        msg = service.users().messages().get(userId='me', id=msg_meta['id']).execute()
        subject = next((h['value'] for h in msg['payload']['headers'] if h['name'] == 'Subject'), '')
        body_text = _get_email_body_text(msg)
        items.append({
            'message_id': msg_meta['id'],
            'subject': subject,
            'body': body_text or '',
        })
    return items