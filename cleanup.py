from google.cloud import firestore

db = firestore.Client()
docs = db.collection("expenses").where("payee", "in", ["Unknown", "UNKNOWN", "Not Found", None]).stream()

count = 0
for doc in docs:
    doc.reference.delete()
    count += 1

print(f"Deleted {count} bad records")