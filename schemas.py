RECEIPT_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "vendor": {"type": "STRING"},
        "date": {"type": "STRING", "description": "ISO 8601 format YYYY-MM-DD"},
        "amount": {"type": "NUMBER"},
        "currency": {"type": "STRING"},
        "category": {
            "type": "STRING",
            "enum": ["Meals & Entertainment", "Travel", "Office Supplies",
                     "Software & Subscriptions", "Utilities", "Transportation",
                     "Health & Wellness", "Government & Legal Fees", "Other"]
        },
        "confidence": {"type": "NUMBER"},
    },
    "required": ["vendor", "date", "amount", "currency", "category", "confidence"]
}

UPI_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "payee": {"type": "STRING"},
        "date": {"type": "STRING", "description": "ISO 8601 format YYYY-MM-DD"},
        "amount": {"type": "NUMBER"},
        "transaction_type": {"type": "STRING", "enum": ["paid", "received"]},
        "upi_ref_number": {"type": "STRING"},
        "category": {
            "type": "STRING",
            "enum": ["Meals & Entertainment", "Travel", "Office Supplies",
                     "Software & Subscriptions", "Utilities", "Transportation",
                     "Health & Wellness", "Government & Legal Fees", "Transfers", "Other"]
        },
        "confidence": {"type": "NUMBER"},
    },
    "required": ["payee", "date", "amount", "transaction_type", "confidence"]
}