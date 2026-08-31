import functions_framework
from gmail_client import get_gmail_service, fetch_receipt_attachments, fetch_upi_transaction_emails, mark_as_processed
from extraction import extract_receipt, extract_upi_transaction
from firestore_writer import save_expense

@functions_framework.http
def run_extraction(request):
    service = get_gmail_service()

    receipts = fetch_receipt_attachments(service)
    processed_count = 0
    for r in receipts:
        try:
            extracted = extract_receipt(r['data'], r['mime_type'])
            save_expense(extracted, "receipt_attachment", r['message_id'], r['filename'])
            mark_as_processed(service, r['message_id'])
            processed_count += 1
        except Exception as e:
            print(f"Failed on {r['filename']}: {e}")

    upi_emails = fetch_upi_transaction_emails(service)
    for u in upi_emails:
        try:
            extracted = extract_receipt(r['data'], r['mime_type'])
            save_expense(extracted, "receipt_attachment", r['message_id'], r['filename'])
            mark_as_processed(service, r['message_id'])
            processed_count += 1
        except Exception as e:
            print(f"Failed on {u['subject'][:50]}: {e}")

    return {"status": "success", "processed": processed_count}, 200