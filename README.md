# ReceiptRunner

An autonomous AI agent that watches Gmail for receipts and UPI transaction alerts, extracts structured expense data using Gemini, stores it in Firestore, and automatically compiles a monthly PDF expense report — with zero manual data entry.

Built for the **All Things Agentic Hackathon** — Taskmaster track.

## Architecture

```
Gmail (receipts + UPI alerts)
        |
        v
Cloud Scheduler (hourly trigger)
        |
        v
Cloud Function: receiptrunner-extract
   - Fetches unprocessed labeled emails
   - Gemini extracts vendor/amount/date/category
   - Writes structured records to Firestore
   - Labels emails as processed
        |
        v
Firestore (expenses collection)
        |
        v
Cloud Function: receiptrunner-report
   - Aggregates monthly expenses
   - Gemini generates spending insights
   - Renders PDF report
   - Uploads to Cloud Storage
```

## Tech stack

- **Gemini** (via Vertex AI / Google GenAI SDK) — multimodal receipt extraction and UPI transaction parsing
- **Cloud Functions (Gen 2)** — hosts both agents
- **Cloud Scheduler** — triggers extraction autonomously on a recurring basis
- **Firestore** — stores structured expense records
- **Secret Manager** — securely stores Gmail OAuth credentials
- **Cloud Storage** — stores generated PDF reports
- **ReportLab** — generates the PDF reports
- **Gmail API** — reads receipt attachments and UPI notification emails

## Prerequisites

- A Google Cloud project with billing enabled
- `gcloud` CLI installed and authenticated
- Python 3.12
- A Gmail account with:
  - A label applied to receipt emails (see `RECEIPTS_LABEL` in `config.py`)
  - A label applied to UPI transaction emails (see `UPI_LABEL` in `config.py`)

## Local setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/Priscilla2005931/receiptrunner.git
   cd receiptrunner
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\Activate.ps1
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Authenticate with Google Cloud**
   ```bash
   gcloud auth application-default login
   gcloud config set project YOUR_PROJECT_ID
   ```

5. **Set up Gmail OAuth credentials**
   - Create an OAuth Client ID (Desktop app type) in Google Cloud Console under APIs & Services → Credentials
   - Add the Gmail `readonly` (or `modify`) scope on the OAuth consent screen
   - Add your Google account as a test user (the app runs in "Testing" mode — only test users can authorize it)
   - Run `auth_setup.py` to complete the OAuth flow and generate a local token
   - Upload the resulting token and client credentials to Secret Manager:
     ```bash
     gcloud secrets create gmail-oauth-token --data-file=token.pickle
     gcloud secrets create gmail-credentials --data-file=credentials.json
     ```

6. **Configure `config.py`**
   Set `PROJECT_ID`, `LOCATION`, `GEMINI_MODEL`, and your Gmail label names.

7. **Run locally**
   ```bash
   python main_local.py
   python report_generator.py
   ```

## Cloud deployment

1. **Enable required APIs**
   ```bash
   gcloud services enable cloudfunctions.googleapis.com run.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com cloudscheduler.googleapis.com aiplatform.googleapis.com
   ```

2. **Grant IAM roles to the Cloud Functions service account**
   ```bash
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID --member=serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com --role=roles/secretmanager.secretAccessor
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID --member=serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com --role=roles/aiplatform.user
   ```

3. **Deploy the extraction agent**
   ```bash
   gcloud functions deploy receiptrunner-extract --gen2 --runtime=python312 --region=us-central1 --source=. --entry-point=run_extraction --trigger-http --allow-unauthenticated --memory=512MB --timeout=180s
   ```

4. **Deploy the report agent**
   ```bash
   gcloud functions deploy receiptrunner-report --gen2 --runtime=python312 --region=us-central1 --source=. --entry-point=generate_report --trigger-http --allow-unauthenticated --memory=512MB --timeout=180s
   ```

5. **Set up autonomous scheduling**
   ```bash
   gcloud scheduler jobs create http receiptrunner-schedule --schedule="0 * * * *" --uri="YOUR_EXTRACT_FUNCTION_URL" --http-method=POST --location=us-central1
   ```

## Testing it

- Send a receipt (PDF/image attachment) or UPI transaction alert to the labeled Gmail categories
- Trigger the extraction function manually, or wait for the hourly scheduler:
  ```bash
  curl.exe -X POST YOUR_EXTRACT_FUNCTION_URL
  ```
- Check Firestore's `expenses` collection for the new record
- Trigger the report function with a year/month:
  ```bash
  curl.exe -X POST "YOUR_REPORT_FUNCTION_URL?year=2026&month=7"
  ```

## Notes

- The Gmail OAuth app runs in "Testing" mode. Only Google accounts added as test users on the OAuth consent screen can authorize it — this is expected and by design for the hackathon submission, not a bug.
- The pipeline is idempotent: emails are labeled as processed before extraction, and Firestore writes are deduplicated by `message_id`, so repeated runs are safe.
