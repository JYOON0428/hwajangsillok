from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import PostService, LocationService
from app.schemas import PostCreate, PostUpdate, PostPasswordVerify, PostResponse, PostDetailResponse
from typing import List

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("/categories")
async def get_categories(db: Session = Depends(get_db)):
    """모든 카테고리 조회"""
    categories = PostService.get_all_categories(db)
    return {"categories": categories}


@router.get("", response_model=List[PostResponse])
async def get_posts(
    category: str = Query(..., description="카테고리명"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("recent", regex="^(recent|rating)$"),
    db: Session = Depends(get_db)
):
    """
    카테고리별 게시글 조회
    
    Parameters:
    - category: 카테고리명 (필수) - "관광지", "문화시설", "축제/공연", "쇼핑"
    - sort_by: 정렬 기준 - "recent" (최신순) 또는 "rating" (평점순)
    """
    posts = PostService.get_posts_by_category(db, category, skip, limit, sort_by)
    return posts


@router.get("/{post_id}", response_model=PostDetailResponse)
async def get_post_detail(
    post_id: int,
    db: Session = Depends(get_db)
):
    """게시글 상세 조회"""
    post = PostService.get_post_detail(db, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    return post


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post: PostCreate,
    db: Session = Depends(get_db)
):
    """
    게시글 작성
    
    - category: "관광지", "문화시설", "축제/공연", "쇼핑"
    - title: 게시글 제목
    - content: 게시글 내용
    - password: 비밀번호 (수정/삭제 시 필요)
    - rating: 평점 (0~5)
    - image_url: 이미지 URL (선택)
    - toilet_id: 화장실 ID (선택)
    """
    if post.rating < 0 or post.rating > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be between 0 and 5"
        )
    
    return PostService.create_post(db, post)


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int,
    update_data: PostUpdate,
    db: Session = Depends(get_db)
):
    """게시글 수정 (비밀번호 필수)"""
    if update_data.rating and (update_data.rating < 0 or update_data.rating > 5):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be between 0 and 5"
        )
    
    updated_post = PostService.update_post(
        db, post_id, update_data.password,
        title=update_data.title,
        content=update_data.content,
        rating=update_data.rating,
        image_url=update_data.image_url
    )
    
    if not updated_post:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password or post not found"
        )
    
    return updated_post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    password_verify: PostPasswordVerify,
    db: Session = Depends(get_db)
):
    """게시글 삭제 (비밀번호 필수)"""
    success = PostService.delete_post(db, post_id, password_verify.password)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password or post not found"
        )
    
    return None
