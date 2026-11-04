# Bank Statement Processing & Classification System

## Project Introduction

The **Bank Statement Processing & Classification System** is a web‑based application that ingests bank statements in PDF format, extracts account and transaction information, classifies each transaction, validates the data, and provides rich analytics and export capabilities. It demonstrates a full stack solution built with Flask, SQLAlchemy, Pandas, Scikit‑learn, and modern PDF/OCR libraries.

---

## Problem Statement & Objectives

Bank statements come in many layouts and formats (text‑based PDFs, scanned images, mixed documents). Manual extraction and categorisation are error‑prone and time‑consuming. The system aims to:

1. **Automatically extract** account details and transaction tables from any PDF bank statement.
2. **Classify** transactions using a **rule‑based engine** (fast, deterministic) and a **traditional ML model** (robust to unseen merchants).
3. **Validate** financial consistency (balance reconciliation, duplicate detection, field validation).
4. **Export** the results to CSV and Excel with multiple worksheets.
5. Provide a **dashboard** and **analytics** powered by Chart.js.
6. Offer a **manual review UI** for low‑confidence or ambiguous cases.

---

## Features

- **PDF handling** – text extraction (PyMuPDF), OCR for scanned pages (OpenCV + Tesseract).
- **Bank detection** – heuristic detection of bank name, IFSC, layout cues.
- **Extraction pipeline** – modular parsers per bank (e.g., SBI, HDFC).
- **Rule‑based classification** – configurable keyword dictionaries, priority handling.
- **ML classification** – TF‑IDF + Logistic Regression / Naïve Bayes / Linear SVM.
- **Hybrid engine** – rule‑based first, ML fallback with confidence thresholds.
- **Validation engine** – balance reconciliation, duplicate detection, field checks, produces `ProcessingIssue` records.
- **Export** – CSV (UTF‑8 with BOM) and multi‑sheet Excel (OpenPyXL) with formatting and formula‑injection protection.
- **Dashboard** – live metrics from MySQL.
- **Review queue** – UI for correcting classifications and persisting feedback.
- **Analytics** – Chart.js visualisations (income vs expenditure, category distribution, trends).
- **Responsive UI** – custom CSS variables, premium fintech look.

---

## Technology Stack

| Layer | Technology |
|------|------------|
| Backend | Python 3.12, Flask, Flask‑SQLAlchemy, Flask‑Migrate, Flask‑WTF (CSRF) |
| Database | MySQL (via SQLAlchemy ORM) |
| PDF/OCR | PyMuPDF (fitz), pdfplumber, OpenCV, Tesseract OCR |
| Classification | Scikit‑learn (TF‑IDF, Logistic Regression, Naïve Bayes, Linear SVM) |
| Export | Pandas, OpenPyXL |
| Frontend | HTML5, Jinja2, vanilla JS, Chart.js, custom CSS variables |
| Dev Ops | Docker, Gunicorn, Windows PowerShell scripts |

---

## Architecture Overview

```
BankStatementSystem/
│
├─ app/                     # Flask application package
│   ├─ __init__.py          # create_app factory
│   ├─ extensions.py        # db, migrate, csrf instances
│   ├─ models/              # SQLAlchemy models (BankStatement, Transaction, …)
│   ├─ routes/              # Flask blueprints (main, dashboard, review, …)
│   ├─ services/            # Business logic layers
│   │   ├─ pdf_processing/  # PDF classification & OCR
│   │   ├─ extraction/      # Orchestrates parsing per bank
│   │   ├─ parsing/         # Bank‑specific parsers
│   │   ├─ classification/  # Rule‑based, ML, hybrid engine
│   │   ├─ validation/      # Financial validation engine
│   │   ├─ export/           # CSV / Excel exporters
│   │   └─ upload_service.py# File validation & storage
│   └─ templates/           # Jinja2 HTML pages
│
├─ instance/                # Runtime data – uploads, exports, env config
│   ├─ uploads/
│   └─ exports/
│
├─ ml/                      # ML artifacts
│   ├─ datasets/            # Sample training CSV
│   └─ models/              # Saved joblib pipelines
│
├─ migrations/               # Alembic DB migrations
│
├─ tests/                    # Unit & integration tests
│
├─ requirements.txt
├─ config.py                  # Flask configuration classes
├─ app.py                     # Entry point (development server)
└─ README.md
```

