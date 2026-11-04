"""Bank Statement Processing & Classification System package.

Provides the Flask application factory and registers extensions and blueprints.
"""

import os
from flask import Flask

# Import extensions from the app subpackage
from .app.extensions import db, migrate, csrf

# Import blueprints from the app subpackage
from .app.routes.health import health_bp
from .app.routes.main import main_bp

# Import models so SQLAlchemy registers them
from .app.models import (
    bank_statement,
    transaction,
    classification_feedback,
    processing_history,
    processing_issue,
)


def create_app(config_object='BankStatementSystem.config.DevelopmentConfig'):
    """Application factory pattern.

    Args:
        config_object (str): Import path for the configuration class.
    Returns:
        Flask: Configured Flask application instance.
    """
    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(pkg_dir, 'app', 'templates')
    static_dir = os.path.join(pkg_dir, 'app', 'static')

    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder=template_dir,
        static_folder=static_dir,
    )
    # Load default configuration and optional instance config
    app.config.from_object(config_object)
    app.config.from_pyfile('config.py', silent=True)

    # Ensure required instance folders exist
    os.makedirs(app.instance_path, exist_ok=True)
    if 'UPLOAD_FOLDER' in app.config:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    if 'EXPORT_FOLDER' in app.config:
        os.makedirs(app.config['EXPORT_FOLDER'], exist_ok=True)

    # Initialise extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Auto-create tables for local development
    with app.app_context():
        db.create_all()

    # Register blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(main_bp, url_prefix='')

    return app


__all__ = ['create_app', 'db', 'migrate', 'csrf']
