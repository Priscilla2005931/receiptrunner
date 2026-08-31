import json
from google import genai
from google.genai import types
from config import PROJECT_ID, LOCATION, GEMINI_MODEL
from schemas import RECEIPT_SCHEMA, UPI_SCHEMA

client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
def extract_receipt(file_bytes: bytes, mime_type: str) -> dict:
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
            "Extract the structured expense data from this receipt. "
            "If any field is illegible or missing, make your best guess and "
            "lower the confidence score accordingly. Categorize using the "
            "closest matching category from the enum."
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=RECEIPT_SCHEMA,
        )
    )
    return json.loads(response.text)


def extract_upi_transaction(subject: str, body_text: str) -> dict:
    prompt = f"""
    Extract structured UPI transaction data from this email.

    Subject: {subject}
    Body: {body_text[:4000]}

    Extract: payee/merchant name, date (YYYY-MM-DD), amount, transaction
    type (paid/received), UPI reference number if present, and best-guess
    expense category. If a field isn't present, omit it or use your best
    judgement. Return JSON only.
    """
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=UPI_SCHEMA,
        )
    )
    return json.loads(response.text)