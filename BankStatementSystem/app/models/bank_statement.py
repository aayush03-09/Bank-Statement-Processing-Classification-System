"""BankStatement model.

Represents an uploaded bank statement PDF and its extracted metadata.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, DateTime, Numeric, Enum, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship

from ..extensions import db

class BankStatement(db.Model):
    __tablename__ = "bank_statements"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=True)  # optional, if auth added later
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False, unique=True)
    file_checksum = Column(String(64), nullable=False)
    bank_name = Column(String(128), nullable=True)
    pdf_type = Column(Enum('text', 'image', 'mixed'), nullable=True)
    page_count = Column(Integer, nullable=True)
    account_holder_name = Column(String(255), nullable=True)
    masked_account_number = Column(String(32), nullable=True)
    ifsc_code = Column(String(16), nullable=True)
    account_type = Column(String(64), nullable=True)
    statement_start_date = Column(Date, nullable=True)
    statement_end_date = Column(Date, nullable=True)
    opening_balance = Column(Numeric(precision=20, scale=4), nullable=True)
    closing_balance = Column(Numeric(precision=20, scale=4), nullable=True)
    currency = Column(String(8), nullable=True)
    processing_status = Column(String(32), nullable=False, default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    transactions = relationship('Transaction', back_populates='statement', cascade='all, delete-orphan')
    issues = relationship('ProcessingIssue', back_populates='statement', cascade='all, delete-orphan')
    history = relationship('ProcessingHistory', back_populates='statement', cascade='all, delete-orphan')
