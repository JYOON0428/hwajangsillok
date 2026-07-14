from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database import engine, Base
from app.models import Toilet, Post, Review
from app.config import settings
from app.routes import frontend, restrooms, posts, location

# DB 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="화장실 커뮤니티 백엔드 API",
    version="1.0.0"
)

UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
try:
    UPLOAD_DIR.mkdir(exist_ok=True)
except OSError:
    pass
if UPLOAD_DIR.exists():
    app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우트 등록
app.include_router(restrooms.router, prefix=settings.API_V1_STR)
app.include_router(posts.router, prefix=settings.API_V1_STR)
app.include_router(location.router, prefix=settings.API_V1_STR)
app.include_router(frontend.router)


@app.get("/")
async def root():
    """헬스 체크"""
    return {
        "message": "화장실 커뮤니티 API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """상태 확인"""
    return {"status": "healthy"}

