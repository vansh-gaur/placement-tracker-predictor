"""Configuration from environment variables. No secrets are hardcoded.

DATABASE_URL examples:
  - (unset)                       -> sqlite file backend/placements.db
  - sqlite:///path/to/file.db     -> SQLite file
  - sqlite:///:memory:            -> in-memory SQLite (tests)
  - postgresql://user:pass@host:port/db  -> PostgreSQL (production)

JWT_SECRET must be set in production. Locally, a development secret
is used and a warning is logged, so a forgotten secret can never
silently become a production secret.
"""

import logging
import os

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _database_url():
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        return f"sqlite:///{os.path.join(BASE_DIR, 'placements.db')}"
    if url.startswith("postgres://"):
        # SQLAlchemy wants postgresql://, not postgres://
        url = "postgresql://" + url[len("postgres://"):]
    return url


class Config:
    DATABASE_URL = _database_url()
    JWT_SECRET = os.environ.get("JWT_SECRET", "")
    JWT_EXPIRY_HOURS = int(os.environ.get("JWT_EXPIRY_HOURS", "24"))
    PORT = int(os.environ.get("PORT", "5000"))
    MODEL_PATH = os.environ.get(
        "MODEL_PATH", os.path.join(BASE_DIR, "model.pkl")
    )
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ]

    @classmethod
    def check(cls):
        if not cls.JWT_SECRET:
            logger.warning(
                "JWT_SECRET is not set; using a development-only secret. "
                "Set JWT_SECRET before deploying anywhere real."
            )
            cls.JWT_SECRET = "dev-only-secret-change-me"
