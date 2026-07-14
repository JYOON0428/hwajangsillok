import os
from datetime import datetime

class Settings:
    """애플리케이션 설정"""
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "화장실 커뮤니티 API"
    DEBUG: bool = True

settings = Settings()
