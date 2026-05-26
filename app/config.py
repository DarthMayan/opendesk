import os
from pathlib import Path


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024
    PROFILE_AVATAR_UPLOAD_FOLDER = os.environ.get(
        "PROFILE_AVATAR_UPLOAD_FOLDER",
        str(Path(__file__).resolve().parent / "static" / "uploads" / "avatars"),
    )

    _db_url = os.environ.get("DATABASE_URL", "sqlite:///opendesk.db")
    # Render/Heroku entregan "postgres://"; SQLAlchemy requiere "postgresql://".
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
