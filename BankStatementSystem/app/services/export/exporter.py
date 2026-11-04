import io
import pandas as pd
from datetime import datetime
from ..models.bank_statement import BankStatement
from ..models.transaction import Transaction
from ..models.processing_issue import ProcessingIssue
from ..extensions import db

# ---------------------------------------------------------------------------
# Helper: protect against Excel formula injection by prefixing a single quote
# for any cell value that starts with =, +, - or @ (common spreadsheet prefixes).
# ---------------------------------------------------------------------------
def _escape_formula(value: str) -> str:
    if isinstance(value, str) and value and value[0] in ('=', '+', '-', '@'):
        return "'" + value
    return value


def export_transactions_csv(statement_id: int, filters: dict | None = None) -> bytes:
    """Return a CSV byte string for the given statement.

    Args:
        statement_id: ID of the BankStatement to export.
        filters: Optional dict of filter criteria (e.g. {'review_required': False}).

    Returns:
        UTF‑8 encoded CSV bytes (with BOM for Excel compatibility).
    """
    stmt = BankStatement.query.get_or_404(statement_id)
    query = Transaction.query.filter_by(statement_id=statement_id)
    if filters:
        for attr, val in filters.items():
            query = query.filter(getattr(Transaction, attr) == val)
    df = pd.read_sql(query.statement, db.session.bind)

    # Rename columns to required export names
    column_map = {
        'id': 'Transaction ID',
        'transaction_date': 'Date',
        'original_description': 'Description',
        'debit_amount': 'Debit',
        'credit_amount': 'Credit',
        'balance': 'Balance',
        'transaction_type': 'Transaction Type',
        'category': 'Category',
        'classification_method': 'Classification Method',
        'classification_confidence': 'Classification Confidence',
        'extraction_method': 'Extraction Method',
        'extraction_confidence': 'Extraction Confidence',
        'review_required': 'Review Status',
    }
    df = df.rename(columns=column_map)

    # Escape potential formula injection in string columns
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].apply(_escape_formula)

    # Ensure proper ordering
    df = df[list(column_map.values())]

    output = io.BytesIO()
    # Write BOM for Excel compatibility
    output.write(b"\xef\xbb\bf")
    df.to_csv(output, index=False, encoding='utf-8')
    return output.getvalue()


def export_transactions_excel(statement_id: int, filters: dict | None = None) -> bytes:
    """Return an Excel workbook (bytes) with the required worksheets.

    Args:
        statement_id: BankStatement to export.
        filters: Optional filter dict for transactions.
    """
    stmt = BankStatement.query.get_or_404(statement_id)
    # ---------------------------------------------------------------------
    # 1. ACCOUNT SUMMARY sheet
    # ---------------------------------------------------------------------
    summary_data = {
        'Bank Name': [stmt.bank_name],
        'Masked Account Number': [stmt.masked_account_number],
        'Account Holder Name': [stmt.account_holder_name],
        'IFSC Code': [stmt.ifsc_code],
        'Account Type': [stmt.account_type],
        'Statement Period': [f"{stmt.statement_start_date} to {stmt.statement_end_date}" if stmt.statement_start_date and stmt.statement_end_date else None],
        'Currency': [stmt.currency],
        'Opening Balance': [stmt.opening_balance],
        'Closing Balance': [stmt.closing_balance],
    }
    df_summary = pd.DataFrame(summary_data)

    # ---------------------------------------------------------------------
    # 2. TRANSACTIONS sheet
    # ---------------------------------------------------------------------
    query = Transaction.query.filter_by(statement_id=statement_id)
    if filters:
        for attr, val in filters.items():
            query = query.filter(getattr(Transaction, attr) == val)
    df_tx = pd.read_sql(query.statement, db.session.bind)
    # Rename columns as in CSV export
    column_map = {
        'id': 'Transaction ID',
        'transaction_date': 'Date',
        'original_description': 'Description',
        'debit_amount': 'Debit',
        'credit_amount': 'Credit',
        'balance': 'Balance',
        'transaction_type': 'Transaction Type',
        'category': 'Category',
        'classification_method': 'Classification Method',
        'classification_confidence': 'Classification Confidence',
        'extraction_method': 'Extraction Method',
        'extraction_confidence': 'Extraction Confidence',
        'review_required': 'Review Status',
    }
    df_tx = df_tx.rename(columns=column_map)
    for col in df_tx.select_dtypes(include=['object']).columns:
        df_tx[col] = df_tx[col].apply(_escape_formula)
    df_tx = df_tx[list(column_map.values())]

    # ---------------------------------------------------------------------
    # 3. CATEGORY SUMMARY sheet
    # ---------------------------------------------------------------------
    category_grp = df_tx.groupby('Category')
    cat_summary = category_grp.agg({
        'Transaction ID': 'count',
        'Debit': 'sum',
        'Credit': 'sum',
    }).reset_index()
    cat_summary = cat_summary.rename(columns={
        'Transaction ID': 'Number of Transactions',
        'Debit': 'Total Debit',
        'Credit': 'Total Credit',
    })

    # ---------------------------------------------------------------------
    # 4. VALIDATION REPORT sheet
    # ---------------------------------------------------------------------
    issues = ProcessingIssue.query.filter(ProcessingIssue.transaction.has(statement_id=statement_id)).all()
    val_data = {
        'Issue ID': [i.id for i in issues],
        'Transaction ID': [i.transaction_id for i in issues],
        'Issue Type': [i.issue_type for i in issues],
        'Severity': [i.severity for i in issues],
        'Description': [i.message for i in issues],
        'Resolution Status': [i.resolution_status for i in issues],
    }
    df_validation = pd.DataFrame(val_data)
    for col in df_validation.select_dtypes(include=['object']).columns:
        df_validation[col] = df_validation[col].apply(_escape_formula)

    # ---------------------------------------------------------------------
    # 5. PROCESSING REPORT sheet
    # ---------------------------------------------------------------------
    proc_report = {
        'PDF Type': [stmt.pdf_type],
        'Detected Bank': [stmt.bank_name],
        'Number of Pages': [stmt.page_count],
        'Extraction Method': [stmt.processing_status],  # placeholder field
        'Classification Models Used': ['Rule + ML'],
        'Processing Status': [stmt.processing_status],
        'Processing Date': [stmt.created_at],
        'Warnings': [stmt.processing_status],  # could be populated from issues
    }
    df_processing = pd.DataFrame(proc_report)

    # ---------------------------------------------------------------------
    # Write to Excel workbook using pandas ExcelWriter (openpyxl engine)
    # ---------------------------------------------------------------------
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_summary.to_excel(writer, sheet_name='Account Summary', index=False)
        df_tx.to_excel(writer, sheet_name='Transactions', index=False)
        cat_summary.to_excel(writer, sheet_name='Category Summary', index=False)
        df_validation.to_excel(writer, sheet_name='Validation Report', index=False)
        df_processing.to_excel(writer, sheet_name='Processing Report', index=False)
        workbook = writer.book
        # Apply basic formatting – frozen header rows & autofilter
        for ws in workbook.worksheets:
            ws.freeze_panes = ws['A2']
            ws.auto_filter.ref = ws.dimensions
            # Set column widths (simple heuristic)
            for column_cells in ws.columns:
                length = max(len(str(cell.value)) if cell.value is not None else 0 for cell in column_cells)
                adjusted = (length + 2)
                ws.column_dimensions[column_cells[0].column_letter].width = adjusted
    return output.getvalue()
