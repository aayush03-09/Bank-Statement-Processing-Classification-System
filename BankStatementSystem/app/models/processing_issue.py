"""ProcessingIssue model.

Tracks any problems encountered while processing a statement or a
specific transaction.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from ..extensions import db

class ProcessingIssue(db.Model):
    __tablename__ = "processing_issues"

    id = Column(Integer, primary_key=True)
    statement_id = Column(Integer, ForeignKey('bank_statements.id'), nullable=False, index=True)
    transaction_id = Column(Integer, ForeignKey('transactions.id'), nullable=True, index=True)
    issue_type = Column(String(64), nullable=False)
    severity = Column(String(32), nullable=False)
    message = Column(Text, nullable=False)
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    statement = db.relationship('BankStatement', back_populates='issues')
    transaction = db.relationship('Transaction', back_populates='issues', uselist=False)
