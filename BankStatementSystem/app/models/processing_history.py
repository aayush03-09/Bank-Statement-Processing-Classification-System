"""ProcessingHistory model.

Records operations performed on a BankStatement (e.g., parsing, classification).
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from ..extensions import db

class ProcessingHistory(db.Model):
    __tablename__ = "processing_history"

    id = Column(Integer, primary_key=True)
    statement_id = Column(Integer, ForeignKey('bank_statements.id'), nullable=False, index=True)
    operation = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship back to BankStatement
    statement = db.relationship('BankStatement', back_populates='history')
