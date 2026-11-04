"""ClassificationFeedback model.

Stores user corrections for transaction categories.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from ..extensions import db

class ClassificationFeedback(db.Model):
    __tablename__ = "classification_feedback"

    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey('transactions.id'), nullable=False, index=True)
    original_category = Column(String(64), nullable=True)
    corrected_category = Column(String(64), nullable=False)
    corrected_by = Column(String(255), nullable=True)  # could be username or system id
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship back to Transaction
    transaction = db.relationship('Transaction', back_populates='feedback')