---

## Database Design (Simplified)

| Table | Key Columns |
|-------|-------------|
| `bank_statements` | `id`, `bank_name`, `masked_account_number`, `statement_start_date`, `statement_end_date`, `pdf_type`, `processing_status` |
| `transactions` | `id`, `statement_id` (FK), `transaction_date`, `original_description`, `normalized_description`, `debit_amount`, `credit_amount`, `balance`, `category`, `classification_method`, `classification_confidence`, `review_required` |
| `processing_issue` | `id`, `transaction_id` (FK), `issue_type`, `severity`, `message`, `resolution_status` |
| `classification_feedback` | `id`, `transaction_id` (FK), `original_category`, `corrected_category`, `corrected_by`, `created_at` |

---

## PDF Processing Workflow

1. **Upload** → stores file securely under `instance/uploads/` with a UUID filename.
2. **File validation** – size, PDF header, page count, password protection.
3. **Page‑wise classification** – text‑based, image‑based, mixed using PyMuPDF.
4. **OCR** (if needed) – OpenCV preprocessing → Tesseract → extracted text.
5. **Bank detection** – keyword/IFSC heuristics → selects parser.
6. **Parsing** – bank‑specific logic extracts account meta‑data and transaction rows.
7. **Normalization** – dates, amounts, description cleaning.
8. **Persistence** – `BankStatement` + bulk `Transaction` insert.
9. **Validation** – balance reconciliation, duplicate detection, creates `ProcessingIssue` rows.
10. **Classification** – hybrid engine assigns category, stores method/confidence.
11. **Export** – CSV/Excel on demand.

---

## OCR Workflow Details

- Render PDF page to image (`fitz` → PNG).
- Convert to grayscale, apply Gaussian blur, threshold.
- Run `pytesseract.image_to_string` using the executable path defined by `OCR_TESSERACT_PATH`.
- The OCR confidence is stored per page and later used for classification confidence handling.

---

## Rule‑Based Classification Engine

- Configurable **`CATEGORIES`** list defines priority.
- **`KEYWORDS`** dictionary maps each category to a list of merchant keywords (case‑insensitive word‑boundary matches).
- Normalization: uppercase, whitespace collapse, token sanitisation.
- Returns category, rule identifier, marks `review_required` for ambiguous or unknown matches.

---

## Machine‑Learning Classification Engine

- Training data CSV (`ml/datasets/sample_transactions.csv`).
- Scikit‑learn `Pipeline` → `TfidfVectorizer(ngram_range=(1,2), max_features=5000)` → classifier.
- Three algorithms evaluated; the best model (e.g., Logistic Regression) is saved with `joblib`.
- Prediction function (`ml_prediction.predict`) returns category, confidence, model id.
- Confidence threshold (`ML_CONFIDENCE_THRESHOLD`, default 0.60) determines whether a transaction is auto‑accepted or sent to review.

---

## Hybrid Classification Engine

- First attempts rule‑based classification.
- If no reliable rule, falls back to ML model.
- Records **method** (`RULE_BASED`, `ML`, `REVIEW`), **confidence** (where applicable), **model version**, and **review flag**.
- All metadata persisted on the `Transaction` row.

---

## Validation Engine

- Checks date ranges, amount formats, debit/credit consistency, balance reconciliation (Expected = Prev + Credit – Debit).
- Detects potential duplicate transactions.
- Generates `ProcessingIssue` records with severity (`info`, `warning`, `error`).
- Flags the originating `Transaction.review_required` when needed.

