import re
import os

from .config import CATEGORIES, KEYWORDS, ML_CONFIDENCE_THRESHOLD

# Lazy load ML prediction function – may be missing during tests.
# We import the predict function at call time so that pytest monkeypatch can replace it.
#
# def _load_ml_predict():
#     try:
#         from .ml_prediction import predict  # noqa: F401
#         return predict
#     except Exception:
#         return None
#
# # Lazy load ML predict inside classify_transaction to allow monkeypatching.
# _ml_predict = _load_ml_predict()

def _load_ml_predict():
    try:
        from .ml_prediction import predict  # noqa: F401
        return predict
    except Exception:
        return None

# Lazy load ML predict inside classify_transaction to allow monkeypatching.
# _ml_predict = _load_ml_predict()

def _match_rule(description: str):
    """Return (category, matched_keyword) if a rule matches, else (None, None).
    Word‑boundary, case‑insensitive matching based on the ordered CATEGORIES list.
    """
    desc = description.upper()
    for cat in CATEGORIES:
        for keyword in KEYWORDS.get(cat, []):
            pattern = r"\b" + re.escape(keyword.upper()) + r"\b"
            if re.search(pattern, desc):
                return cat, keyword
    return None, None

def classify_transaction(transaction):
    """Hybrid classification for a ``Transaction``‑like object.

    Parameters
    ----------
    transaction: object
        Must expose ``original_description`` and ``normalized_description``.

    Returns
    -------
    dict with keys:
        - category
        - classification_method ('RULE_BASED', 'ML', 'REVIEW')
        - confidence (float or None)
        - matched_rule (keyword or None)
        - review_required (bool)
    """
    # Use the normalized description if present, otherwise fallback to original.
    description = getattr(transaction, "normalized_description", None) or getattr(transaction, "original_description", "")
    description = description.upper()

    # 1️⃣ Rule‑based classification
    category, rule = _match_rule(description)
    if category:
        return {
            "category": category,
            "classification_method": "RULE_BASED",
            "confidence": None,
            "matched_rule": rule,
            "review_required": False,
        }

    # 2️⃣ ML fallback – if model not available, force review.
    try:
        from .ml_prediction import predict as ml_predict  # noqa: F401
    except Exception:
        ml_predict = None
    if not ml_predict:
        return {
            "category": "Others / Needs Review",
            "classification_method": "REVIEW",
            "confidence": None,
            "matched_rule": None,
            "review_required": True,
        }
    ml_result = ml_predict(description)
    if not ml_result:
        return {
            "category": "Others / Needs Review",
            "classification_method": "REVIEW",
            "confidence": None,
            "matched_rule": None,
            "review_required": True,
        }
    conf = ml_result.get("confidence")
    cat = ml_result.get("category", "Others / Needs Review")
    review = conf is None or conf < ML_CONFIDENCE_THRESHOLD
    return {
        "category": cat,
        "classification_method": "ML",
        "confidence": conf,
        "matched_rule": None,
        "review_required": review,
    }
