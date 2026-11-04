"""Rule‑based classification configuration.

This module defines:
- ``CATEGORIES`` – ordered list that also determines rule priority.
- ``KEYWORDS`` – mapping from category to a list of merchant keywords.
- ``ML_CONFIDENCE_THRESHOLD`` – configurable confidence cutoff for the ML fallback.
"""

# ---------------------------------------------------------------------------
# Ordered categories – earlier entries have higher priority when matching rules.
# ---------------------------------------------------------------------------
CATEGORIES = [
    "Food & Dining",
    "Shopping",
    "Transportation",
    "Entertainment",
    "Healthcare",
    "Utilities",
    "Education",
    "Income",
    "Transfers",
    "Cash Withdrawal",
    "Bank Charges",
    "Refunds",
    "Loan Payments",
    "Investment",
    "Others / Needs Review",
]

# ---------------------------------------------------------------------------
# Confidence threshold for ML predictions (default 0.60). Can be overridden via
# the ``ML_CONFIDENCE_THRESHOLD`` environment variable.
# ---------------------------------------------------------------------------
import os
ML_CONFIDENCE_THRESHOLD = float(os.getenv("ML_CONFIDENCE_THRESHOLD", "0.60"))

# ---------------------------------------------------------------------------
# Keyword dictionaries – simple word‑boundary matches (case‑insensitive).
# ---------------------------------------------------------------------------
KEYWORDS = {
    "Food & Dining": ["SWIGGY", "ZOMATO", "DOMINOS", "RESTAURANT"],
    "Shopping": ["AMAZON", "FLIPKART", "MYNTRA"],
    "Transportation": ["UBER", "OLA", "PETROL", "FUEL"],
    "Entertainment": ["NETFLIX", "SPOTIFY"],
    "Healthcare": ["HOSPITAL", "CLINIC", "PHARMACY"],
    "Utilities": ["ELECTRICITY", "GAS BILL", "WATER BILL"],
    "Education": ["TUITION", "UNIVERSITY", "COURSE"],
    "Income": ["SALARY", "INTEREST CREDIT"],
    "Transfers": ["NEFT", "IMPS", "RTGS", "UPI"],
    "Cash Withdrawal": ["ATM", "CASH WITHDRAWAL"],
    "Bank Charges": ["SERVICE CHARGE", "BANK CHARGE"],
    "Refunds": ["REFUND", "REVERSAL"],
    "Loan Payments": ["LOAN PAYMENT", "EMI"],
    "Investment": ["MUTUAL FUND", "ETF", "STOCK"],
    "Others / Needs Review": [],
}
