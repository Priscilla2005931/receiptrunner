from google.cloud import firestore

db = firestore.Client()

def dedupe_expenses():
    docs = list(db.collection("expenses").stream())
    seen = {}
    to_delete = []

    for doc in docs:
        data = doc.to_dict()
        mid = data.get("message_id")
        if not mid:
            continue
        if mid not in seen:
            seen[mid] = doc
        else:
            # Keep the one with the earliest created_at, delete the rest
            existing_created = seen[mid].to_dict().get("created_at")
            current_created = data.get("created_at")
            if current_created and existing_created and current_created < existing_created:
                to_delete.append(seen[mid].id)
                seen[mid] = doc
            else:
                to_delete.append(doc.id)

    print(f"Found {len(to_delete)} duplicate(s) to delete")
    for doc_id in to_delete:
        db.collection("expenses").document(doc_id).delete()
        print(f"  Deleted {doc_id}")

    print("Done.")

if __name__ == "__main__":
    dedupe_expenses()