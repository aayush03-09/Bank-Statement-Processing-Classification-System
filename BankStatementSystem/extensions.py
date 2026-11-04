"""Flask extensions initialization.

This module creates extension objects that are instantiated
once and then initialized with the Flask app inside the
application factory.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import CSRFProtect

# Database instance (SQLAlchemy)
db = SQLAlchemy()

# Migration handling
migrate = Migrate()

# CSRF protection for forms
csrf = CSRFProtect()
