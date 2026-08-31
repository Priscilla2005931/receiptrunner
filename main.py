import functions_framework
from gmail_client import get_gmail_service, fetch_receipt_attachments, fetch_upi_transaction_emails, mark_as_processed
from extraction import extract_receipt, extract_upi_transaction
from firestore_writer import save_expense

@functions_framework.http
def run_extraction(request):
    service = get_gmail_service()

    receipts = fetch_receipt_attachments(service)
    print(f"Found {len(receipts)} new receipt attachment(s)")
    processed_count = 0
    for r in receipts:
        try:
            extracted = extract_receipt(r['data'], r['mime_type'])
            save_expense(extracted, "receipt_attachment", r['message_id'], r['filename'])
            mark_as_processed(service, r['message_id'])
            processed_count += 1
            print(f"  OK {r['filename']} -> {extracted.get('vendor')} {extracted.get('amount')}")
        except Exception as e:
            print(f"  FAIL {r['filename']}: {e}")

    upi_emails = fetch_upi_transaction_emails(service)
    print(f"Found {len(upi_emails)} new UPI transaction email(s)")
    for u in upi_emails:
        try:
            extracted = extract_upi_transaction(u['subject'], u['body'])
            save_expense(extracted, "upi_transaction", u['message_id'])
            mark_as_processed(service, u['message_id'])
            processed_count += 1
            print(f"  OK {u['subject'][:50]} -> {extracted.get('payee')} {extracted.get('amount')}")
        except Exception as e:
            print(f"  FAIL {u['subject'][:50]}: {e}")

    return {"status": "success", "processed": processed_count}, 200