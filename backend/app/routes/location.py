from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import LocationService
from app.schemas import LocationQuery

router = APIRouter(prefix="/location", tags=["location"])


@router.get("/nearby")
async def get_nearby_with_posts(
    latitude: float,
    longitude: float,
    distance: int = 1000,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    근처 화장실과 최근 게시글 조회
    
    Parameters:
    - latitude: 사용자 위도 (필수)
    - longitude: 사용자 경도 (필수)
    - distance: 검색 거리 (미터, 기본값 1000)
    - limit: 반환 화장실 개수 제한 (기본값 20)
    
    Returns:
    - toilets: 근처 화장실 목록 (거리순)
    - posts_by_toilet: {toilet_id: [최근 게시글]}
    """
    try:
        toilets, posts_by_toilet = LocationService.get_nearby_with_posts(
            db, latitude, longitude, distance, limit
        )
        
        return {
            "toilets": toilets,
            "posts_by_toilet": posts_by_toilet
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching nearby data: {str(e)}"
        )
