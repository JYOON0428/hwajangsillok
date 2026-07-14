import csv
import json
import os
import math
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import Toilet, Post, Review


def calculate_distance(lat1, lon1, lat2, lon2):
    """하버사인 공식으로 거리 계산 (미터)"""
    R = 6371000  # 지구 반지름 (미터)
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


def find_nearest_toilet(db: Session, latitude: float, longitude: float, max_distance: float = 2000):
    """좌표 기반으로 가장 가까운 화장실 찾기"""
    toilets = db.query(Toilet).all()
    
    nearest = None
    nearest_distance = max_distance
    
    for toilet in toilets:
        if toilet.latitude == 0 or toilet.longitude == 0:
            continue
        
        distance = calculate_distance(latitude, longitude, toilet.latitude, toilet.longitude)
        
        if distance < nearest_distance:
            nearest = toilet
            nearest_distance = distance
    
    return nearest


def load_toilet_data(csv_file_path: str):
    """
    공중화장실 CSV 데이터 로드
    """
    db = SessionLocal()
    
    try:
        with open(csv_file_path, 'r', encoding='cp949') as f:
            reader = csv.DictReader(f)
            count = 0
            
            for row in reader:
                try:
                    # CSV 컬럼 매핑
                    toilet = Toilet(
                        name=row.get('화장실명', '').strip(),
                        address=row.get('도로명주소', '').strip() or row.get('지번주소', '').strip(),
                        latitude=float(row.get('위도', 0) or 0),
                        longitude=float(row.get('경도', 0) or 0),
                        male_toilet_count=int(row.get('남성-대변기', 0) or 0),
                        female_toilet_count=int(row.get('여성-대변기', 0) or 0),
                        male_urinal_count=int(row.get('남성-소변기', 0) or 0),
                        female_urinal_count=int(row.get('여성-소변기', 0) or 0),
                        handicap_facility=row.get('장애인화장실-대변기', 0) != '0' and row.get('장애인화장실-대변기', '').strip() != '',
                        emergency_bell=row.get('비상벨설치유무', 'N') == 'Y',
                        diaper_changing_table=row.get('기저귀교환대설치유무', 'N') == 'Y',
                        phone=row.get('전화번호', '').strip() or None
                    )
                    
                    db.add(toilet)
                    count += 1
                    
                    if count % 100 == 0:
                        db.commit()
                        print(f"Loaded {count} toilets...")
                
                except Exception as e:
                    print(f"Error loading row: {e}")
                    continue
            
            db.commit()
            print(f"Total {count} toilets loaded successfully!")
    
    except Exception as e:
        print(f"Error loading toilet data: {e}")
        db.rollback()
    
    finally:
        db.close()


