"""Configuration classes for the Bank Statement Processing System.

Environment variables are loaded via python-dotenv in the Flask app
via ``app.config.from_pyfile('config.py', silent=True)``.
"""

import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class BaseConfig:
    """Base configuration with defaults shared by all environments."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'change-me-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Session lifetime
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    # Upload settings
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25 MB limit
    UPLOAD_FOLDER = os.path.join(basedir, 'instance', 'uploads')
    EXPORT_FOLDER = os.path.join(basedir, 'instance', 'exports')

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    ENV = 'development'
    # MySQL connection configuration – reads from env vars. Falls back to SQLite for local dev.
    MYSQL_HOST = os.getenv('DB_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('DB_PORT', '3306'))
    MYSQL_DB   = os.getenv('DB_NAME', 'bank_stmt_db')
    MYSQL_USER = os.getenv('DB_USER', 'root')
    MYSQL_PASS = os.getenv('DB_PASSWORD', '')

    @classmethod
    def get_database_uri(cls):
        dev_uri = os.getenv('DEV_DATABASE_URI')
        if dev_uri:
            return dev_uri
        # Check if MySQL is running on MYSQL_HOST:MYSQL_PORT
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        mysql_live = False
        try:
            sock.connect((cls.MYSQL_HOST, cls.MYSQL_PORT))
            mysql_live = True
        except Exception:
            mysql_live = False
        finally:
            sock.close()

        if mysql_live:
            if cls.MYSQL_PASS:
                return f"mysql+pymysql://{cls.MYSQL_USER}:{cls.MYSQL_PASS}@{cls.MYSQL_HOST}:{cls.MYSQL_PORT}/{cls.MYSQL_DB}"
            return f"mysql+pymysql://{cls.MYSQL_USER}@{cls.MYSQL_HOST}:{cls.MYSQL_PORT}/{cls.MYSQL_DB}"

        # Clean fallback to SQLite for local development
        sqlite_file = os.path.join(basedir, 'instance', 'bank_statement.db').replace('\\', '/')
        return f"sqlite:///{sqlite_file}"

    SQLALCHEMY_DATABASE_URI = get_database_uri.__func__(None)



class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = True
    ENV = 'testing'
    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URI',
        f"sqlite:///:memory:")
    # Shorter token expiry for tests
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=5)

class ProductionConfig(BaseConfig):
    DEBUG = False
    ENV = 'production'
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI')
    # In production, enforce stronger session protection
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
