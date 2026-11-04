"""Utility functions for normalising dates, amounts and other fields.

All functions return ``None`` when they cannot reliably parse the input –
callers should treat ``None`` as a missing/flagged value.
"""

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

# ---------------------------------------------------------------------------
# Date handling
# ---------------------------------------------------------------------------

_DATE_FORMATS = [
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%Y-%m-%d",
    "%d %b %Y",
    "%d-%b-%y",
    "%d %b %y",
]

def normalize_date(date_str: str) -> str | None:
    """Convert a date string to ``YYYY-MM-DD``.

    Returns ``None`` if the format is not recognised.
    """
    if not date_str:
        return None
    date_str = date_str.strip()
    for fmt in _DATE_FORMATS:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None

# ---------------------------------------------------------------------------
# Amount handling
# ---------------------------------------------------------------------------

# Regex to capture numeric part, handling optional parentheses and sign words
_AMOUNT_RE = re.compile(r"(?P<prefix>\()?\s*(?P<symbol>₹)?\s*(?P<number>[\d,\.]+)\s*(?P<suffix>DR|CR)?\s*(\))?")

def normalize_amount(amount_str: str) -> Decimal | None:
    """Parse a monetary amount string into a ``Decimal``.

    Handles Indian grouping commas, currency symbols, and debit/credit notations.
    Returns ``None`` if parsing fails.
    """
    if not amount_str:
        return None
    amount_str = amount_str.strip()
    match = _ABSENT_RE = _AMOUNT_RE.search(amount_str)
    if not match:
        return None
    num = match.group('number')
    # Remove any commas used as thousand separators
    num = num.replace(',', '')
    # Determine sign
    sign = 1
    if match.group('prefix') == '(' and amount_str.endswith(')'):
        sign = -1
    elif match.group('suffix'):
        suffix = match.group('suffix').upper()
        if suffix == 'DR':
            sign = -1
        elif suffix == 'CR':
            sign = 1
    try:
        dec = Decimal(num) * sign
        return dec
    except InvalidOperation:
        return None

# ---------------------------------------------------------------------------
# Description cleaning
# ---------------------------------------------------------------------------

def clean_description(desc: str) -> str:
    """Normalise whitespace and strip surrounding noise.
    """
    if not desc:
        return ""
    # Collapse multiple spaces/tabs/newlines into a single space
    cleaned = re.sub(r"\s+", " ", desc)
    return cleaned.strip()

# ---------------------------------------------------------------------------
# Account number masking
# ---------------------------------------------------------------------------

def mask_account_number(acc_num: str) -> str | None:
    """Mask an account number, leaving only the last 4 digits visible.
    Returns ``None`` if ``acc_num`` is falsy.
    """
    if not acc_num:
        return None
    # Remove any non‑digit characters for masking, keep original format length
    digits = re.sub(r"\D", "", acc_num)
    if len(digits) <= 4:
        return "X" * len(digits)
    masked = "X" * (len(digits) - 4) + digits[-4:]
    return masked
