from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Toilet(Base):
    """공중화장실 모델"""
    __tablename__ = "toilets"
    
    toilet_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    address = Column(String(255))
    latitude = Column(Float)
    longitude = Column(Float)
    male_toilet_count = Column(Integer, default=0)
    female_toilet_count = Column(Integer, default=0)
    male_urinal_count = Column(Integer, default=0)
    female_urinal_count = Column(Integer, default=0)
    handicap_facility = Column(Boolean, default=False)
    emergency_bell = Column(Boolean, default=False)
    diaper_changing_table = Column(Boolean, default=False)
    phone = Column(String(20), nullable=True)
    opening_hours = Column(String(100), nullable=True)
    open_time_detail = Column(String(100), nullable=True)
    data_reference_date = Column(String(20), nullable=True)
    entrance_cctv = Column(Boolean, default=False)
    toilet_type = Column(String(50), nullable=True)
    managing_agency = Column(String(100), nullable=True)
    geocoded_address = Column(String(255), nullable=True)
    geocode_source = Column(String(50), nullable=True)
    geocode_status = Column(String(50), nullable=True)
    
    # 관계
    posts = relationship("Post", back_populates="toilet")
    reviews = relationship("Review", back_populates="toilet")


class Post(Base):
    """게시글 모델 (카테고리별 커뮤니티)"""
    __tablename__ = "posts"
    
    post_id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), index=True)  # "관광지", "문화시설", "축제/공연", "쇼핑"
    title = Column(String(255), index=True)
    content = Column(Text)
    password = Column(String(255))  # 평문 저장 (실제로는 암호화해야 함)
    rating = Column(Float, default=0)  # 0~5
    image_url = Column(String(500), nullable=True)
    image_urls = Column(Text, nullable=True)
    nickname = Column(String(50), nullable=True)
    post_type = Column(String(50), default="화장실 리뷰")
    related_place = Column(String(100), nullable=True)
    restroom_name = Column(String(255), nullable=True)
    recommendation_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    toilet_id = Column(Integer, ForeignKey("toilets.toilet_id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    toilet = relationship("Toilet", back_populates="posts")
    comments = relationship("Comment", back_populates="post")


class Review(Base):
    """화장실 리뷰 모델"""
    __tablename__ = "reviews"
    
    review_id = Column(Integer, primary_key=True, index=True)
    toilet_id = Column(Integer, ForeignKey("toilets.toilet_id"), index=True)
    post_id = Column(Integer, ForeignKey("posts.post_id"), nullable=True, index=True)
    rating = Column(Float)  # 0~5
    content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # 관계
    toilet = relationship("Toilet", back_populates="reviews")
    post = relationship("Post", backref="linked_reviews")


class Comment(Base):
    """게시글 댓글 모델"""
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.post_id"), index=True)
    nickname = Column(String(50), nullable=False)
    password = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    post = relationship("Post", back_populates="comments")
