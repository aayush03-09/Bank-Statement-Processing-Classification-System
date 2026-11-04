import os
import secrets
import hashlib
from datetime import datetime
from flask import current_app, flash
import fitz  # PyMuPDF
from werkzeug.utils import secure_filename

from ..extensions import db
from ..models import BankStatement

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def compute_checksum(file_path: str) -> str:
    """Compute SHA‑256 hex digest for the given file."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def validate_pdf(file_path: str) -> dict:
    """Validate PDF integrity.
    Returns dict with keys: valid (bool), page_count (int), encrypted (bool), error (str|None).
    """
    try:
        doc = fitz.open(file_path)
        if doc.is_encrypted:
            return {"valid": False, "error": "PDF is password‑protected.", "encrypted": True, "page_count": 0}
        page_count = doc.page_count
        if page_count == 0:
            return {"valid": False, "error": "PDF contains no pages.", "encrypted": False, "page_count": 0}
        with open(file_path, 'rb') as f:
            header = f.read(5)
            if not header.startswith(b'%PDF'):
                return {"valid": False, "error": "File does not start with PDF signature.", "encrypted": False, "page_count": page_count}
        return {"valid": True, "error": None, "encrypted": False, "page_count": page_count}
    except Exception as e:
        return {"valid": False, "error": f"Corrupted PDF: {str(e)}", "encrypted": False, "page_count": 0}

def store_file(uploaded_file) -> dict:
    """Persist the uploaded file securely and return metadata.
    Returns dict with keys: stored_path, stored_filename, original_filename, checksum.
    """
    upload_root = current_app.instance_path
    uploads_dir = os.path.join(upload_root, 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)

    original_name = secure_filename(uploaded_file.filename)
    ext = os.path.splitext(original_name)[1].lower()
    random_name = secrets.token_urlsafe(16) + ext
    stored_path = os.path.join(uploads_dir, random_name)
    uploaded_file.save(stored_path)
    checksum = compute_checksum(stored_path)
    return {
        'stored_path': stored_path,
        'stored_filename': random_name,
        'original_filename': original_name,
        'checksum': checksum,
    }

def handle_upload(uploaded_file, user_id=None):
    """Full upload pipeline.
    Returns tuple (success: bool, message: str, statement: BankStatement|None).
    """
    if uploaded_file is None or uploaded_file.filename == '':
        return False, 'No file selected.', None

    if not allowed_file(uploaded_file.filename):
        return False, 'Invalid file type. Only PDF files are allowed.', None

    meta = store_file(uploaded_file)
    validation = validate_pdf(meta['stored_path'])
    if not validation['valid']:
        try:
            os.remove(meta['stored_path'])
        except OSError:
            pass
        return False, validation['error'], None

    existing = BankStatement.query.filter_by(file_checksum=meta['checksum'], user_id=user_id).first()
    if existing:
        try:
            os.remove(meta['stored_path'])
        except OSError:
            pass
        return False, 'Duplicate file detected: this statement has already been uploaded.', None

    statement = BankStatement(
        user_id=user_id,
        original_filename=meta['original_filename'],
        stored_filename=meta['stored_filename'],
        file_checksum=meta['checksum'],
        pdf_type='mixed',  # placeholder
        page_count=validation['page_count'],
        processing_status='UPLOADED',
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.session.add(statement)
    db.session.commit()
    return True, 'File uploaded and saved successfully.', statement
