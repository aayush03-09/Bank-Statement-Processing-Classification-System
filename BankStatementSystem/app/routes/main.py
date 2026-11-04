from flask import Blueprint, render_template, request, flash, redirect, url_for

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def dashboard():
    return render_template('dashboard.html')

@main_bp.route('/upload', methods=['GET', 'POST'])
def upload_statement():
    from ..services.upload_service import handle_upload
    if request.method == 'POST':
        file = request.files.get('statement')
        success, message, statement = handle_upload(file)
        flash(message, 'success' if success else 'danger')
        if success:
            return redirect(url_for('main.statements'))
    return render_template('upload_statement.html')

@main_bp.route('/statements')
def statements():
    from ..models import BankStatement
    statements = BankStatement.query.order_by(BankStatement.created_at.desc()).all()
    return render_template('statements.html', statements=statements)

@main_bp.route('/statement/<int:statement_id>')
def statement_details(statement_id):
    return render_template('statement_details.html', statement_id=statement_id)

@main_bp.route('/transactions')
def transactions():
    return render_template('transactions.html')

@main_bp.route('/analytics')
def analytics():
    return render_template('analytics.html')

@main_bp.route('/review')
def review_queue():
    return render_template('review_queue.html')

@main_bp.route('/reports')
def reports():
    return render_template('reports.html')

@main_bp.route('/settings')
def settings():
    return render_template('settings.html')
