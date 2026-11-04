import re
from typing import Dict
from flask import current_app

# Simple heuristics for bank detection
# Returns a dict:
#   {
#       "bank": str or None,
#       "method": str,
#       "confidence": float (0-1),
#       "parser_available": bool
#   }

def detect_bank(extracted_text: str) -> Dict[str, object]:
    """Detect the bank name from the full extracted PDF text.

    The function applies a series of lightweight heuristics:
    * Presence of known bank full names or common abbreviations.
    * IFSC code pattern – the first four letters often identify the bank.
    * Specific heading keywords that appear in Indian bank statements.

    Confidence is a simple heuristic score (0‑1). The highest‑scoring
    candidate is returned. If no evidence is found, ``bank`` is ``None``
    and ``parser_available`` is ``False``.
    """
    # Normalise text for matching
    text = extracted_text.lower()

    # Known banks and associated keywords (lower‑case)
    bank_keywords = {
        "sbi": ["state bank of india", "sbi", "sbi bank"],
        "hdfc": ["hdfc bank", "hdfc"],
        "icici": ["icici bank", "icici"],
        "axis": ["axis bank", "axis"],
        "kotak": ["kotak mahindra bank", "kotak"],
        "baroda": ["bank of baroda", "baroda"]
    }

    # IFSC pattern – first four letters identify the bank (common mapping)
    ifsc_pattern = re.compile(r"([A-Z]{4})0[0-9A-Z]{6}")
    matches = ifsc_pattern.findall(extracted_text.upper())
    if matches:
        # Use the first IFSC prefix as evidence
        prefix = matches[0]
        ifsc_map = {
            "SBIN": "sbi",
            "HDFC": "hdfc",
            "ICIC": "icici",
            "UTIB": "axis",  # Axis Bank IFSC often starts with UTIB
            "KKBK": "kotak",
            "BARB": "baroda"
        }
        bank_from_ifsc = ifsc_map.get(prefix)
    else:
        bank_from_ifsc = None

    best_bank = None
    best_conf = 0.0
    method_used = None

    # Evaluate keyword matches
    for bank, kws in bank_keywords.items():
        hits = sum(1 for kw in kws if kw in text)
        if hits:
            conf = min(1.0, hits / len(kws) * 0.6)  # up to 0.6 confidence from keywords
            if conf > best_conf:
                best_conf = conf
                best_bank = bank
                method_used = "keywords"

    # Evaluate IFSC evidence – gives up to 0.4 additional confidence
    if bank_from_ifsc:
        conf = 0.4
        if best_bank == bank_from_ifsc:
            best_conf = min(1.0, best_conf + conf)
        elif conf > best_conf:
            best_conf = conf
            best_bank = bank_from_ifsc
            method_used = "ifsc"

    # If nothing matched, fallback to generic
    if not best_bank:
        method_used = "generic"

    parser_available = best_bank in {"sbi", "hdfc", "icici", "axis", "kotak", "baroda"}

    return {
        "bank": best_bank,
        "method": method_used,
        "confidence": best_conf,
        "parser_available": parser_available
    }
}