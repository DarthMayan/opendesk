from flask import Flask
from flask_login import current_user
from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy import inspect, text

from .config import Config
from .extensions import db, login_manager

load_dotenv()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.config.setdefault(
        "PROFILE_AVATAR_UPLOAD_FOLDER",
        str(Path(app.static_folder) / "uploads" / "avatars"),
    )
    app.config.setdefault("MAX_CONTENT_LENGTH", 2 * 1024 * 1024)
    Path(app.config["PROFILE_AVATAR_UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    from .auth.routes import auth_bp
    from .main.routes import main_bp
    from .tickets.routes import tickets_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(tickets_bp)

    @app.context_processor
    def inject_notifications():
        if not current_user.is_authenticated:
            return {}

        from .models import Notification

        unread_notifications = Notification.query.filter_by(
            user_id=current_user.id,
            read_at=None,
        ).count()
        return {"unread_notifications": unread_notifications}

    with app.app_context():
        from . import models  # noqa: F401
        db.create_all()
        _ensure_user_avatar_column()

    return app


def _ensure_user_avatar_column():
    columns = {column["name"] for column in inspect(db.engine).get_columns("users")}
    if "avatar_filename" not in columns:
        db.session.execute(text("ALTER TABLE users ADD COLUMN avatar_filename VARCHAR(255)"))
        db.session.commit()
