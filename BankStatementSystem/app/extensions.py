from flask_sqlalchemy import SQLAlchemy

from flask_migrate import Migrate
from flask_wtf import CSRFProtect

db = SQLAlchemy()
# Initialize migration and CSRF protection objects – they are attached to the app in the factory.
migrate = Migrate()
csrf = CSRFProtect()
