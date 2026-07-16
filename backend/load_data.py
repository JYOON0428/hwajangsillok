import csv
import hashlib
import json
import os
import time
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.models import Post, Toilet, Comment
import random

BACKEND_ROOT = Path(__file__).resolve().parent
TOILET_FILE_NAME = "공중화장실정보_서울특별시.csv"
KAKAO_ADDRESS_SEARCH_URL = "https://dapi.kakao.com/v2/local/search/address.json"
GEOCODE_CACHE_PATH = BACKEND_ROOT / "data" / "geocode_cache.json"

DEFAULT_CENTER = (37.5665, 126.9780)
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

PLACE_CENTERS = {
    "서울숲": (37.5430715815, 127.0417984460),
    "강남역": (37.4979, 127.0276),
    "경복궁": (37.5760307000, 126.9767218661),
    "국립중앙박물관": (37.5239, 126.9804),
    "대학로": (37.5805669329, 127.0023878907),
    "아이파크몰": (37.5298249324, 126.9647566449),
    "남산": (37.5510545366, 126.9878820833),
    "명동": (37.5636, 126.9822),
    "코엑스": (37.5118, 127.0592),
    "여의도": (37.5268, 126.9237),
}

SAMPLE_PLACES = [
    {
        "name": "서울숲",
        "lat": 37.5430715815,
        "lon": 127.0417984460,
        "category": "관광지",
        "title": "서울숲 산책 후 쓰기 좋은 화장실",
        "content": "방문객이 많았지만 내부가 밝고 관리 상태가 안정적이었습니다.",
        "rating": 4.6,
        "nickname": "푸른 여행자",
    },
    {
        "name": "경복궁",
        "lat": 37.5760307000,
        "lon": 126.9767218661,
        "category": "관광지",
        "title": "경복궁 근처 가족 방문 후기",
        "content": "아이와 함께 이동하기 편했고, 주변 개방화장실 안내도 찾기 쉬웠습니다.",
        "rating": 4.2,
        "nickname": "궁궐 산책러",
    },
    {
        "name": "국립중앙박물관",
        "lat": 37.5239,
        "lon": 126.9804,
        "category": "문화시설",
        "title": "박물관 관람 전 확인한 화장실",
        "content": "유모차 동선이 무난했고 세면대 주변 관리도 괜찮았습니다.",
        "rating": 4.8,
        "nickname": "조용한 관람객",
    },
    {
        "name": "대학로",
        "lat": 37.5805669329,
        "lon": 127.0023878907,
        "category": "축제/공연",
        "title": "공연 종료 직후에는 조금 혼잡해요",
        "content": "공연이 끝나는 시간대에는 줄이 생겼지만 회전은 빠른 편이었습니다.",
        "rating": 3.5,
        "nickname": "빠른 시민",
    },
    {
        "name": "아이파크몰 용산점",
        "lat": 37.5298249324,
        "lon": 126.9647566449,
        "category": "쇼핑",
        "title": "용산 쇼핑 동선에서 가까운 화장실",
        "content": "층별 편차가 있지만 상층부는 비교적 덜 붐비고 깨끗했습니다.",
        "rating": 4.1,
        "nickname": "깨끗한 탐험가",
    },
]


def load_local_env() -> None:
    env_path = BACKEND_ROOT / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_local_env()


def int_value(raw: str | None) -> int:
    try:
        return int(str(raw or "0").strip() or 0)
    except ValueError:
        return 0


def yes(raw: str | None) -> bool:
    return str(raw or "").strip().upper() == "Y"


def fallback_coordinates_for(address: str, name: str) -> tuple[float, float]:
    searchable = f"{address} {name}"
    base = DEFAULT_CENTER
    jitter_scale = (0.018, 0.024)
    for place, center in PLACE_CENTERS.items():
        if place in searchable:
            base = center
            jitter_scale = (0.004, 0.006)
            break
    else:
        for district, center in DISTRICT_CENTERS.items():
            if district in address:
                base = center
                break

    digest = hashlib.sha1(f"{address}|{name}".encode("utf-8")).hexdigest()
    lat_seed = int(digest[:6], 16) / 0xFFFFFF
    lon_seed = int(digest[6:12], 16) / 0xFFFFFF
    lat_offset = (lat_seed - 0.5) * jitter_scale[0]
    lon_offset = (lon_seed - 0.5) * jitter_scale[1]
    return round(base[0] + lat_offset, 8), round(base[1] + lon_offset, 8)


