@echo off
rem ------------------------------------------------------------
rem  Launch Bank Statement Processing & Classification System
rem ------------------------------------------------------------

cd /d "%~dp0BankStatementSystem"
if not exist ".venv\Scripts\activate.bat" (
    echo Virtual environment not found. Please ensure .venv exists.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat
python app.py
pause
