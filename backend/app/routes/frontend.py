import json
import math
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4
import os
import logging

import httpx
from dotenv import load_dotenv

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Post, Review, Toilet, Comment

router = APIRouter(prefix="/api", tags=["frontend"])

BACKEND_ROOT = Path(__file__).resolve().parents[2]

# backend/.env 파일을 명시적으로 불러옵니다.
load_dotenv(BACKEND_ROOT / ".env")

logger = logging.getLogger(__name__)

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

    # build comments list if relationship is available
    comments_list: list[dict[str, Any]] = []
    try:
        raw_comments = getattr(post, "comments", []) or []
        for c in raw_comments:
            comments_list.append(
                {
                    "id": c.id,
                    "commentId": c.id,
                    "nickname": c.nickname or "익명의 사용자",
                    "content": c.content,
                    "createdAt": _client_datetime(c.created_at),
                    "updatedAt": _client_datetime(c.updated_at) if getattr(c, "updated_at", None) else "",
                }
            )
    except Exception:
        comments_list = []

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
        "comments": comments_list,
        "commentPreview": comments_list[:3],
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


# --- OpenAI function-calling: FUNCTIONS spec & DB helper ---
FUNCTIONS = [
    {
        "name": "get_nearby_toilets",
        "description": "주어진 좌표 주변의 화장실 목록을 반환합니다. 위치, 거리, 평점, 시설 정보(기저귀, 장애인 등)를 확인해야 할 때 사용합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "latitude": {"type": "number", "description": "사용자 현재 위도"},
                "longitude": {"type": "number", "description": "사용자 현재 경도"},
                "radius": {"type": "integer", "description": "검색 반경(미터). 명시되지 않으면 기본 1000."},
                "sort_by": {"type": "string", "enum": ["distance", "rating"], "description": "정렬 기준. 기본은 distance(거리순). 리뷰/평점순이면 rating."},
                "needs_diaper_table": {"type": "boolean", "description": "기저귀 교환대 필요 여부"},
                "needs_handicap": {"type": "boolean", "description": "장애인 화장실 필요 여부"},
                "needs_emergency_bell": {"type": "boolean", "description": "비상벨 필요 여부"}
            },
            "required": ["latitude", "longitude"]
        }
    }
]


def _execute_get_nearby_toilets(
    db: Session, 
    latitude: float, 
    longitude: float, 
    radius: int = 1000, 
    sort_by: str = "distance",
    needs_diaper_table: bool = False,
    needs_handicap: bool = False,
    needs_emergency_bell: bool = False,
    limit: int = 3
):
    try:
        lat = float(latitude)
        lon = float(longitude)
    except (TypeError, ValueError):
        return []

    items = []
    # 위/경도가 있는 화장실만 조회
    toilets = db.query(Toilet).filter(Toilet.latitude != 0, Toilet.longitude != 0).all()

    for toilet in toilets:
        # OpenAI가 뽑아준 조건 필터링
        if needs_diaper_table and not toilet.diaper_changing_table: continue
        if needs_handicap and not toilet.handicap_facility: continue
        if needs_emergency_bell and not toilet.emergency_bell: continue

        dist = _distance_meters(lat, lon, toilet.latitude, toilet.longitude)
        if dist <= radius:
            items.append(_chat_restroom_summary(db, toilet, dist))

    # 정렬 (OpenAI가 요청한 기준에 따라)
    if sort_by == "rating":
        # 평점 내림차순, 같으면 거리 오름차순
        items.sort(key=lambda i: (-(i.get("rating") or 0), i["distanceMeters"]))
    else:
        # 기본 거리 오름차순
        items.sort(key=lambda i: i["distanceMeters"])

    return items[:limit]


CHAT_FIXED_CURRENT_LOCATION = {
    "label": "역삼역 멀티캠퍼스",
    "latitude": 37.5012743,
    "longitude": 127.0395850,
}

CHAT_RESTROOM_KEYWORDS = (
    "화장실", "공중화장실", "장실", "변기", "기저귀", "장애", "비상벨",
    "개방", "24시간", "청결", "깨끗", "평점", "거리", "가까운", "근처",
    "주변", "위치", "추천",
)
CHAT_REVIEW_KEYWORDS = ("리뷰", "후기", "평점", "평가", "어때", "깨끗", "청결", "좋아")
CHAT_REVIEW_SUMMARY_KEYWORDS = ("리뷰 보여", "리뷰 알려", "리뷰 요약", "후기 보여", "후기 알려", "후기 요약", "어때")
CHAT_COMMUNITY_KEYWORDS = ("커뮤니티", "게시판", "게시글", "글", "자유게시판", "댓글")
CHAT_OFF_TOPIC_KEYWORDS = ("밥", "점심", "저녁", "음식", "영화", "노래", "게임", "공부")
CHAT_FOLLOWUP_KEYWORDS = (
    "개", "곳", "더", "보여줘", "알려줘", "찾아줘", "추천해줘",
    "거리순", "평점순", "리뷰", "후기",
)
CHAT_COUNT_WORDS = {
    "한": 1,
    "하나": 1,
    "두": 2,
    "둘": 2,
    "세": 3,
    "셋": 3,
    "네": 4,
    "넷": 4,
    "다섯": 5,
    "여섯": 6,
}
CHAT_STOPWORDS = {
    "화장실", "공중화장실", "추천", "리뷰", "후기", "평점", "평가", "어때",
    "근처", "주변", "내", "현재", "지금", "위치", "있는", "없는", "좋은",
    "깨끗한", "깨끗", "청결", "장소", "곳", "좀", "봐줘", "알려줘", "찾아줘",
    "해줘", "부탁해", "거리순", "평점순", "가까운", "제일", "가장",
    "대신", "요약해줘", "요약", "어떤지도", "있는걸로",
    "장애인용", "장애인", "시설", "시설이", "있는", "있는걸", "기저귀",
    "교환대", "화장실만", "화장실로", "보여줘",
}


