from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ============ Toilet Schemas ============
class ToiletBase(BaseModel):
    name: str
    address: str
    latitude: float
    longitude: float
    male_toilet_count: int = 0
    female_toilet_count: int = 0
    male_urinal_count: int = 0
    female_urinal_count: int = 0
    handicap_facility: bool = False
    emergency_bell: bool = False
    diaper_changing_table: bool = False
    phone: Optional[str] = None
    opening_hours: Optional[str] = None
    open_time_detail: Optional[str] = None
    data_reference_date: Optional[str] = None
    entrance_cctv: bool = False
    toilet_type: Optional[str] = None
    managing_agency: Optional[str] = None
    geocoded_address: Optional[str] = None
    geocode_source: Optional[str] = None
    geocode_status: Optional[str] = None


class ToiletCreate(ToiletBase):
    pass


class ToiletResponse(ToiletBase):
    toilet_id: int
    
    class Config:
        from_attributes = True


class ToiletWithDistance(ToiletResponse):
    """거리 정보를 포함한 화장실 응답"""
    distance: float


class ToiletWithRecentPosts(ToiletResponse):
    """최근 게시글을 포함한 화장실 응답"""
    average_rating: Optional[float] = None
    recent_posts: Optional[List["PostResponse"]] = []


# ============ Post Schemas ============
class PostBase(BaseModel):
    category: str
    title: str
    content: str
    password: str
    rating: float = 0
    image_url: Optional[str] = None
    image_urls: Optional[str] = None
    nickname: Optional[str] = None
    post_type: str = "화장실 리뷰"
    related_place: Optional[str] = None
    restroom_name: Optional[str] = None
    recommendation_count: int = 0
    comment_count: int = 0
    toilet_id: Optional[int] = None


class PostCreate(PostBase):
    pass


class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    password: str
    rating: Optional[float] = None
    image_url: Optional[str] = None
    image_urls: Optional[str] = None
    nickname: Optional[str] = None
    post_type: Optional[str] = None
    related_place: Optional[str] = None
    restroom_name: Optional[str] = None
    toilet_id: Optional[int] = None


class PostPasswordVerify(BaseModel):
    password: str


class PostResponse(BaseModel):
    post_id: int
    category: str
    title: str
    content: str
    rating: float
    image_url: Optional[str]
    image_urls: Optional[str]
    nickname: Optional[str]
    post_type: Optional[str]
    related_place: Optional[str]
    restroom_name: Optional[str]
    recommendation_count: int
    comment_count: int
    toilet_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PostDetailResponse(PostResponse):
    """상세 조회용 응답"""
    toilet: Optional[ToiletResponse] = None


# ============ Review Schemas ============
class ReviewBase(BaseModel):
    toilet_id: int
    rating: float
    content: Optional[str] = None


class ReviewCreate(ReviewBase):
    pass


class ReviewResponse(ReviewBase):
    review_id: int
    post_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ Location Schemas ============
class LocationQuery(BaseModel):
    latitude: float
    longitude: float
    distance: int = 1000  # 기본 거리 1km


class NearbyToiletResponse(ToiletWithDistance):
    """근처 화장실 응답 (거리 포함)"""
    average_rating: Optional[float] = None


class NearbyResponse(BaseModel):
    """위치 기반 응답 (화장실 + 최근 게시글)"""
    toilets: List[NearbyToiletResponse]
    posts_by_toilet: dict  # {toilet_id: [posts]}
