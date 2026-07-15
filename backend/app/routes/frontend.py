import json
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4
import os

import httpx

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Post, Review, Toilet

router = APIRouter(prefix="/api", tags=["frontend"])

BACKEND_ROOT = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BACKEND_ROOT / "uploads"
SEOUL_DATA_DIR = BACKEND_ROOT / "data" / "seoul"

CATEGORY_ALIASES = {
    "전체": "전체",
    "관광지": "관광지",
    "문화시설": "문화시설",
    "축제·공연": "축제/공연",
    "축제/공연": "축제/공연",
    "축제공연행사": "축제/공연",
    "쇼핑": "쇼핑",
    "자유게시판": "자유게시판",
}

FRONTEND_CATEGORY_LABELS = {
    "축제/공연": "축제·공연",
    "축제·공연": "축제·공연",
}

DEFAULT_CENTER = (37.5665, 126.9780)
KEYWORD_CENTERS = {
    "역삼역 멀티캠퍼스": (37.5012743, 127.0395850),
    "멀티캠퍼스": (37.5012743, 127.0395850),
    "역삼역": (37.5006220, 127.0364560),
    "서울숲": (37.5430715815, 127.0417984460),
    "강남역": (37.4979, 127.0276),
    "남산": (37.5510545366, 126.9878820833),
    "남산서울타워": (37.5510545366, 126.9878820833),
    "경복궁": (37.5760307000, 126.9767218661),
    "광화문": (37.5716, 126.9769),
    "명동": (37.5636, 126.9822),
    "대학로": (37.5805669329, 127.0023878907),
    "국립중앙박물관": (37.5239, 126.9804),
    "국립박물관": (37.5239, 126.9804),
    "홍대": (37.5563, 126.9236),
    "여의도": (37.5268, 126.9237),
    "동대문": (37.5700, 127.0095),
    "코엑스": (37.5118, 127.0592),
    "잠실": (37.5133, 127.1028),
    "용산": (37.5298, 126.9648),
}

DISTRICT_CENTERS = {
    "종로구": (37.5735, 126.9788),
    "중구": (37.5636, 126.9976),
    "용산구": (37.5326, 126.9905),
    "성동구": (37.5633, 127.0369),
    "광진구": (37.5384, 127.0823),
    "동대문구": (37.5744, 127.0396),
    "중랑구": (37.6063, 127.0927),
    "성북구": (37.5894, 127.0167),
    "강북구": (37.6396, 127.0257),
    "도봉구": (37.6688, 127.0471),
    "노원구": (37.6542, 127.0568),
    "은평구": (37.6027, 126.9291),
    "서대문구": (37.5791, 126.9368),
    "마포구": (37.5663, 126.9018),
    "양천구": (37.5170, 126.8665),
    "강서구": (37.5509, 126.8495),
    "구로구": (37.4955, 126.8877),
    "금천구": (37.4569, 126.8958),
    "영등포구": (37.5264, 126.8963),
    "동작구": (37.5124, 126.9393),
    "관악구": (37.4784, 126.9516),
    "서초구": (37.4837, 127.0324),
    "강남구": (37.5172, 127.0473),
    "송파구": (37.5145, 127.1059),
    "강동구": (37.5301, 127.1238),
}


def _frontend_category(category: str | None) -> str:
    if not category:
        return "일반"
    return FRONTEND_CATEGORY_LABELS.get(category, category)


def _backend_category(category: str | None) -> str | None:
    if not category or category == "전체":
        return None
    return CATEGORY_ALIASES.get(category, category)


def _json_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        value = json.loads(raw)
        if isinstance(value, list):
            return [str(item) for item in value if item]
    except json.JSONDecodeError:
        pass
    return [raw] if raw else []


def _dump_image_urls(urls: list[str]) -> str | None:
    clean_urls = [url for url in urls if url]
    return json.dumps(clean_urls, ensure_ascii=False) if clean_urls else None


