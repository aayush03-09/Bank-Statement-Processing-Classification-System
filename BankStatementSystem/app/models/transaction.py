"""Transaction model.

Represents a single financial transaction extracted from a bank statement.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, DateTime, Numeric, Enum, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship

from ..extensions import db

class Transaction(db.Model):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    statement_id = Column(Integer, ForeignKey('bank_statements.id'), nullable=False, index=True)
    transaction_date = Column(Date, nullable=True, index=True)
    original_description = Column(Text, nullable=True)
    normalized_description = Column(Text, nullable=True)
    debit_amount = Column(Numeric(precision=20, scale=4), nullable=True)
    credit_amount = Column(Numeric(precision=20, scale=4), nullable=True)
    balance = Column(Numeric(precision=20, scale=4), nullable=True)
    currency = Column(String(8), nullable=True)
    transaction_type = Column(String(32), nullable=True)
    category = Column(String(64), nullable=True)
    classification_method = Column(Enum('rule', 'ml', 'review'), nullable=True)
    classification_confidence = Column(Numeric(precision=5, scale=4), nullable=True)
    extraction_method = Column(Enum('text', 'ocr'), nullable=True)
    extraction_confidence = Column(Numeric(precision=5, scale=4), nullable=True)
    transaction_reference = Column(String(255), nullable=True)
    page_number = Column(Integer, nullable=True)
    sequence_number = Column(Integer, nullable=True)
    review_required = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    statement = relationship('BankStatement', back_populates='transactions')
    feedback = relationship('ClassificationFeedback', back_populates='transaction', uselist=False, cascade='all, delete-orphan')
    issues = relationship('ProcessingIssue', back_populates='transaction', cascade='all, delete-orphan')
