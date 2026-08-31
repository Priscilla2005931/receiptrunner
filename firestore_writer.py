from google.cloud import firestore
from datetime import datetime
db = firestore.Client()


def _is_valid_date(date_str: str) -> bool:
    if not date_str:
        return False
    try:
        parsed = datetime.strptime(date_str, "%Y-%m-%d")
        if parsed.year < 2020 or parsed.year > 2027:
            return False
        return True
    except (ValueError, TypeError):
        return False


def save_expense(extracted: dict, source_type: str, message_id: str, source_file=None):
    existing = db.collection("expenses") \
        .where(filter=firestore.FieldFilter("message_id", "==", message_id)) \
        .limit(1) \
        .stream()
    if any(existing):
        print(f"  ~ Skipping duplicate: {message_id}")
        return

    date_str = extracted.get("date")
    status = "processed" if _is_valid_date(date_str) else "needs_review"

    db.collection("expenses").add({
        **extracted,
        "source_type": source_type,
        "source_file": source_file,
        "message_id": message_id,
        "status": status,
        "created_at": firestore.SERVER_TIMESTAMP,
    })