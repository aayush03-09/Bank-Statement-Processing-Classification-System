from flask import Blueprint, render_template
from ..models.bank_statement import BankStatement
from ..models.transaction import Transaction
from ..models.processing_issue import ProcessingIssue
from ..extensions import db

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
def dashboard():
    # Aggregate metrics
    total_statements = db.session.query(BankStatement).count()
    total_transactions = db.session.query(Transaction).count()
    total_debit = db.session.query(db.func.coalesce(db.func.sum(Transaction.debit_amount), 0)).scalar()
    total_credit = db.session.query(db.func.coalesce(db.func.sum(Transaction.credit_amount), 0)).scalar()
    total_income = db.session.query(db.func.coalesce(db.func.sum(Transaction.credit_amount), 0))\
        .join(BankStatement, Transaction.statement_id == BankStatement.id)\
        .filter(Transaction.category == 'Income').scalar()
    total_expenditure = db.session.query(db.func.coalesce(db.func.sum(Transaction.debit_amount), 0))\
        .join(BankStatement, Transaction.statement_id == BankStatement.id)\
        .filter(Transaction.category != 'Income').scalar()
    review_needed = db.session.query(Transaction).filter(Transaction.review_required.is_(True)).count()
    extraction_warnings = db.session.query(ProcessingIssue).filter(ProcessingIssue.severity == 'warning').count()
    reconciliation_discrepancies = db.session.query(ProcessingIssue).filter(ProcessingIssue.issue_type == 'BALANCE_MISMATCH').count()

    return render_template('dashboard.html', 
        total_statements=total_statements,
        total_transactions=total_transactions,
        total_debit=total_debit,
        total_credit=total_credit,
        total_income=total_income,
        total_expenditure=total_expenditure,
        review_needed=review_needed,
        extraction_warnings=extraction_warnings,
        reconciliation_discrepancies=reconciliation_discrepancies)