def load_test_toilets_and_posts():
    """
    테스트용 화장실 데이터 및 관광지 게시글 로드
    주요 관광지 주변에 화장실 데이터 생성
    """
    db = SessionLocal()
    
    try:
        # 서울 주요 관광지 좌표 및 테스트 화장실 데이터
        test_locations = [
            {
                "location": "서울 타워",
                "base_lat": 37.5512,
                "base_lon": 126.9882,
                "toilets": [
                    {"name": "남산타워 공중화장실", "offset_lat": 0.0001, "offset_lon": 0.0001},
                    {"name": "남산공원 입구 화장실", "offset_lat": -0.0002, "offset_lon": 0.0002},
                    {"name": "남산 정상 공중화장실", "offset_lat": 0.0002, "offset_lon": -0.0001},
                ]
            },
            {
                "location": "강남역",
                "base_lat": 37.4979,
                "base_lon": 127.0276,
                "toilets": [
                    {"name": "강남역 지하상가 화장실", "offset_lat": 0.0001, "offset_lon": 0.0001},
                    {"name": "강남역 광장 공중화장실", "offset_lat": -0.0001, "offset_lon": -0.0001},
                    {"name": "강남 COEX 화장실", "offset_lat": 0.0002, "offset_lon": 0.0002},
                ]
            },
            {
                "location": "국립박물관",
                "base_lat": 37.5266,
                "base_lon": 126.9805,
                "toilets": [
                    {"name": "국립박물관 주출입구 화장실", "offset_lat": 0.0001, "offset_lon": 0.0001},
                    {"name": "국립박물관 야외광장 화장실", "offset_lat": -0.0001, "offset_lon": 0.0001},
                ]
            },
            {
                "location": "경복궁",
                "base_lat": 37.5795,
                "base_lon": 126.9770,
                "toilets": [
                    {"name": "경복궁 정문 공중화장실", "offset_lat": 0.0001, "offset_lon": 0.0001},
                    {"name": "경복궁 내부 화장실", "offset_lat": 0.0002, "offset_lon": 0.0002},
                ]
            },
            {
                "location": "명동",
                "base_lat": 37.5629,
                "base_lon": 126.9846,
                "toilets": [
                    {"name": "명동거리 공중화장실", "offset_lat": 0.0001, "offset_lon": 0.0001},
                    {"name": "명동 쇼핑몰 화장실", "offset_lat": -0.0001, "offset_lon": 0.0001},
                ]
            },
        ]
        
        posts_to_add = []
        
        for loc_data in test_locations:
            location_name = loc_data["location"]
            base_lat = loc_data["base_lat"]
            base_lon = loc_data["base_lon"]
            
            # 각 관광지별 화장실 생성 및 게시글 연결
            for toilet_data in loc_data["toilets"]:
                toilet = Toilet(
                    name=toilet_data["name"],
                    address=f"서울 {location_name} 근처",
                    latitude=base_lat + toilet_data["offset_lat"],
                    longitude=base_lon + toilet_data["offset_lon"],
                    male_toilet_count=2,
                    female_toilet_count=2,
                    male_urinal_count=1,
                    female_urinal_count=0,
                    handicap_facility=True,
                    emergency_bell=True,
                    diaper_changing_table=True,
                    phone="02-1234-5678"
                )
                db.add(toilet)
                db.flush()  # ID 생성
                
                # 해당 화장실에 대한 게시글 생성
                post = Post(
                    category="관광지",
                    title=f"{location_name} 근처 화장실 후기",
                    content=f"{location_name}에서 {toilet_data['name']}을 사용했습니다. 깨끗하고 시설이 잘 되어있습니다.",
                    password="1111",
                    rating=4.5,
                    image_url=None,
                    toilet_id=toilet.toilet_id
                )
                posts_to_add.append(post)
        
        # 모든 게시글 저장
        for post in posts_to_add:
            db.add(post)
        
        db.commit()
        print(f"Loaded {len(posts_to_add)} test posts linked to test toilets!")
    
    except Exception as e:
        print(f"Error loading test data: {e}")
        db.rollback()
    
    finally:
        db.close()


def load_sample_posts():
    """
    샘플 게시글 로드
    """
    db = SessionLocal()
    
    try:
        sample_posts = [
            Post(
                category="관광지",
                title="서울 타워 근처 화장실",
                content="서울 타워 관광 후 사용했는데 깨끗하고 넓었습니다.",
                password="1234",
                rating=4.5,
                image_url=None
            ),
            Post(
                category="문화시설",
                title="국립박물관 화장실 리뷰",
                content="박물관 2층 화장실이 제일 깨끗했어요.",
                password="5678",
                rating=5.0,
                image_url=None
            ),
            Post(
                category="쇼핑",
                title="강남역 쇼핑몰 화장실",
                content="항상 깨끗하게 유지되고 있습니다.",
                password="abcd",
                rating=4.0,
                image_url=None
            ),
            Post(
                category="축제/공연",
                title="서울 뮤직 페스티벌 화장실",
                content="페스티벌 기간에 임시 화장실이 설치되었는데 관리가 잘되었습니다.",
                password="xyz",
                rating=3.5,
                image_url=None
            ),
            Post(
                category="일반",
                title="화장실 앱 사용 팁",
                content="이 앱으로 근처 화장실을 쉽게 찾을 수 있어서 좋습니다!",
                password="test",
                rating=5.0,
                image_url=None
            ),
        ]
        
        for post in sample_posts:
            db.add(post)
        
        db.commit()
        print(f"Loaded {len(sample_posts)} sample posts!")
    
    except Exception as e:
        print(f"Error loading sample posts: {e}")
        db.rollback()
    
    finally:
        db.close()


if __name__ == "__main__":
    # DB 테이블 생성
    from app.models import Base
    Base.metadata.create_all(bind=engine)
    print("Database tables created!")
    
    # 공중화장실 데이터 로드
    # CSV 파일 경로를 지정해야 함
    csv_path = "c:/Users/SSAFY/Downloads/공중화장실정보_서울특별시.csv"
    
    if os.path.exists(csv_path):
        load_toilet_data(csv_path)
    else:
        print(f"CSV file not found at {csv_path}")
        print("Please download the toilet data first")
    
    # 샘플 게시글 로드
    load_sample_posts()
    
    # 테스트용 화장실 및 관광지 게시글 로드
    print("\n=== Loading test data for tourist attractions ===")
    load_test_toilets_and_posts()
