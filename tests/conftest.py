from pathlib import Path
import sys

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app import create_app
from app.extensions import db


@pytest.fixture
def app(tmp_path):
    class TestConfig:
        SECRET_KEY = "test-secret-key"
        TESTING = True
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp_path / 'test.db'}"
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        PROFILE_AVATAR_UPLOAD_FOLDER = str(tmp_path / "avatars")
        MAX_CONTENT_LENGTH = 2 * 1024 * 1024

    app = create_app(TestConfig)

    with app.app_context():
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()
