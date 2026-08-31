# Central place for project settings — edit PROJECT_ID to match your actual GCP project ID
PROJECT_ID = "receiptrunner-hackathon"   # <-- check exact ID in GCP Console top bar
LOCATION = "global"
GEMINI_MODEL = "gemini-3.5-flash"       # verify this is still current in Model Garden

RECEIPTS_LABEL = "Receipts"
UPI_LABEL = "UPI-Transactions"
PROCESSED_LABEL = "RR-Processed"         # tracks what the agent has already handled