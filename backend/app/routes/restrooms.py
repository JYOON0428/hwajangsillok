from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import ToiletService, LocationService
from app.schemas import ToiletCreate, ToiletResponse
from typing import List

router = APIRouter(prefix="/restrooms", tags=["restrooms"])


@router.get("/nearby", response_model=List[dict])
async def get_nearby_toilets(
    latitude: float,
    longitude: float,
    distance: int = 1000,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    근처 화장실 조회
    
    Parameters:
    - latitude: 사용자 위도
    - longitude: 사용자 경도
    - distance: 검색 거리 (미터, 기본값 1000)
    - limit: 반환 개수 제한 (기본값 50)
    """
    try:
        toilets = LocationService.get_nearby_toilets(
            db, latitude, longitude, distance, limit
        )
        return toilets
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching nearby toilets: {str(e)}"
        )


@router.get("/{toilet_id}", response_model=dict)
async def get_toilet_detail(
    toilet_id: int,
    db: Session = Depends(get_db)
):
    """특정 화장실 상세 정보 조회"""
    toilet = ToiletService.get_toilet_detail(db, toilet_id)
    if not toilet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Toilet not found"
        )
    return toilet


@router.post("", response_model=ToiletResponse)
async def create_toilet(
    toilet: ToiletCreate,
    db: Session = Depends(get_db)
):
    """화장실 생성 (관리자 기능)"""
    return ToiletService.create_toilet(db, toilet)
