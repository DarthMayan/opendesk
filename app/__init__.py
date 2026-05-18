from flask import Flask
from dotenv import load_dotenv

from .config import Config
from .extensions import db, login_manager

load_dotenv()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    from .main.routes import main_bp
    app.register_blueprint(main_bp)

    with app.app_context():
        from . import models  # noqa: F401
        db.create_all()

    return app
