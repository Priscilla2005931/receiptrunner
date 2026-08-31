from google.cloud import firestore

db = firestore.Client()
docs = db.collection("expenses").stream()

dates = sorted(set(d.to_dict().get("date", "MISSING") for d in docs))
print("Distinct dates in your data:")
for d in dates:
    print(f"  {d}")