def _distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371000 * 2 * math.asin(math.sqrt(a))


def _time_label(value: datetime | None) -> str:
    if not value:
        return ""
    delta = datetime.utcnow() - value
    minutes = max(0, int(delta.total_seconds() // 60))
    if minutes < 1:
        return "방금 전"
    if minutes < 60:
        return f"{minutes}분 전"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}시간 전"
    display_value = value + timedelta(hours=9)
    return display_value.strftime("%Y.%m.%d")


def _client_datetime(value: datetime | None) -> str:
    if not value:
        return ""
    suffix = "" if value.tzinfo else "Z"
    return f"{value.isoformat()}{suffix}"


def _map_position(latitude: float | None, longitude: float | None) -> dict[str, float]:
    if not latitude or not longitude:
        return {"x": 50.0, "y": 50.0}
    x = ((longitude - 126.75) / (127.2 - 126.75)) * 100
    y = 100 - ((latitude - 37.42) / (37.7 - 37.42)) * 100
    return {
        "x": round(min(94, max(6, x)), 1),
        "y": round(min(94, max(6, y)), 1),
    }


def _opening_hours(toilet: Toilet) -> str:
    detail = (toilet.open_time_detail or "").strip()
    opening = (toilet.opening_hours or "").strip()
    if detail:
        return detail
    if opening == "상시":
        return "24시간"
    return opening or "정보 없음"


def _is_open_now(toilet: Toilet) -> bool:
    hours = _opening_hours(toilet)
    if "24" in hours or "상시" in hours:
        return True
    if "~" not in hours:
        return True
    try:
        start_raw, end_raw = [part.strip() for part in hours.split("~", 1)]
        start = datetime.strptime(start_raw[:5], "%H:%M").time()
        end = datetime.strptime(end_raw[:5], "%H:%M").time()
        now = datetime.now().time()
        if start <= end:
            return start <= now <= end
        return now >= start or now <= end
    except ValueError:
        return True


def _rating_and_count(db: Session, toilet_id: int) -> tuple[float | None, int]:
    review_avg = db.query(func.avg(Review.rating)).filter(Review.toilet_id == toilet_id).scalar()
    review_count = db.query(func.count(Review.review_id)).filter(Review.toilet_id == toilet_id).scalar() or 0
    post_avg = db.query(func.avg(Post.rating)).filter(Post.toilet_id == toilet_id).scalar()
    post_count = db.query(func.count(Post.post_id)).filter(Post.toilet_id == toilet_id).scalar() or 0

    values = [value for value in [review_avg, post_avg] if value is not None]
    rating = round(sum(values) / len(values), 1) if values else None
    return rating, int(review_count + post_count)


def _latest_review_text(db: Session, toilet_id: int) -> tuple[str, datetime | None]:
    latest_post = (
        db.query(Post)
        .filter(Post.toilet_id == toilet_id)
        .order_by(Post.created_at.desc())
        .first()
    )
    latest_review = (
        db.query(Review)
        .filter(Review.toilet_id == toilet_id)
        .order_by(Review.created_at.desc())
        .first()
    )
    candidates = []
    if latest_post:
        candidates.append((latest_post.content, latest_post.created_at))
    if latest_review:
        candidates.append((latest_review.content or "청결도 리뷰가 등록되었습니다.", latest_review.created_at))
    if not candidates:
        return "", None
    candidates.sort(key=lambda item: item[1], reverse=True)
    return candidates[0]


def _restroom_tags(toilet: Toilet, open_now: bool) -> list[str]:
    tags = []
    if toilet.diaper_changing_table:
        tags.append("기저귀 교환대")
    if toilet.handicap_facility:
        tags.append("장애인용")
    if toilet.emergency_bell:
        tags.append("비상벨")
    if "24" in _opening_hours(toilet):
        tags.append("24시간")
    elif open_now:
        tags.append("현재 개방")
    return tags


def _normalize_restroom(db: Session, toilet: Toilet, distance: float | None = None) -> dict[str, Any]:
    rating, review_count = _rating_and_count(db, toilet.toilet_id)
    latest_review, latest_at = _latest_review_text(db, toilet.toilet_id)
    open_now = _is_open_now(toilet)
    distance_meters = int(round(distance or 0))

    return {
        "id": toilet.toilet_id,
        "toiletId": toilet.toilet_id,
        "name": toilet.name,
        "address": toilet.address,
        "distanceMeters": distance_meters,
        "rating": rating,
        "reviewCount": review_count,
        "latestReviewAt": latest_at.isoformat() if latest_at else "",
        "latestReviewLabel": _time_label(latest_at),
        "latestReview": latest_review,
        "tags": _restroom_tags(toilet, open_now),
        "facilities": {
            "diaperTable": bool(toilet.diaper_changing_table),
            "accessible": bool(toilet.handicap_facility),
            "emergencyBell": bool(toilet.emergency_bell),
            "entranceCctv": bool(toilet.entrance_cctv),
            "open24Hours": "24" in _opening_hours(toilet),
        },
        "openNow": open_now,
        "openingHours": _opening_hours(toilet),
        "dataReferenceDate": toilet.data_reference_date or "",
        "recentStatus": "",
        "latitude": toilet.latitude,
        "longitude": toilet.longitude,
        "mapPosition": _map_position(toilet.latitude, toilet.longitude),
        "phone": toilet.phone,
        "maleToiletCount": toilet.male_toilet_count,
        "femaleToiletCount": toilet.female_toilet_count,
        "geocodedAddress": toilet.geocoded_address,
        "geocodeSource": toilet.geocode_source,
        "geocodeStatus": toilet.geocode_status,
    }


def _normalize_post(post: Post, anonymous_name: str | None = None) -> dict[str, Any]:
    urls = _json_list(post.image_urls)
    if post.image_url and post.image_url not in urls:
        urls.insert(0, post.image_url)
    restroom = post.toilet
    restroom_name = post.restroom_name or (restroom.name if restroom else "")

    return {
        "id": post.post_id,
        "postId": post.post_id,
        "nickname": anonymous_name or post.nickname or "익명의 사용자",
        "restroomId": post.toilet_id,
        "category": _frontend_category(post.category),
        "postType": post.post_type or "화장실 리뷰",
        "title": post.title,
        "content": post.content,
        "relatedPlace": post.related_place or _frontend_category(post.category),
        "restroomName": restroom_name,
        "rating": post.rating,
        "recommendationCount": post.recommendation_count or 0,
        "commentCount": post.comment_count or 0,
        "createdAt": _client_datetime(post.created_at),
        "createdAtLabel": _time_label(post.created_at),
        "updatedAt": _client_datetime(post.updated_at),
        "imageUrl": urls[0] if urls else "",
        "imageUrls": urls,
    }


def _anonymous_name_for_post(db: Session, post: Post) -> str:
    if not post.created_at:
        return f"익명의 사용자 {post.post_id}"

    sequence = (
        db.query(func.count(Post.post_id))
        .filter(
            or_(
                Post.created_at < post.created_at,
                and_(Post.created_at == post.created_at, Post.post_id <= post.post_id),
            )
        )
        .scalar()
        or post.post_id
    )
    return f"익명의 사용자 {int(sequence)}"


def _load_poi_index() -> list[dict[str, Any]]:
    if hasattr(_load_poi_index, "cache"):
        return getattr(_load_poi_index, "cache")

    items: list[dict[str, Any]] = []
    for path in SEOUL_DATA_DIR.glob("서울_*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        content_type = data.get("contentType", "")
        for item in data.get("items", []):
            title = str(item.get("title") or "")
            mapx = item.get("mapx")
            mapy = item.get("mapy")
            if not title or not mapx or not mapy:
                continue
            try:
                items.append(
                    {
                        "title": title,
                        "address": str(item.get("addr1") or item.get("addr2") or ""),
                        "category": content_type,
                        "latitude": float(mapy),
                        "longitude": float(mapx),
                    }
                )
            except (TypeError, ValueError):
                continue

    setattr(_load_poi_index, "cache", items)
    return items


def _resolve_center(db: Session, keyword: str | None) -> tuple[float, float]:
    keyword = (keyword or "").strip()
    if not keyword or keyword == "화장실":
        return DEFAULT_CENTER

    for key, center in KEYWORD_CENTERS.items():
        if key in keyword or keyword in key:
            return center

    for poi in _load_poi_index():
        title = poi["title"]
        if keyword in title or title in keyword or keyword in poi["address"]:
            return poi["latitude"], poi["longitude"]

    matched_toilet = (
        db.query(Toilet)
        .filter(or_(Toilet.name.contains(keyword), Toilet.address.contains(keyword)))
        .filter(Toilet.latitude != 0, Toilet.longitude != 0)
        .first()
    )
    if matched_toilet:
        return matched_toilet.latitude, matched_toilet.longitude

    for district, center in DISTRICT_CENTERS.items():
        if district in keyword:
            return center

    return DEFAULT_CENTER


def _post_query(db: Session, category: str | None, keyword: str | None):
    query = db.query(Post)
    backend_category = _backend_category(category)
    if backend_category:
        query = query.filter(Post.category == backend_category)

    keyword = (keyword or "").strip()
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            or_(
                Post.title.like(like),
                Post.content.like(like),
                Post.nickname.like(like),
                Post.related_place.like(like),
                Post.restroom_name.like(like),
            )
        )
    return query


async def _read_post_payload(request: Request) -> tuple[dict[str, Any], list[str]]:
    content_type = request.headers.get("content-type", "")
    uploaded_urls: list[str] = []

    if "multipart/form-data" in content_type:
        form = await request.form()
        payload: dict[str, Any] = {key: value for key, value in form.items() if key != "images"}
        files = form.getlist("images")
        uploaded_urls = await _save_uploads(request, files)
        return payload, uploaded_urls

    try:
        payload = await request.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON body") from exc
    return payload or {}, uploaded_urls


async def _save_uploads(request: Request, files: list[Any]) -> list[str]:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    urls: list[str] = []
    base_url = str(request.base_url).rstrip("/")

    for file in files:
        filename = getattr(file, "filename", "") or ""
        if not filename:
            continue
        suffix = Path(filename).suffix.lower()
        if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
            continue
        target_name = f"{uuid4().hex}{suffix}"
        target_path = UPLOAD_DIR / target_name
        target_path.write_bytes(await file.read())
        urls.append(f"{base_url}/uploads/{target_name}")

    return urls


def _payload_image_urls(payload: dict[str, Any], uploaded_urls: list[str]) -> list[str]:
    urls: list[str] = []
    raw_urls = payload.get("imageUrls") or payload.get("image_urls")
    if isinstance(raw_urls, list):
        urls.extend(str(url) for url in raw_urls if url)
    elif isinstance(raw_urls, str) and raw_urls:
        try:
            parsed = json.loads(raw_urls)
            if isinstance(parsed, list):
                urls.extend(str(url) for url in parsed if url)
            else:
                urls.append(raw_urls)
        except json.JSONDecodeError:
            urls.append(raw_urls)

    image_url = payload.get("imageUrl") or payload.get("image_url")
    if image_url and image_url not in urls:
        urls.insert(0, str(image_url))
    urls.extend(uploaded_urls)
    return urls


@router.get("/locations")
async def search_locations(
    keyword: str = "",
    radius: int = Query(1000, ge=100, le=10000),
    sort: str = "distance",
    openNow: bool = False,
    diaperTable: bool = False,
    accessible: bool = False,
    emergencyBell: bool = False,
    recentReview: bool = False,
    db: Session = Depends(get_db),
):
    center_lat, center_lon = _resolve_center(db, keyword)
    query = db.query(Toilet).filter(Toilet.latitude != 0, Toilet.longitude != 0)

    if diaperTable:
        query = query.filter(Toilet.diaper_changing_table.is_(True))
    if accessible:
        query = query.filter(Toilet.handicap_facility.is_(True))
    if emergencyBell:
        query = query.filter(Toilet.emergency_bell.is_(True))

    toilets = query.all()
    results = []
    text_keyword = keyword.strip()

    for toilet in toilets:
        distance = _distance_meters(center_lat, center_lon, toilet.latitude, toilet.longitude)
        text_match = bool(
            text_keyword
            and text_keyword != "화장실"
            and (text_keyword in (toilet.name or "") or text_keyword in (toilet.address or ""))
        )
        if distance > radius and not text_match:
            continue

        normalized = _normalize_restroom(db, toilet, distance)
        normalized["searchCenter"] = {
            "label": text_keyword or "검색 위치",
            "latitude": center_lat,
            "longitude": center_lon,
        }
        if openNow and not normalized["openNow"]:
            continue
        if recentReview and normalized["reviewCount"] <= 0:
            continue
        results.append(normalized)

    if sort == "cleanliness":
        results.sort(key=lambda item: (item["rating"] is None, -(item["rating"] or 0), item["distanceMeters"]))
    elif sort == "reviews":
        results.sort(key=lambda item: (-item["reviewCount"], item["distanceMeters"]))
    else:
        results.sort(key=lambda item: item["distanceMeters"])

    return results[:80]


@router.get("/locations/{restroom_id}")
async def get_location(restroom_id: int, db: Session = Depends(get_db)):
    toilet = db.query(Toilet).filter(Toilet.toilet_id == restroom_id).first()
    if not toilet:
        raise HTTPException(status_code=404, detail="화장실을 찾을 수 없습니다.")
    return _normalize_restroom(db, toilet)


@router.get("/locations/{restroom_id}/reviews")
async def get_location_reviews(restroom_id: int, sort: str = "recent", db: Session = Depends(get_db)):
    toilet = db.query(Toilet).filter(Toilet.toilet_id == restroom_id).first()
    if not toilet:
        raise HTTPException(status_code=404, detail="화장실을 찾을 수 없습니다.")

    reviews: list[dict[str, Any]] = []
    for review in db.query(Review).filter(Review.toilet_id == restroom_id).all():
        reviews.append(
            {
                "id": f"review-{review.review_id}",
                "reviewId": review.review_id,
                "post_id": review.post_id,
                "postId": review.post_id,
                "title": "청결도 리뷰",
                "cleanliness": review.rating,
                "content": review.content or "리뷰 내용이 없습니다.",
                "imageUrls": [],
                "commentCount": 0,
                "createdAt": _client_datetime(review.created_at),
                "createdAtLabel": _time_label(review.created_at),
            }
        )

    for post in db.query(Post).filter(Post.toilet_id == restroom_id).all():
        normalized = _normalize_post(post, _anonymous_name_for_post(db, post))
        reviews.append(
            {
                "id": f"post-{post.post_id}",
                "postId": post.post_id,
                "post_id": post.post_id,
                "title": post.title,
                "cleanliness": post.rating,
                "content": post.content,
                "imageUrls": normalized["imageUrls"],
                "commentCount": post.comment_count or 0,
                "createdAt": _client_datetime(post.created_at),
                "createdAtLabel": _time_label(post.created_at),
            }
        )

    if sort == "rating":
        reviews.sort(key=lambda item: item["cleanliness"], reverse=True)
    else:
        reviews.sort(key=lambda item: item["createdAt"], reverse=True)
    return reviews


@router.get("/posts")
async def list_posts(
    category: str = "전체",
    keyword: str = "",
    sort: str = "recent",
    page: int = Query(1, ge=1),
    size: int = Query(6, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = _post_query(db, category, keyword)
    total = query.count()

    if sort == "rating":
        query = query.order_by(Post.rating.desc(), Post.created_at.desc())
    elif sort == "popular":
        query = query.order_by(Post.recommendation_count.desc(), Post.created_at.desc())
    else:
        query = query.order_by(Post.created_at.desc())

    posts = query.offset((page - 1) * size).limit(size).all()
    return {
        "items": [_normalize_post(post, _anonymous_name_for_post(db, post)) for post in posts],
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/posts/{post_id}")
async def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.post_id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    return _normalize_post(post, _anonymous_name_for_post(db, post))


@router.post("/posts/{post_id}/verify-password")
async def verify_post_password(post_id: int, request: Request, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.post_id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")

    try:
        payload = await request.json()
    except json.JSONDecodeError:
        payload = {}

    if post.password != str(payload.get("password") or ""):
        raise HTTPException(status_code=401, detail="비밀번호가 일치하지 않습니다.")
    return {"ok": True}


@router.post("/posts", status_code=status.HTTP_201_CREATED)
async def create_post(request: Request, db: Session = Depends(get_db)):
    payload, uploaded_urls = await _read_post_payload(request)

    raw_rating = payload.get("rating")
    rating = None if raw_rating in (None, "", "null") else float(raw_rating)
    if rating is not None and (rating < 0 or rating > 5):
        raise HTTPException(status_code=400, detail="청결도는 0점에서 5점 사이여야 합니다.")

    toilet_id = payload.get("restroomId") or payload.get("toilet_id") or payload.get("toiletId")
    toilet_id = int(toilet_id) if toilet_id not in (None, "", "null") else None
    toilet = db.query(Toilet).filter(Toilet.toilet_id == toilet_id).first() if toilet_id else None

    image_urls = _payload_image_urls(payload, uploaded_urls)
    post = Post(
        category=_backend_category(payload.get("category")) or "일반",
        title=str(payload.get("title") or "").strip(),
        content=str(payload.get("content") or "").strip(),
        password=str(payload.get("password") or ""),
        rating=rating,
        image_url=image_urls[0] if image_urls else None,
        image_urls=_dump_image_urls(image_urls),
        nickname=None,
        post_type=str(payload.get("postType") or payload.get("post_type") or "화장실 리뷰"),
        related_place=str(payload.get("relatedPlace") or payload.get("related_place") or payload.get("category") or ""),
        restroom_name=str(payload.get("restroomName") or payload.get("restroom_name") or (toilet.name if toilet else "")),
        toilet_id=toilet_id,
    )

    if not post.title or not post.content or not post.password:
        raise HTTPException(status_code=400, detail="제목, 내용, 비밀번호는 필수입니다.")

    db.add(post)
    db.commit()
    db.refresh(post)
    # If the client created this post from an existing review, link them
    review_id = payload.get("reviewId") or payload.get("review_id")
    if review_id not in (None, "", "null"):
        try:
            rid = int(review_id)
            review_obj = db.query(Review).filter(Review.review_id == rid).first()
            if review_obj:
                review_obj.post_id = post.post_id
                db.commit()
        except Exception:
            # ignore invalid review id or DB errors here; post was already created
            pass

    return _normalize_post(post, _anonymous_name_for_post(db, post))


@router.put("/posts/{post_id}")
async def update_post(post_id: int, request: Request, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.post_id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")

    payload, uploaded_urls = await _read_post_payload(request)
    if post.password != str(payload.get("password") or ""):
        raise HTTPException(status_code=401, detail="비밀번호가 일치하지 않습니다.")

    if "rating" in payload:
        raw_rating = payload.get("rating")
        rating = None if raw_rating in ("", None, "null") else float(raw_rating)
        if rating is not None and (rating < 0 or rating > 5):
            raise HTTPException(status_code=400, detail="청결도는 0점에서 5점 사이여야 합니다.")
        post.rating = rating

    toilet_id = payload.get("restroomId") or payload.get("toilet_id") or payload.get("toiletId")
    if toilet_id not in (None, "", "null"):
        post.toilet_id = int(toilet_id)

    for source_key, attr in [
        ("title", "title"),
        ("content", "content"),
        ("nickname", "nickname"),
        ("postType", "post_type"),
        ("post_type", "post_type"),
        ("relatedPlace", "related_place"),
        ("related_place", "related_place"),
        ("restroomName", "restroom_name"),
        ("restroom_name", "restroom_name"),
    ]:
        if source_key in payload and payload[source_key] not in (None, ""):
            setattr(post, attr, str(payload[source_key]).strip())

    if "category" in payload and payload["category"]:
        post.category = _backend_category(payload["category"]) or str(payload["category"])
        if post.category == "자유게시판":
            post.toilet_id = None
            post.restroom_name = ""
            post.rating = None

    image_urls = _payload_image_urls(payload, uploaded_urls)
    if image_urls or "imageUrls" in payload or "image_urls" in payload:
        post.image_url = image_urls[0] if image_urls else None
        post.image_urls = _dump_image_urls(image_urls)

    post.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(post)
    return _normalize_post(post, _anonymous_name_for_post(db, post))


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: int, request: Request, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.post_id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")

    try:
        payload = await request.json()
    except json.JSONDecodeError:
        payload = {}

    if post.password != str(payload.get("password") or ""):
        raise HTTPException(status_code=401, detail="비밀번호가 일치하지 않습니다.")

    db.delete(post)
    db.commit()
    return None


@router.post("/chat")
async def chat(payload: dict[str, Any], db: Session = Depends(get_db)):
    # Try OpenAI first if configured; on any failure, fall back to rule-based search
    message = str(payload.get("message") or "")
    history = payload.get("history")

    openai_key = os.getenv("OPENAI_API_KEY")
    openai_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    if openai_key:
        try:
            send_messages = history if history else [{"role": "user", "content": message}]
            body = {"model": openai_model, "messages": send_messages}
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {openai_key}"},
                    json=body,
                )
                resp.raise_for_status()
                data = resp.json()
                assistant_text = data.get("choices", [])[0].get("message", {}).get("content", "")
                return {"answer": assistant_text, "locations": [], "warnings": []}
        except Exception:
            # fallback to rule-based behavior below
            pass

    # --- rule-based fallback search (existing behavior) ---
    radius = 1000
    if "2km" in message or "2킬로" in message:
        radius = 2000
    elif "500" in message:
        radius = 500
    elif "200" in message:
        radius = 200

    center_lat, center_lon = _resolve_center(db, message)
    toilets = db.query(Toilet).filter(Toilet.latitude != 0, Toilet.longitude != 0).all()
    matches = []
    for toilet in toilets:
        if "기저귀" in message and not toilet.diaper_changing_table:
            continue
        if "장애" in message and not toilet.handicap_facility:
            continue
        if "비상벨" in message and not toilet.emergency_bell:
            continue
        distance = _distance_meters(center_lat, center_lon, toilet.latitude, toilet.longitude)
        if distance <= radius:
            matches.append(_normalize_restroom(db, toilet, distance))

    matches.sort(key=lambda item: ((item.get("rating") or 0) * -1, item["distanceMeters"]))
    locations = matches[:3]
    if locations:
        answer = f"조건에 가까운 화장실 {len(locations)}곳을 찾았습니다. 거리와 시설 조건을 함께 확인해보세요."
    else:
        answer = "조건에 맞는 화장실을 찾지 못했습니다. 검색 반경이나 조건을 조금 넓혀보세요."

    return {"answer": answer, "locations": locations, "warnings": []}