def load_geocode_cache() -> dict[str, dict]:
    if not GEOCODE_CACHE_PATH.exists():
        return {}
    try:
        return json.loads(GEOCODE_CACHE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_geocode_cache(cache: dict[str, dict]) -> None:
    GEOCODE_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    GEOCODE_CACHE_PATH.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def kakao_geocode(address: str, cache: dict[str, dict]) -> dict | None:
    rest_api_key = os.getenv("KAKAO_REST_API_KEY", "").strip()
    if not rest_api_key:
        return None

    query = address.strip()
    if not query:
        return None
    if query in cache:
        cached = cache[query]
        return cached if cached.get("status") == "ok" else None

    params = urlencode({"query": query, "size": 1})
    request = Request(
        f"{KAKAO_ADDRESS_SEARCH_URL}?{params}",
        headers={"Authorization": f"KakaoAK {rest_api_key}"},
        method="GET",
    )

    try:
        with urlopen(request, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        cache[query] = {
            "source": "kakao",
            "status": "error",
            "message": str(exc),
        }
        return None

    documents = payload.get("documents") or []
    if not documents:
        cache[query] = {
            "source": "kakao",
            "status": "not_found",
        }
        return None

    document = documents[0]
    result = {
        "source": "kakao",
        "status": "ok",
        "latitude": float(document["y"]),
        "longitude": float(document["x"]),
        "address": document.get("address_name") or query,
    }
    cache[query] = result

    delay = float(os.getenv("KAKAO_GEOCODE_DELAY", "0.03") or 0)
    if delay > 0:
        time.sleep(delay)
    return result


def coordinates_for(address: str, name: str, cache: dict[str, dict]) -> dict:
    geocoded = kakao_geocode(address, cache)
    if geocoded:
        return {
            "latitude": geocoded["latitude"],
            "longitude": geocoded["longitude"],
            "geocoded_address": geocoded["address"],
            "geocode_source": "kakao",
            "geocode_status": "ok",
        }

    latitude, longitude = fallback_coordinates_for(address, name)
    status = "no_api_key" if not os.getenv("KAKAO_REST_API_KEY", "").strip() else "fallback"
    return {
        "latitude": latitude,
        "longitude": longitude,
        "geocoded_address": None,
        "geocode_source": "fallback",
        "geocode_status": status,
    }


def resolve_csv_path() -> Path:
    candidates = [
        os.getenv("TOILET_CSV_PATH"),
        BACKEND_ROOT / "data" / "toilet" / TOILET_FILE_NAME,
        Path.home() / "Desktop" / "dataset" / "toilet" / TOILET_FILE_NAME,
    ]
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate)
        if path.exists():
            return path
    raise FileNotFoundError("공중화장실 CSV 파일을 찾지 못했습니다.")


def open_csv(path: Path):
    for encoding in ("utf-8-sig", "cp949"):
        try:
            handle = path.open("r", encoding=encoding, newline="")
            handle.readline()
            handle.seek(0)
            return handle
        except UnicodeDecodeError:
            continue
    return path.open("r", encoding="utf-8", newline="")


def reset_database() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def load_toilet_data(csv_file_path: Path) -> int:
    db = SessionLocal()
    count = 0
    cache = load_geocode_cache()
    kakao_count = 0
    fallback_count = 0
    try:
        with open_csv(csv_file_path) as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                name = (row.get("화장실명") or "").strip()
                address = (row.get("소재지도로명주소") or row.get("소재지지번주소") or "").strip()
                if not name or not address:
                    continue

                coordinate = coordinates_for(address, name, cache)
                if coordinate["geocode_source"] == "kakao":
                    kakao_count += 1
                else:
                    fallback_count += 1
                disabled_count = sum(
                    int_value(row.get(column))
                    for column in (
                        "남성용-장애인용대변기수",
                        "남성용-장애인용소변기수",
                        "여성용-장애인용대변기수",
                    )
                )

                toilet = Toilet(
                    name=name,
                    address=address,
                    latitude=coordinate["latitude"],
                    longitude=coordinate["longitude"],
                    male_toilet_count=int_value(row.get("남성용-대변기수")),
                    female_toilet_count=int_value(row.get("여성용-대변기수")),
                    male_urinal_count=int_value(row.get("남성용-소변기수")),
                    female_urinal_count=0,
                    handicap_facility=disabled_count > 0,
                    emergency_bell=yes(row.get("비상벨설치여부")),
                    diaper_changing_table=yes(row.get("기저귀교환대유무")),
                    phone=(row.get("전화번호") or "").strip() or None,
                    opening_hours=(row.get("개방시간") or "").strip() or None,
                    open_time_detail=(row.get("개방시간상세") or "").strip() or None,
                    data_reference_date=(row.get("데이터기준일자") or "").strip() or None,
                    entrance_cctv=yes(row.get("화장실입구CCTV설치유무")),
                    toilet_type=(row.get("구분명") or "").strip() or None,
                    managing_agency=(row.get("관리기관명") or "").strip() or None,
                    geocoded_address=coordinate["geocoded_address"],
                    geocode_source=coordinate["geocode_source"],
                    geocode_status=coordinate["geocode_status"],
                )
                db.add(toilet)
                count += 1
                if count % 500 == 0:
                    db.commit()
                    save_geocode_cache(cache)
                    print(f"Loaded {count} toilets...")

        db.commit()
        save_geocode_cache(cache)
        print(f"Geocoded by Kakao: {kakao_count}, fallback: {fallback_count}")
        return count
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    import math

    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371000 * 2 * math.asin(math.sqrt(a))


def find_nearest_toilet(db: Session, latitude: float, longitude: float) -> Toilet | None:
    nearest = None
    nearest_distance = float("inf")
    for toilet in db.query(Toilet).all():
        current = distance_meters(latitude, longitude, toilet.latitude, toilet.longitude)
        if current < nearest_distance:
            nearest = toilet
            nearest_distance = current
    return nearest


def load_sample_posts() -> int:
    db = SessionLocal()
    try:
        count = 0
        nick_adjectives = ["상쾌한", "푸른", "조용한", "빠른", "따뜻한", "밝은"]
        nick_nouns = ["여행자", "시민", "산책러", "탐험가", "방문객"]

        for place in SAMPLE_PLACES:
            # pick nearby toilet
            toilet = find_nearest_toilet(db, place["lat"], place["lon"])
            if not toilet:
                continue

            # create 1-3 posts for the place with varying ratings
            post_count = random.randint(1, 3)
            for i in range(post_count):
                title = f"{place['title']} - 후기 #{i+1}"
                rating = max(0.5, min(5.0, round(random.gauss(place['rating'], 1.0), 1)))
                nickname = f"{random.choice(nick_adjectives)} {random.choice(nick_nouns)} #{random.randint(1,99)}"
                # make post content slightly unique per post to avoid duplicate content
                post_content = f"{place['content']} (방문 후기 {i+1})"
                post = Post(
                    category=place["category"],
                    title=title,
                    content=post_content,
                    password="1234",
                    rating=rating,
                    nickname=nickname,
                    post_type="화장실 리뷰",
                    related_place=place["name"],
                    restroom_name=toilet.name,
                    toilet_id=toilet.toilet_id,
                    recommendation_count=random.randint(0, 20),
                    comment_count=0,
                )
                db.add(post)
                try:
                    db.flush()
                except Exception:
                    pass

                # NOTE: reviews are intentionally not auto-created here.
                # The user will add Review entries manually later if desired.
                # create 0-3 comments for this post
                comment_num = random.randint(0, 3)
                for j in range(comment_num):
                    c_nick = f"{random.choice(nick_adjectives)} {random.choice(nick_nouns)}"
                    c = Comment(
                        post_id=post.post_id if getattr(post, "post_id", None) else None,
                        nickname=c_nick,
                        password="1234",
                        content=f"{c_nick}의 코멘트 #{j+1}",
                        created_at=datetime.utcnow(),
                    )
                    db.add(c)
                    post.comment_count = (post.comment_count or 0) + 1

                count += 1

        db.commit()
        return count
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    csv_path = resolve_csv_path()
    print(f"Using toilet CSV: {csv_path}")
    reset_database()
    print("Database tables recreated.")
    toilet_count = load_toilet_data(csv_path)
    post_count = load_sample_posts()
    print(f"Loaded {toilet_count} toilets.")
    print(f"Loaded {post_count} sample posts.")
