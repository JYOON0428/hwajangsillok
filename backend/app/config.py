import os
from datetime import datetime
from pathlib import Path

# Load .env from backend root (if present)
def load_local_env():
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        val = val.strip().strip('"').strip("'")
        os.environ.setdefault(key.strip(), val)

load_local_env()


class Settings:
    """애플리케이션 설정"""
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "화장실 커뮤니티 API"
    DEBUG: bool = True

settings = Settings()