def _chat_contains_any(text: str, keywords: tuple[str, ...] | set[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _compact_text(value: Any, limit: int = 120) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."


def _valid_coordinates(latitude: Any, longitude: Any) -> bool:
    try:
        lat = float(latitude)
        lon = float(longitude)
    except (TypeError, ValueError):
        return False
    return -90 <= lat <= 90 and -180 <= lon <= 180


def _is_short_greeting(message: str) -> bool:
    cleaned = re.sub(r"[\s!?.~]+", "", message.lower())
    return cleaned in {"안녕", "안녕하세요", "하이", "hi", "hello", "ㅎㅇ", "헬로"}


def _chat_requested_limit(message: str, default: int = 3) -> int:
    text = message.strip()
    match = re.search(r"(\d+)\s*(?:개|곳)", text)
    if match:
        return max(1, min(6, int(match.group(1))))

    for word, count in CHAT_COUNT_WORDS.items():
        if re.search(rf"{word}\s*(?:개|곳)", text):
            return count
    return default


def _chat_has_count_request(message: str) -> bool:
    text = message.strip()
    if re.search(r"\d+\s*(?:개|곳)", text):
        return True
    return any(re.search(rf"{word}\s*(?:개|곳)", text) for word in CHAT_COUNT_WORDS)


def _is_chat_followup_request(message: str) -> bool:
    text = message.strip()
    if _chat_has_count_request(text):
        return True
    return _chat_contains_any(text, CHAT_FOLLOWUP_KEYWORDS)


def _classify_chat_intent(message: str) -> str:
    text = message.strip()
    if _is_short_greeting(text):
        return "greeting"
    restroom_keywords_without_recommend = tuple(
        keyword for keyword in CHAT_RESTROOM_KEYWORDS if keyword != "추천"
    )
    if _chat_contains_any(text, CHAT_OFF_TOPIC_KEYWORDS) and not _chat_contains_any(text, restroom_keywords_without_recommend):
        return "general"
    if _chat_contains_any(text, CHAT_COMMUNITY_KEYWORDS):
        return "community"
    if _chat_contains_any(text, ("찾아", "추천", "보여", "알려")) and _chat_contains_any(text, CHAT_RESTROOM_KEYWORDS):
        return "restroom_search"
    if _chat_contains_any(text, CHAT_REVIEW_SUMMARY_KEYWORDS):
        return "review"
    if _chat_contains_any(text, CHAT_REVIEW_KEYWORDS):
        return "restroom_search"
    if _chat_contains_any(text, CHAT_RESTROOM_KEYWORDS):
        return "restroom_search"
    if _is_chat_followup_request(text):
        if _chat_contains_any(text, CHAT_REVIEW_KEYWORDS):
            return "review"
        return "restroom_search"
    return "general"


def _chat_search_tokens(message: str) -> list[str]:
    raw_tokens = re.split(r"[\s,./!?()\[\]{}\"'“”‘’]+", message)
    tokens: list[str] = []
    for token in raw_tokens:
        token = token.strip()
        for suffix in ("에서", "으로", "로", "은", "는", "이", "가", "을", "를", "만"):
            if token.endswith(suffix) and len(token) > len(suffix) + 1:
                token = token[: -len(suffix)]
                break
        if len(token) >= 2 and token not in CHAT_STOPWORDS:
            tokens.append(token)
    return tokens[:6]


def _extract_place_keyword(db: Session, message: str) -> str:
    text = message.strip()
    if not text:
        return ""

    for key in sorted(KEYWORD_CENTERS, key=len, reverse=True):
        if key in text:
            return key

    for district in sorted(DISTRICT_CENTERS, key=len, reverse=True):
        if district in text:
            return district

    for poi in _load_poi_index():
        title = poi["title"]
        if len(title) >= 2 and title in text:
            return title

    match = re.search(r"([가-힣A-Za-z0-9·()\s]{2,30}?)(?:에서|근처|주변|인근|기준)", text)
    if match:
        candidate = match.group(1).strip()
        candidate = re.sub(r"^(?:내|현재|지금)\s*", "", candidate).strip()
        candidate = re.sub(r"(?:화장실|공중화장실)$", "", candidate).strip()
        if candidate and candidate not in CHAT_STOPWORDS:
            return candidate

    return ""


def _chat_history_text(history: Any, current_message: str) -> str:
    if not isinstance(history, list):
        return ""

    snippets: list[str] = []
    for item in reversed(history[-8:]):
        if not isinstance(item, dict):
            continue
        content = str(item.get("content") or "").strip()
        if not content or content == current_message:
            continue
        snippets.append(_compact_text(content, 180))
        if len(snippets) >= 3:
            break
    return " ".join(reversed(snippets))


def _chat_message_with_context(db: Session, message: str, history: Any) -> str:
    if not _is_chat_followup_request(message):
        return message
    if _has_specific_place_hint(db, message) or _is_current_location_request(message):
        return message
    previous = _chat_history_text(history, message)
    if not previous:
        return message
    return f"{message} {previous}"


def _find_toilet_from_message(db: Session, message: str) -> Toilet | None:
    text = message.strip()
    if not text:
        return None

    base_query = db.query(Toilet).filter(Toilet.latitude != 0, Toilet.longitude != 0)
    for toilet in base_query.all():
        name = (toilet.name or "").strip()
        if len(name) >= 2 and name in text:
            return toilet

    for token in _chat_search_tokens(text):
        if len(token) < 3:
            continue
        toilet = (
            base_query
            .filter(Toilet.name.contains(token))
            .first()
        )
        if toilet:
            return toilet
    return None


def _has_specific_place_hint(db: Session, message: str) -> bool:
    text = message.strip()
    if _extract_place_keyword(db, text):
        return True
    if _find_toilet_from_message(db, text):
        return True
    return False


def _is_current_location_request(message: str) -> bool:
    return _chat_contains_any(message, ("내 주변", "현재 위치", "지금 위치", "여기", "근처", "주변"))


def _chat_center_label(db: Session, message: str) -> str:
    text = message.strip()
    place_keyword = _extract_place_keyword(db, text)
    if place_keyword:
        return place_keyword
    toilet = _find_toilet_from_message(db, text)
    if toilet:
        return toilet.name
    return "검색 위치"


def _resolve_chat_center(db: Session, message: str, user_lat: Any = None, user_lon: Any = None) -> dict[str, Any]:
    if _valid_coordinates(user_lat, user_lon):
        return {"label": "현재 위치", "latitude": float(user_lat), "longitude": float(user_lon)}

    if _is_current_location_request(message) and not _has_specific_place_hint(db, message):
        return CHAT_FIXED_CURRENT_LOCATION.copy()

    place_keyword = _extract_place_keyword(db, message)
    center_lat, center_lon = _resolve_center(db, place_keyword or message)
    return {
        "label": place_keyword or _chat_center_label(db, message),
        "latitude": center_lat,
        "longitude": center_lon,
    }


def _chat_radius(message: str) -> int:
    text = message.lower()
    if "2km" in text or "2킬로" in text or "2000" in text:
        return 2000
    if "500" in text:
        return 500
    if "200" in text:
        return 200
    return 1000


def _chat_sort_by(message: str) -> str:
    if "거리" in message or "가까운" in message:
        return "distance"
    if _chat_contains_any(message, ("평점", "리뷰", "후기", "깨끗", "청결", "좋은")):
        return "rating"
    return "distance"


def _chat_conditions(message: str) -> dict[str, bool]:
    needs_review = bool(
        re.search(r"(?:리뷰|후기).{0,8}(?:있는|있|좋은|좋|많은|많)", message)
        or re.search(r"(?:평점|평가).{0,8}(?:좋은|높은|좋|높)", message)
    )
    return {
        "needs_diaper_table": "기저귀" in message,
        "needs_handicap": "장애" in message,
        "needs_emergency_bell": "비상벨" in message,
        "needs_review": needs_review,
    }


def _chat_review_snippets(db: Session, toilet_id: int, limit: int = 3) -> list[dict[str, Any]]:
    snippets: list[dict[str, Any]] = []

    for review in (
        db.query(Review)
        .filter(Review.toilet_id == toilet_id)
        .order_by(Review.created_at.desc())
        .limit(limit)
        .all()
    ):
        snippets.append(
            {
                "title": "청결도 리뷰",
                "rating": review.rating,
                "content": _compact_text(review.content or "리뷰 내용이 없습니다.", 110),
                "createdAtLabel": _time_label(review.created_at),
                "_created_at": review.created_at or datetime.min,
            }
        )

    for post in (
        db.query(Post)
        .filter(Post.toilet_id == toilet_id)
        .order_by(Post.created_at.desc())
        .limit(limit)
        .all()
    ):
        snippets.append(
            {
                "title": _compact_text(post.title, 60),
                "rating": post.rating,
                "content": _compact_text(post.content, 110),
                "createdAtLabel": _time_label(post.created_at),
                "_created_at": post.created_at or datetime.min,
            }
        )

    snippets.sort(key=lambda item: item["_created_at"], reverse=True)
    cleaned = []
    for item in snippets[:limit]:
        item.pop("_created_at", None)
        cleaned.append(item)
    return cleaned


def _chat_restroom_summary(db: Session, toilet: Toilet, distance: float | None = None) -> dict[str, Any]:
    normalized = _normalize_restroom(db, toilet, distance)
    snippets = _chat_review_snippets(db, toilet.toilet_id)
    return {
        "id": normalized["id"],
        "toiletId": normalized["toiletId"],
        "name": normalized["name"],
        "address": normalized["address"],
        "distanceMeters": normalized["distanceMeters"],
        "rating": normalized["rating"],
        "reviewCount": normalized["reviewCount"],
        "latestReview": normalized["latestReview"],
        "latestReviewLabel": normalized["latestReviewLabel"],
        "tags": normalized["tags"],
        "facilities": normalized["facilities"],
        "openNow": normalized["openNow"],
        "openingHours": normalized["openingHours"],
        "latitude": normalized["latitude"],
        "longitude": normalized["longitude"],
        "mapPosition": normalized["mapPosition"],
        "reviewSnippets": snippets,
        "diaper_table": bool(toilet.diaper_changing_table),
        "handicap": bool(toilet.handicap_facility),
        "emergency_bell": bool(toilet.emergency_bell),
    }


def _search_chat_restrooms(
    db: Session,
    message: str,
    user_lat: Any = None,
    user_lon: Any = None,
    limit: int = 3,
) -> dict[str, Any]:
    center = _resolve_chat_center(db, message, user_lat, user_lon)
    radius = _chat_radius(message)
    sort_by = _chat_sort_by(message)
    conditions = _chat_conditions(message)

    query = db.query(Toilet).filter(Toilet.latitude != 0, Toilet.longitude != 0)
    if conditions["needs_diaper_table"]:
        query = query.filter(Toilet.diaper_changing_table.is_(True))
    if conditions["needs_handicap"]:
        query = query.filter(Toilet.handicap_facility.is_(True))
    if conditions["needs_emergency_bell"]:
        query = query.filter(Toilet.emergency_bell.is_(True))

    def collect_items(search_radius: int) -> list[dict[str, Any]]:
        collected: list[dict[str, Any]] = []
        for toilet in query.all():
            distance = _distance_meters(center["latitude"], center["longitude"], toilet.latitude, toilet.longitude)
            if distance > search_radius:
                continue
            summary = _chat_restroom_summary(db, toilet, distance)
            if conditions["needs_review"] and summary["reviewCount"] <= 0:
                continue
            collected.append(summary)
        return collected

    items = collect_items(radius)
    expanded_radius = radius
    if conditions["needs_review"] and not items and radius < 3000:
        expanded_radius = 3000
        items = collect_items(expanded_radius)

    if sort_by == "rating":
        items.sort(key=lambda item: (-(item["rating"] or 0), -item["reviewCount"], item["distanceMeters"]))
    else:
        items.sort(key=lambda item: item["distanceMeters"])

    return {
        "center": center,
        "radius": expanded_radius,
        "sortBy": sort_by,
        "conditions": conditions,
        "items": items[:limit],
    }


def _chat_post_summary(db: Session, post: Post) -> dict[str, Any]:
    normalized = _normalize_post(post, _anonymous_name_for_post(db, post))
    return {
        "id": normalized["id"],
        "title": _compact_text(normalized["title"], 70),
        "content": _compact_text(normalized["content"], 130),
        "category": normalized["category"],
        "restroomId": normalized["restroomId"],
        "restroomName": normalized["restroomName"],
        "rating": normalized["rating"],
        "recommendationCount": normalized["recommendationCount"],
        "createdAtLabel": normalized["createdAtLabel"],
    }


def _search_chat_posts(
    db: Session,
    message: str,
    focus_toilet: Toilet | None = None,
    limit: int = 4,
) -> list[dict[str, Any]]:
    query = db.query(Post)
    if focus_toilet:
        query = query.filter(Post.toilet_id == focus_toilet.toilet_id)
    else:
        conditions = []
        for token in _chat_search_tokens(message):
            like = f"%{token}%"
            conditions.extend(
                [
                    Post.title.like(like),
                    Post.content.like(like),
                    Post.related_place.like(like),
                    Post.restroom_name.like(like),
                ]
            )
        if conditions:
            query = query.filter(or_(*conditions))

    if _chat_sort_by(message) == "rating":
        query = query.order_by(Post.rating.desc(), Post.recommendation_count.desc(), Post.created_at.desc())
    else:
        query = query.order_by(Post.created_at.desc())

    return [_chat_post_summary(db, post) for post in query.limit(limit).all()]


def _build_chat_context(
    db: Session,
    message: str,
    history: Any = None,
    user_lat: Any = None,
    user_lon: Any = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    intent = _classify_chat_intent(message)
    lookup_message = _chat_message_with_context(db, message, history)
    requested_limit = _chat_requested_limit(message)
    context: dict[str, Any] = {
        "intent": intent,
        "message": message,
        "lookupMessage": lookup_message,
        "requestedLimit": requested_limit,
        "needsPlace": False,
        "restrooms": [],
        "communityPosts": [],
    }

    if intent == "general":
        place_info = _chat_place_info(db, message)
        if place_info:
            context["placeInfo"] = place_info
        return context, []

    if intent == "greeting":
        return context, []

    focus_toilet = _find_toilet_from_message(db, lookup_message)
    place_keyword = _extract_place_keyword(db, lookup_message)
    has_place = (
        bool(place_keyword)
        or focus_toilet is not None
        or _valid_coordinates(user_lat, user_lon)
        or _is_current_location_request(lookup_message)
    )

    if not has_place:
        context["needsPlace"] = True
        count_text = f" {requested_limit}곳" if _chat_has_count_request(message) else ""
        context["question"] = f"어느 장소 기준으로{count_text} 찾아볼까요? 예: 강남역, 경복궁, 역삼역처럼 입력해 주세요."
        return context, []

    if focus_toilet and intent in {"review", "community"}:
        focused = _chat_restroom_summary(db, focus_toilet)
        context["focusedRestroom"] = focused
        context["communityPosts"] = _search_chat_posts(db, lookup_message, focus_toilet)
        return context, [focused]

    search_result = _search_chat_restrooms(
        db,
        lookup_message,
        user_lat,
        user_lon,
        limit=requested_limit,
    )
    context.update(
        {
            "center": search_result["center"],
            "radius": search_result["radius"],
            "sortBy": search_result["sortBy"],
            "conditions": search_result["conditions"],
            "restrooms": search_result["items"],
        }
    )

    if intent in {"review", "community"}:
        context["communityPosts"] = _search_chat_posts(db, lookup_message)

    return context, search_result["items"]


def _trim_chat_answer(answer: str, max_chars: int = 360) -> str:
    text = " ".join(str(answer or "").split())
    if len(text) <= max_chars:
        return text

    sentences = re.split(r"(?<=[.!?。！？])\s+", text)
    picked: list[str] = []
    current_length = 0
    for sentence in sentences:
        if current_length + len(sentence) > max_chars:
            break
        picked.append(sentence)
        current_length += len(sentence)
        if len(picked) >= 3:
            break
    if picked:
        return " ".join(picked)
    return text[:max_chars].rstrip() + "..."


# def _fallback_chat_answer(context: dict[str, Any]) -> str:
    intent = context.get("intent")
    if intent == "greeting":
        return "안녕하세요! 장소나 조건을 말해주시면 가까운 화장실을 찾아드릴게요."
    if intent == "general":
        place_info = context.get("placeInfo")
        if place_info:
            address = f" 위치는 {place_info['address']} 쪽이에요." if place_info.get("address") else ""
            return f"네, {place_info['title']} 알아요. 서울의 {place_info['category']}로 볼 수 있는 장소예요.{address}"
        return "좋아요. 편하게 물어보세요."
    if context.get("needsPlace"):
        return context.get("question") or "어느 장소 기준으로 찾아볼까요?"

    focused = context.get("focusedRestroom")
    if focused:
        rating = focused["rating"]
        snippets = focused.get("reviewSnippets") or []
        rating_text = "리뷰 없음" if rating is None else f"평점 {rating}"
        if snippets:
            return f"{focused['name']}은 {rating_text}이고, 최근 후기는 '{snippets[0]['content']}' 정도로 요약돼요."
        return f"{focused['name']}은 {rating_text}이에요. 아직 자세한 리뷰는 많지 않습니다."

    restrooms = context.get("restrooms") or []
    if restrooms:
        best = restrooms[0]
        rating_text = "리뷰 없음" if best["rating"] is None else f"평점 {best['rating']}"
        return f"{context.get('center', {}).get('label', '검색 위치')} 기준으로는 {best['name']}가 좋아 보여요. {best['distanceMeters']}m 거리이고 {rating_text}입니다."

    return "조건에 맞는 화장실을 찾지 못했어요. 위치나 반경을 조금 넓혀보세요."
def _fallback_chat_answer(
    context: dict[str, Any],
    message: str = "",
) -> str:
    """
    OpenAI API 호출이 실패했을 때만 사용하는 기본 답변입니다.
    정상적인 일반 대화는 OpenAI가 처리합니다.
    """

    intent = context.get("intent")

    cleaned_message = re.sub(
        r"[\s!?.~]+",
        "",
        message.lower(),
    )

    if intent == "greeting":
        return "안녕하세요! 반가워요. 오늘은 어떤 이야기를 해볼까요?"

    if intent == "general":
        place_info = context.get("placeInfo")

        if place_info:
            address = (
                f" 위치는 {place_info['address']} 쪽이에요."
                if place_info.get("address")
                else ""
            )

            return (
                f"네, {place_info['title']} 알아요. "
                f"서울의 {place_info['category']}로 볼 수 있는 장소예요."
                f"{address}"
            )

        if cleaned_message in {
            "야",
            "저기",
            "있잖아",
            "챗봇아",
        }:
            return "네, 듣고 있어요. 무슨 일이에요?"

        # API 연결 실패 상황임을 솔직하게 표시합니다.
        return (
            "지금 AI 대화 연결이 원활하지 않아요. "
            "잠시 후 다시 말해 주세요."
        )

    if context.get("needsPlace"):
        return (
            context.get("question")
            or "어느 장소를 기준으로 찾아볼까요?"
        )

    focused = context.get("focusedRestroom")

    if focused:
        rating = focused.get("rating")
        snippets = focused.get("reviewSnippets") or []

        rating_text = (
            "리뷰 없음"
            if rating is None
            else f"평점 {rating}"
        )

        if snippets:
            return (
                f"{focused['name']}은 {rating_text}이고, "
                f"최근 후기는 '{snippets[0]['content']}' 정도로 요약돼요."
            )

        return (
            f"{focused['name']}은 {rating_text}이에요. "
            "아직 자세한 리뷰는 많지 않습니다."
        )

    restrooms = context.get("restrooms") or []

    if restrooms:
        best = restrooms[0]
        rating = best.get("rating")

        rating_text = (
            "리뷰 없음"
            if rating is None
            else f"평점 {rating}"
        )

        center_label = (
            context.get("center", {}).get("label")
            or "검색 위치"
        )

        return (
            f"{center_label} 기준으로는 {best['name']}가 가까워요. "
            f"{best['distanceMeters']}m 거리이고 {rating_text}입니다."
        )

    return (
        "조건에 맞는 화장실을 찾지 못했어요. "
        "위치나 검색 반경을 조금 넓혀보세요."
    )

def _chat_place_info(db: Session, message: str) -> dict[str, Any] | None:
    keyword = _extract_place_keyword(db, message)
    if not keyword:
        return None

    for poi in _load_poi_index():
        title = poi["title"]
        if keyword == title or keyword in title or title in keyword:
            return {
                "title": title,
                "address": poi.get("address", ""),
                "category": poi.get("category", "장소"),
                "latitude": poi.get("latitude"),
                "longitude": poi.get("longitude"),
            }

    if keyword in KEYWORD_CENTERS:
        lat, lon = KEYWORD_CENTERS[keyword]
        return {"title": keyword, "address": "", "category": "장소", "latitude": lat, "longitude": lon}
    if keyword in DISTRICT_CENTERS:
        lat, lon = DISTRICT_CENTERS[keyword]
        return {"title": keyword, "address": "", "category": "서울 자치구", "latitude": lat, "longitude": lon}
    return None


def _openai_content_from_response(data: dict[str, Any]) -> str:
    message = (data.get("choices") or [{}])[0].get("message") or {}
    content = message.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                parts.append(str(item.get("text") or item.get("content") or ""))
            else:
                parts.append(str(item))
        return " ".join(part for part in parts if part)
    return str(content or "")


# async def _call_openai_chat(openai_key: str, openai_model: str, messages: list[dict[str, str]]) -> str:
#     base_payload = {"model": openai_model, "messages": messages}
#     payloads = [
#         {**base_payload, "max_completion_tokens": 220},
#         {**base_payload, "max_tokens": 220, "temperature": 0.4},
#         base_payload,
#     ]
#     last_error: Exception | None = None

#     async with httpx.AsyncClient(timeout=30.0) as client:
#         for body in payloads:
#             try:
#                 response = await client.post(
#                     "https://api.openai.com/v1/chat/completions",
#                     headers={"Authorization": f"Bearer {openai_key}"},
#                     json=body,
#                 )
#                 response.raise_for_status()
#                 return _openai_content_from_response(response.json())
#             except httpx.HTTPStatusError as exc:
#                 last_error = exc
#                 if exc.response.status_code not in {400, 422}:
#                     break
#             except Exception as exc:
#                 last_error = exc
#                 break

#     if last_error:
#         raise last_error
#     return ""
async def _call_openai_chat(
    openai_key: str,
    openai_model: str,
    messages: list[dict[str, str]],
) -> str:
    """
    OpenAI Chat Completions API를 호출하고
    실제 챗봇 답변 문자열을 반환합니다.
    """

    body = {
        "model": openai_model,
        "messages": messages,

        # 기존 220은 추론 토큰까지 포함하면 너무 작을 수 있습니다.
        # 답변이 비는 현상을 방지하기 위해 여유 있게 설정합니다.
        "max_completion_tokens": 1000,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {openai_key}",
                "Content-Type": "application/json",
            },
            json=body,
        )

    if response.is_error:
        # API 키는 출력하지 않고 OpenAI 오류 내용만 확인합니다.
        error_text = response.text[:1000]

        raise RuntimeError(
            f"OpenAI API error {response.status_code}: {error_text}"
        )

    data = response.json()
    choices = data.get("choices") or []

    if not choices:
        raise RuntimeError(
            f"OpenAI 응답에 choices가 없습니다: {str(data)[:500]}"
        )

    assistant_text = _openai_content_from_response(data).strip()

    if not assistant_text:
        choice = choices[0]

        raise RuntimeError(
            "OpenAI가 빈 답변을 반환했습니다. "
            f"finish_reason={choice.get('finish_reason')}, "
            f"usage={data.get('usage')}"
        )

    return assistant_text


def _sanitize_chat_history(history: Any) -> list[dict[str, str]]:
    """
    프론트에서 전달받은 history를
    OpenAI가 이해할 수 있는 메시지 형식으로 정리합니다.
    """

    if not isinstance(history, list):
        return []

    role_aliases = {
        "user": "user",
        "assistant": "assistant",

        # 프론트에서 bot 또는 ai로 보내는 경우를 대비합니다.
        "bot": "assistant",
        "ai": "assistant",
    }

    cleaned_history: list[dict[str, str]] = []

    for item in history[-8:]:
        if not isinstance(item, dict):
            continue

        raw_role = str(item.get("role") or "").lower()
        role = role_aliases.get(raw_role)
        content = item.get("content")

        if not role:
            continue

        if not isinstance(content, str):
            continue

        content = content.strip()

        if not content:
            continue

        cleaned_history.append({
            "role": role,
            "content": content,
        })

    return cleaned_history


def _openai_service_context(
    context: dict[str, Any],
    locations: list[dict[str, Any]],
) -> str:
    """
    일반 대화에는 DB 검색 결과를 넣지 않고,
    화장실 검색이나 리뷰 질문일 때만 DB 데이터를 전달합니다.
    """

    intent = context.get("intent")

    if intent in {"greeting", "general"}:
        return (
            "현재 요청은 일반 대화입니다. "
            "화장실 이야기를 억지로 꺼내지 말고 "
            "사용자가 한 말에 직접 자연스럽게 답하세요."
        )

    safe_locations: list[dict[str, Any]] = []

    for location in locations[:6]:
        safe_locations.append({
            "name": location.get("name"),
            "address": location.get("address"),
            "distanceMeters": location.get("distanceMeters"),
            "rating": location.get("rating"),
            "reviewCount": location.get("reviewCount"),
            "openingHours": location.get("openingHours"),
            "openNow": location.get("openNow"),
            "tags": location.get("tags") or [],
            "facilities": location.get("facilities") or {},
            "latestReview": location.get("latestReview"),
            "reviewSnippets": (
                location.get("reviewSnippets") or []
            )[:3],
        })

    service_data = {
        "intent": intent,
        "needsPlace": context.get("needsPlace", False),
        "question": context.get("question"),
        "center": context.get("center"),
        "sortBy": context.get("sortBy"),
        "conditions": context.get("conditions"),
        "locations": safe_locations,
        "communityPosts": (
            context.get("communityPosts") or []
        )[:4],
    }

    return (
        "아래는 백엔드 DB에서 실제로 조회한 서비스 데이터입니다.\n"
        "화장실 위치, 추천, 시설, 평점, 리뷰에 대한 답변은 "
        "반드시 이 데이터만 근거로 작성하세요.\n"
        "데이터에 없는 내용은 추측하거나 만들어내지 마세요.\n\n"
        + json.dumps(
            service_data,
            ensure_ascii=False,
            default=str,
            indent=2,
        )
    )

def _rating_text(rating: Any) -> str:
    return "리뷰 없음" if rating is None else f"평점 {rating}"


def _format_review_snippets(restroom: dict[str, Any], limit: int = 2) -> str:
    snippets = restroom.get("reviewSnippets") or []
    if not snippets:
        return f"{restroom['name']}: 아직 등록된 리뷰가 없습니다."

    parts = []
    for snippet in snippets[:limit]:
        rating = snippet.get("rating")
        rating_label = "" if rating is None else f"평점 {rating}, "
        parts.append(f"{restroom['name']}: {rating_label}{snippet.get('content')}")
    return " / ".join(parts)


def _direct_service_chat_answer(context: dict[str, Any]) -> str | None:
    intent = context.get("intent")
    if intent == "greeting":
        return None
    if intent == "general":
        if context.get("placeInfo"):
            return _fallback_chat_answer(context)
        return None
    if context.get("needsPlace"):
        return _fallback_chat_answer(context)

    focused = context.get("focusedRestroom")
    if focused and intent in {"review", "community"}:
        return _format_review_snippets(focused, limit=3)

    restrooms = context.get("restrooms") or []
    center_label = (context.get("center") or {}).get("label") or "검색 위치"
    requested_limit = int(context.get("requestedLimit") or 3)

    if intent in {"review", "community"}:
        if not restrooms:
            return f"{center_label} 주변에서 확인할 리뷰를 찾지 못했어요."

        with_reviews = [item for item in restrooms if item.get("reviewSnippets")]
        targets = with_reviews[: min(2, requested_limit)] or restrooms[: min(2, requested_limit)]
        review_text = " / ".join(_format_review_snippets(item, limit=1) for item in targets)
        return f"{center_label} 주변 리뷰를 바로 보면, {review_text}"

    if intent == "restroom_search":
        if not restrooms:
            conditions = context.get("conditions") or {}
            if conditions.get("needs_review"):
                return f"{center_label} 주변에서 리뷰가 등록된 화장실을 찾지 못했어요."
            return f"{center_label} 주변에서 조건에 맞는 화장실을 찾지 못했어요."

        count = len(restrooms)
        sort_label = "평점순" if context.get("sortBy") == "rating" else "거리순"
        if count < requested_limit:
            return f"{center_label} 기준 {sort_label}으로 현재 조건에서 {count}곳 찾았어요."
        return f"{center_label} 기준 {sort_label}으로 {count}곳 찾았어요."

    return None


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


def _normalize_comment(comment: Comment) -> dict[str, Any]:
    return {
        "id": comment.id,
        "commentId": comment.id,
        "nickname": comment.nickname or "익명의 사용자",
        "content": comment.content,
        "createdAt": _client_datetime(comment.created_at),
        "updatedAt": _client_datetime(comment.updated_at) if getattr(comment, "updated_at", None) else "",
    }


@router.post("/posts/{post_id}/comments", status_code=status.HTTP_201_CREATED)
async def create_comment(post_id: int, request: Request, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.post_id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")

    try:
        payload = await request.json()
    except json.JSONDecodeError:
        payload = {}

    nickname = str(payload.get("nickname") or "").strip() or "익명의 사용자"
    password = str(payload.get("password") or "")
    content = str(payload.get("content") or "").strip()

    if not content or not password:
        raise HTTPException(status_code=400, detail="내용과 비밀번호는 필수입니다.")

    comment = Comment(post_id=post_id, nickname=nickname, password=password, content=content)
    db.add(comment)
    post.comment_count = (post.comment_count or 0) + 1
    db.commit()
    db.refresh(comment)
    return _normalize_comment(comment)


@router.put("/posts/{post_id}/comments/{comment_id}")
async def update_comment(post_id: int, comment_id: int, request: Request, db: Session = Depends(get_db)):
    comment = db.query(Comment).filter(Comment.id == comment_id, Comment.post_id == post_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")

    try:
        payload = await request.json()
    except json.JSONDecodeError:
        payload = {}

    if comment.password != str(payload.get("password") or ""):
        raise HTTPException(status_code=401, detail="비밀번호가 일치하지 않습니다.")

    if "content" in payload and payload.get("content") not in (None, ""):
        comment.content = str(payload.get("content") or "").strip()
    if "nickname" in payload and payload.get("nickname") not in (None, ""):
        comment.nickname = str(payload.get("nickname") or "").strip()

    comment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(comment)
    return _normalize_comment(comment)


@router.delete("/posts/{post_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(post_id: int, comment_id: int, request: Request, db: Session = Depends(get_db)):
    comment = db.query(Comment).filter(Comment.id == comment_id, Comment.post_id == post_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")

    try:
        payload = await request.json()
    except json.JSONDecodeError:
        payload = {}

    if comment.password != str(payload.get("password") or ""):
        raise HTTPException(status_code=401, detail="비밀번호가 일치하지 않습니다.")

    post = db.query(Post).filter(Post.post_id == post_id).first()
    db.delete(comment)
    if post:
        post.comment_count = max(0, (post.comment_count or 0) - 1)
    db.commit()
    return None


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
    message = str(payload.get("message") or "").strip()
    if not message:
        intro = (
            "안녕하세요! 화장실록 챗봇입니다. 궁금하신 화장실 위치나 이용 후기를 간단히 알려드릴게요."
        )
        return {"answer": intro, "locations": [], "warnings": []}

    history = payload.get("history", [])
    user_lat = payload.get("latitude")
    user_lon = payload.get("longitude")

    # 1. 문맥과 검색 결과 분석
    context, locations = _build_chat_context(db, message, history, user_lat, user_lon)
    intent = context.get("intent") # intent 추출 ('greeting', 'general', 'restroom_search' 등)

    openai_key = os.getenv("OPENAI_API_KEY")
    openai_model = os.getenv("OPENAI_MODEL")

    if not openai_key:
        return {"answer": _fallback_chat_answer(context), "locations": locations, "warnings": []}

    try:
        # 2. 의도(Intent)에 따라 시스템 프롬프트 분기 처리
        if intent in ("greeting", "general"):
            # 인사말이나 일상 대화일 때는 자유롭고 친절한 페르소나 부여
            system_content = (
                "당신은 친절하고 유쾌한 '화장실록' 서비스의 마스코트 AI 어시스턴트입니다. "
                "사용자의 인사나 가벼운 질문에 친근하고 센스 있게 한국어로 답해 주세요. "
                "궁금한 화장실 위치나 조건(예: '역삼역 근처 기저귀 교환대 있는 화장실')을 물어보면 "
                "언제든 찾아줄 수 있다고 자연스럽게 안내해 주세요."
            )
        else:
            # 화장실 검색, 리뷰, 커뮤니티 조회 등의 실무적인 질문일 때
            context_text = ""
            if locations:
                context_text = "다음은 검색된 화장실 목록입니다:\n"
                for loc in locations:
                    rating = f"평점 {loc.get('rating')}" if loc.get("rating") else "리뷰 없음"
                    context_text += f"- {loc.get('name')} (거리: {loc.get('distanceMeters')}m, {rating})\n"
            
            system_content = (
                "당신은 '화장실록' 서비스의 AI 어시스턴트입니다. "
                "아래 제공된 [화장실 검색 결과]를 바탕으로 사용자 질문에 친절하고 간결하게 한국어로 답하세요. "
                "검색 결과에 없는 정보는 지어내지 마세요.\n\n"
                f"[화장실 검색 결과]\n{context_text}"
            )

        system_message = {
            "role": "system",
            "content": system_content,
        }
        
        # 3. 메시지 대화 목록 구성 (빈 대화 방어 로직 추가)
        messages = [system_message]
        if isinstance(history, list):
            for h in history[-4:]:
                role = h.get("role")
                content = h.get("content")
                # content가 존재하고 빈 문자열이 아닐 때만 추가 (빈 값이면 OpenAI가 응답을 거부할 수 있음)
                if role and content and isinstance(content, str) and content.strip():
                    messages.append({"role": role, "content": content.strip()})
                    
        messages.append({"role": "user", "content": message})

        # 4. OpenAI 호출
        assistant_text = await _call_openai_chat(openai_key, openai_model, messages)
        
        # 5. 빈 말풍선 방지 로직: AI가 알 수 없는 이유로 빈 응답을 주면 안전한 기본 답변으로 강제 교체
        if not assistant_text or not assistant_text.strip():
            assistant_text = _fallback_chat_answer(context)

        return {"answer": _trim_chat_answer(assistant_text), "locations": locations, "warnings": []}
        
    except Exception as exc:
        return {"answer": _fallback_chat_answer(context), "locations": locations, "warnings": [str(type(exc).__name__)]}
