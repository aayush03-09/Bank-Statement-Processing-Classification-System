import pytest
from app.services.classification.engine import classify_transaction
from app.services.classification.config import CATEGORIES, KEYWORDS
from app.models.transaction import Transaction

# Simple Transaction mock (no DB needed)
class SimpleTransaction:
    def __init__(self, description, category=None, classification_method=None, classification_confidence=None, review_required=False):
        self.original_description = description
        self.normalized_description = description.upper()
        self.category = category
        self.classification_method = classification_method
        self.classification_confidence = classification_confidence
        self.review_required = review_required

# Monkeypatch ML prediction to avoid loading real model
@pytest.fixture(autouse=True)
def mock_ml_prediction(monkeypatch):
    def fake_predict(description):
        # Very simple logic: if 'UNKNOWN' in description -> low confidence
        if 'UNKNOWN' in description:
            return {'category': 'Others / Needs Review', 'confidence': 0.4, 'model_id': 'ml_v1'}
        return {'category': 'Income', 'confidence': 0.9, 'model_id': 'ml_v1'}
    monkeypatch.setattr('app.services.classification.ml_prediction.predict', fake_predict)
    yield

def test_rule_based_match():
    tx = SimpleTransaction('SWIGGY FOOD ORDER')
    result = classify_transaction(tx)
    assert result['category'] == 'Food & Dining'
    assert result['classification_method'] == 'RULE_BASED'
    assert result['matched_rule'] == 'SWIGGY'
    assert not result['review_required']

def test_ml_fallback_low_confidence():
    tx = SimpleTransaction('UNKNOWN MERCHANT')
    result = classify_transaction(tx)
    assert result['category'] == 'Others / Needs Review'
    assert result['classification_method'] == 'ML'
    assert result['confidence'] == 0.4
    assert result['review_required']

def test_ml_fallback_high_confidence():
    tx = SimpleTransaction('SALARY CREDIT')
    result = classify_transaction(tx)
    # Rule matches 'SALARY' -> Income via rule
    assert result['category'] == 'Income'
    assert result['classification_method'] == 'RULE_BASED'
    assert result['matched_rule'] == 'SALARY'
    assert not result['review_required']
