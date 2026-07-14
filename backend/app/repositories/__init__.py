from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Toilet, Post, Review
from app.schemas import ToiletCreate, PostCreate, ReviewCreate
from typing import List, Optional


class ToiletRepository:
    """화장실 데이터 접근 계층"""
    
    @staticmethod
    def create(db: Session, toilet: ToiletCreate) -> Toilet:
        """화장실 생성"""
        db_toilet = Toilet(**toilet.dict())
        db.add(db_toilet)
        db.commit()
        db.refresh(db_toilet)
        return db_toilet
    
    @staticmethod
    def get_by_id(db: Session, toilet_id: int) -> Optional[Toilet]:
        """ID로 화장실 조회"""
        return db.query(Toilet).filter(Toilet.toilet_id == toilet_id).first()
    
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[Toilet]:
        """모든 화장실 조회"""
        return db.query(Toilet).offset(skip).limit(limit).all()
    
    @staticmethod
    def search_by_name(db: Session, name: str) -> List[Toilet]:
        """이름으로 검색"""
        return db.query(Toilet).filter(Toilet.name.ilike(f"%{name}%")).all()
    
    @staticmethod
    def get_average_rating(db: Session, toilet_id: int) -> Optional[float]:
        """화장실의 평균 평점 조회"""
        avg = db.query(func.avg(Review.rating)).filter(
            Review.toilet_id == toilet_id
        ).scalar()
        return avg


class PostRepository:
    """게시글 데이터 접근 계층"""
    
    @staticmethod
    def create(db: Session, post: PostCreate) -> Post:
        """게시글 생성"""
        db_post = Post(**post.dict())
        db.add(db_post)
        db.commit()
        db.refresh(db_post)
        return db_post
    
    @staticmethod
    def get_by_id(db: Session, post_id: int) -> Optional[Post]:
        """ID로 게시글 조회"""
        return db.query(Post).filter(Post.post_id == post_id).first()
    
    @staticmethod
    def get_by_category(
        db: Session, 
        category: str, 
        skip: int = 0, 
        limit: int = 20,
        sort_by: str = "created_at"
    ) -> List[Post]:
        """카테고리별 게시글 조회"""
        query = db.query(Post).filter(Post.category == category)
        
        if sort_by == "recent":
            query = query.order_by(Post.created_at.desc())
        elif sort_by == "rating":
            query = query.order_by(Post.rating.desc())
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def get_by_toilet_id(db: Session, toilet_id: int, limit: int = 10) -> List[Post]:
        """특정 화장실의 게시글 조회 (최근순)"""
        return db.query(Post).filter(
            Post.toilet_id == toilet_id
        ).order_by(Post.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def update(db: Session, post_id: int, **kwargs) -> Optional[Post]:
        """게시글 수정"""
        db_post = db.query(Post).filter(Post.post_id == post_id).first()
        if db_post:
            for key, value in kwargs.items():
                if hasattr(db_post, key) and value is not None:
                    setattr(db_post, key, value)
            db.commit()
            db.refresh(db_post)
        return db_post
    
    @staticmethod
    def delete(db: Session, post_id: int) -> bool:
        """게시글 삭제"""
        db_post = db.query(Post).filter(Post.post_id == post_id).first()
        if db_post:
            db.delete(db_post)
            db.commit()
            return True
        return False
    
    @staticmethod
    def get_all_categories(db: Session) -> List[str]:
        """모든 카테고리 조회"""
        categories = db.query(Post.category).distinct().all()
        return [c[0] for c in categories]


class ReviewRepository:
    """리뷰 데이터 접근 계층"""
    
    @staticmethod
    def create(db: Session, review: ReviewCreate) -> Review:
        """리뷰 생성"""
        db_review = Review(**review.dict())
        db.add(db_review)
        db.commit()
        db.refresh(db_review)
        return db_review
    
    @staticmethod
    def get_by_id(db: Session, review_id: int) -> Optional[Review]:
        """ID로 리뷰 조회"""
        return db.query(Review).filter(Review.review_id == review_id).first()
    
    @staticmethod
    def get_by_toilet_id(db: Session, toilet_id: int) -> List[Review]:
        """화장실별 리뷰 조회"""
        return db.query(Review).filter(Review.toilet_id == toilet_id).all()