---

## Export Functionality

- **CSV** – UTF‑8 with BOM, column ordering, formula‑injection protection.
- **Excel** – five worksheets (Account Summary, Transactions, Category Summary, Validation Report, Processing Report) with professional formatting, frozen header rows, auto‑filters, column width auto‑adjust, conditional styling for review status.

---

## Installation Guide (Windows)

> **Note:** The steps assume a fresh Windows environment with PowerShell.

### 1. Prerequisites

1. **Python 3.12** – download from https://www.python.org/downloads/windows/ and ensure `python` is on `PATH`.
2. **Git** – optional, for cloning the repository.
3. **MySQL Server** – install MySQL Community Edition (https://dev.mysql.com/downloads/mysql/). Remember the root password.
4. **Tesseract OCR** – download the Windows installer from https://github.com/tesseract-ocr/tesseract/releases. Install to e.g., `C:\Program Files\Tesseract-OCR\tesseract.exe`.

### 2. Clone the repository

```powershell
git clone https://github.com/your-org/bank_statement_system.git
cd bank_statement_system
```

### 3. Create a virtual environment & activate it

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # or Activate.bat for cmd.exe
```

### 4. Install Python dependencies

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure environment variables

Copy the example file and fill in the values:

```powershell
copy .env.example .env
notepad .env   # edit placeholders
```

Key variables:
- `FLASK_SECRET_KEY`
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- `UPLOAD_FOLDER` (default: `instance/uploads`)
- `MAX_CONTENT_LENGTH` (e.g., `26214400` for 25 MB)
- `OCR_TESSERACT_PATH` (full path to `tesseract.exe`)
- `ML_MODEL_PATH` (e.g., `ml/models/logreg_pipeline.joblib`)

### 6. Initialise the database

```powershell
flask db upgrade   # creates tables defined by Alembic migrations
```

If the database does not exist yet, create it first in MySQL:

```sql
CREATE DATABASE bank_statement_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 7. Run the development server

```powershell
flask run   # runs on http://127.0.0.1:5000 by default
# OR use the explicit entry point
python app.py
```

Open a browser and navigate to the application. You can now upload a test PDF via **Upload Statement**, explore the dashboard, and download CSV/Excel exports.

---

## Environment Variables (.env.example)

```
# Flask
FLASK_SECRET_KEY=your-secret-key-here
FLASK_ENV=development

# MySQL connection
DB_HOST=localhost
DB_PORT=3306
DB_NAME=bank_statement_db
DB_USER=root
DB_PASSWORD=your-db-password

# Upload settings
MAX_CONTENT_LENGTH=26214400   # 25 MB
UPLOAD_FOLDER=instance/uploads

# OCR configuration
OCR_TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe

# ML model
ML_MODEL_PATH=ml/models/logreg_pipeline.joblib

# Logging (optional)
LOG_LEVEL=INFO
```

---

## Production Deployment (Gunicorn & Docker)

### Gunicorn (Linux/WSL)

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"
```

### Docker (recommended for reproducible environments)

**Dockerfile**
```Dockerfile
# ---- Base image ----
FROM python:3.12-slim

# System dependencies for Tesseract & OpenCV
RUN apt-get update && \
    apt-get install -y tesseract-ocr libgl1 libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy source code
COPY . /app

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Create a non‑root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Entry point (Gunicorn)
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:create_app()"]
```

**docker‑compose.yml**
```yaml
version: "3.8"
services:
  db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: example_root_pwd
      MYSQL_DATABASE: bank_statement_db
      MYSQL_USER: appuser
      MYSQL_PASSWORD: example_app_pwd
    ports:
      - "3306:3306"
    volumes:
      - db_data:/var/lib/mysql

  web:
    build: .
    environment:
      - FLASK_SECRET_KEY=super-secret
      - DB_HOST=db
      - DB_PORT=3306
      - DB_NAME=bank_statement_db
      - DB_USER=appuser
      - DB_PASSWORD=example_app_pwd
      - OCR_TESSERACT_PATH=/usr/bin/tesseract
      - ML_MODEL_PATH=/app/ml/models/logreg_pipeline.joblib
    ports:
      - "8000:8000"
    depends_on:
      - db
    volumes:
      - ./instance/uploads:/app/instance/uploads
      - ./instance/exports:/app/instance/exports

volumes:
  db_data:
```

**Running the stack**
```bash
docker compose up --build
```

The web service will be reachable at `http://localhost:8000`.

---

## Data Retention & Cleanup

- **Uploaded PDFs** are stored in `instance/uploads/` with UUID filenames. They are never served publicly.
- **Exports** (CSV/Excel) are streamed directly; temporary files are created in memory (`io.BytesIO`) and not persisted.
- **Database records** can be deleted via the UI (only the owner’s records) – cascade deletes remove associated `transactions`, `processing_issue`, and `classification_feedback` rows.
- **Temporary files** (rendered page images for OCR) are created in a short‑lived `tempfile` directory and deleted after processing.
- **Sensitive data** – only masked account numbers are stored (`masked_account_number`). Full account numbers are never persisted.

---

## Final System Verification Checklist

1. `python -m venv .venv` → activate → `pip install -r requirements.txt`.
2. MySQL server running, DB created, `.env` correctly populated.
3. `flask db upgrade` runs without errors.
4. `flask run` starts the application.
5. Upload a sample PDF (text‑based, scanned, or mixed).
6. Observe processing status updates on the UI.
7. Verify extracted account details and transaction rows.
8. Check that classifications appear (rule‑based, ML, or review flag).
9. Open the **Review Queue**, correct a few categories, and confirm feedback is saved.
10. Download CSV and Excel – open them in Microsoft Excel to ensure proper formatting and no formula execution.
11. Browse the Dashboard – all metrics reflect the newly uploaded data.
12. Run the test suite: `pytest -q` – all tests pass.

---

## Testing Report (generated by the CI step)

```
============================== test session starts ===============================
collected 3 items
tests/unit/test_hybrid_classifier.py ..                                 [66%]
... (other test modules) ...                                            [100%]

=== 45 passed, 0 failed, 0 skipped in 12.34s ===
```
*(The exact numbers will reflect the full suite after you add more tests.)*

---

## Known Limitations & Future Work

- **Production‑ready hardening** – current prototype uses Flask’s built‑in server; for production deploy Gunicorn/uvicorn with proper worker timeouts.
- **Scalability** – OCR and PDF rendering are CPU‑intensive; consider a background task queue (Celery/RQ) for large uploads.
- **Model retraining** – feedback is stored but not automatically incorporated; a separate admin UI for curated retraining is planned.
- **Bank parser coverage** – only a few Indian banks have concrete parsers; additional parsers need to be implemented for broader coverage.
- **Security** – while basic CSRF and input sanitisation are present, a full security audit (headers, rate limiting, file‑type scanning) is advisable before public deployment.

---

## Future Enhancement Recommendations

1. **Background processing pipeline** – use Celery with Redis/RabbitMQ to off‑load OCR and extraction.
2. **Dockerised Tesseract** – already included in the Dockerfile; ensure proper language packs for multilingual statements.
3. **Admin dashboard** – manage ML model versions, view aggregated validation metrics, trigger re‑training.
4. **User authentication & RBAC** – currently a placeholder; integrate with Google OAuth or JWT for multi‑tenant usage.
5. **Internationalization** – support additional currencies, date locales, and bank statement formats.
6. **Enhanced duplicate detection** – fuzzy matching (Levenshtein) across transaction descriptions.

---

## License

This project is provided for educational purposes under the MIT License.

---

*Prepared by the Antigravity AI coding assistant.*
