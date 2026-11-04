def predict(description: str):
    """Placeholder ML prediction function.
    This will be monkeypatched in tests. If called without a patch,
    it returns a low‑confidence fallback.
    """
    return {'category': 'Others / Needs Review', 'confidence': 0.0, 'model_id': 'placeholder'}
