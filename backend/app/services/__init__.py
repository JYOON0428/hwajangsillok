from sqlalchemy.orm import Session
from math import radians, cos, sin, asin, sqrt
from app.repositories import ToiletRepository, PostRepository, ReviewRepository
from app.schemas import (
    ToiletCreate, PostCreate, ToiletWithDistance, 
    NearbyToiletResponse, PostResponse
)
from typing import List, Optional, Tuple


class LocationService:
    """위치 기반 서비스"""
    
    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        두 좌표 사이의 거리 계산 (Haversine 공식)
        반환: 미터 단위의 거리
        """
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        r = 6371000  # 지구 반지름 (미터)
        return c * r
    
    @staticmethod
    def get_nearby_toilets(
        db: Session,
        latitude: float,
        longitude: float,
        distance: int = 1000,
        limit: int = 50
    ) -> List[NearbyToiletResponse]:
        """
        근처 화장실 조회
        
        Args:
            db: DB 세션
            latitude: 사용자 위도
            longitude: 사용자 경도
            distance: 검색 거리 (미터, 기본값 1000m)
            limit: 반환 개수 제한
        
        Returns:
            거리 정보를 포함한 화장실 목록
        """
        all_toilets = ToiletRepository.get_all(db, limit=1000)
        nearby = []
        
        for toilet in all_toilets:
            dist = LocationService.calculate_distance(
                latitude, longitude,
                toilet.latitude, toilet.longitude
            )
            
            if dist <= distance:
                avg_rating = ToiletRepository.get_average_rating(db, toilet.toilet_id)
                nearby.append({
                    "toilet_id": toilet.toilet_id,
                    "name": toilet.name,
                    "address": toilet.address,
                    "latitude": toilet.latitude,
                    "longitude": toilet.longitude,
                    "male_toilet_count": toilet.male_toilet_count,
                    "female_toilet_count": toilet.female_toilet_count,
                    "male_urinal_count": toilet.male_urinal_count,
                    "female_urinal_count": toilet.female_urinal_count,
                    "handicap_facility": toilet.handicap_facility,
                    "emergency_bell": toilet.emergency_bell,
                    "diaper_changing_table": toilet.diaper_changing_table,
                    "phone": toilet.phone,
                    "distance": round(dist, 2),
                    "average_rating": round(avg_rating, 2) if avg_rating else None
                })
        
        # 거리순으로 정렬
        nearby.sort(key=lambda x: x["distance"])
        return nearby[:limit]
    
    @staticmethod
    def get_nearby_with_posts(
        db: Session,
        latitude: float,
        longitude: float,
        distance: int = 1000,
        limit: int = 20
    ) -> Tuple[List[NearbyToiletResponse], dict]:
        """
        근처 화장실과 최근 게시글 조회
        
        Returns:
            (화장실 목록, {toilet_id: [posts]})
        """
        toilets = LocationService.get_nearby_toilets(db, latitude, longitude, distance, limit)
        posts_by_toilet = {}
        
        for toilet in toilets:
            toilet_id = toilet["toilet_id"]
            posts = PostRepository.get_by_toilet_id(db, toilet_id, limit=5)
            if posts:
                posts_by_toilet[toilet_id] = [
                    {
                        "post_id": p.post_id,
                        "category": p.category,
                        "title": p.title,
                        "rating": p.rating,
                        "created_at": p.created_at.isoformat()
                    }
                    for p in posts
                ]
        
        return toilets, posts_by_toilet


class ToiletService:
    """화장실 서비스"""
    
    @staticmethod
    def create_toilet(db: Session, toilet: ToiletCreate):
        """화장실 생성"""
        return ToiletRepository.create(db, toilet)
    
    @staticmethod
    def get_toilet_detail(db: Session, toilet_id: int):
        """화장실 상세 조회"""
        toilet = ToiletRepository.get_by_id(db, toilet_id)
        if not toilet:
            return None
        
        avg_rating = ToiletRepository.get_average_rating(db, toilet_id)
        return {
            "toilet_id": toilet.toilet_id,
            "name": toilet.name,
            "address": toilet.address,
            "latitude": toilet.latitude,
            "longitude": toilet.longitude,
            "male_toilet_count": toilet.male_toilet_count,
            "female_toilet_count": toilet.female_toilet_count,
            "male_urinal_count": toilet.male_urinal_count,
            "female_urinal_count": toilet.female_urinal_count,
            "handicap_facility": toilet.handicap_facility,
            "emergency_bell": toilet.emergency_bell,
            "diaper_changing_table": toilet.diaper_changing_table,
            "phone": toilet.phone,
            "average_rating": round(avg_rating, 2) if avg_rating else None
        }


class PostService:
    """게시글 서비스"""
    
    @staticmethod
    def create_post(db: Session, post: PostCreate):
        """게시글 생성"""
        return PostRepository.create(db, post)
    
    @staticmethod
    def get_post_detail(db: Session, post_id: int):
        """게시글 상세 조회"""
        return PostRepository.get_by_id(db, post_id)
    
    @staticmethod
    def get_posts_by_category(
        db: Session,
        category: str,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "recent"
    ):
        """카테고리별 게시글 조회"""
        return PostRepository.get_by_category(db, category, skip, limit, sort_by)
    
    @staticmethod
    def verify_post_password(db: Session, post_id: int, password: str) -> bool:
        """게시글 비밀번호 검증"""
        post = PostRepository.get_by_id(db, post_id)
        if not post:
            return False
        return post.password == password
    
    @staticmethod
    def update_post(db: Session, post_id: int, password: str, **kwargs):
        """게시글 수정 (비밀번호 검증 후)"""
        if not PostService.verify_post_password(db, post_id, password):
            return None
        
        # password 제거 (업데이트하면 안됨)
        kwargs.pop("password", None)
        return PostRepository.update(db, post_id, **kwargs)
    
    @staticmethod
    def delete_post(db: Session, post_id: int, password: str) -> bool:
        """게시글 삭제 (비밀번호 검증 후)"""
        if not PostService.verify_post_password(db, post_id, password):
            return False
        return PostRepository.delete(db, post_id)
    
    @staticmethod
    def get_all_categories(db: Session) -> List[str]:
        """모든 카테고리 조회"""
        return PostRepository.get_all_categories(db)
