import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import get_db
from app.models import Toilet, Post, Base
from main import app

# 테스트용 DB (메모리 DB)
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture
def setup_test_data():
    """테스트 데이터 설정"""
    db = TestingSessionLocal()
    
    # 테스트용 화장실 데이터 추가
    toilet = Toilet(
        name="강남역 1번출구 화장실",
        address="서울시 강남구 강남역",
        latitude=37.4979,
        longitude=127.0276,
        male_toilet_count=2,
        female_toilet_count=2,
        handicap_facility=True,
        emergency_bell=True,
        diaper_changing_table=False
    )
    db.add(toilet)
    db.commit()
    
    yield db
    
    db.close()


class TestRestrooms:
    """화장실 API 테스트"""
    
    def test_get_nearby_toilets(self, setup_test_data):
        """근처 화장실 조회 테스트"""
        response = client.get(
            "/api/v1/restrooms/nearby",
            params={
                "latitude": 37.5,
                "longitude": 127.0,
                "distance": 10000
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_create_toilet(self):
        """화장실 생성 테스트"""
        toilet_data = {
            "name": "테스트 화장실",
            "address": "테스트 주소",
            "latitude": 37.5,
            "longitude": 127.0,
            "male_toilet_count": 1,
            "female_toilet_count": 1
        }
        response = client.post("/api/v1/restrooms", json=toilet_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "테스트 화장실"


class TestPosts:
    """게시글 API 테스트"""
    
    def test_create_post(self):
        """게시글 생성 테스트"""
        post_data = {
            "category": "관광지",
            "title": "테스트 게시글",
            "content": "테스트 내용입니다.",
            "password": "1234",
            "rating": 4.5
        }
        response = client.post("/api/v1/posts", json=post_data)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "테스트 게시글"
        assert data["category"] == "관광지"
    
    def test_get_posts_by_category(self):
        """카테고리별 게시글 조회 테스트"""
        # 먼저 게시글 생성
        post_data = {
            "category": "쇼핑",
            "title": "쇼핑 테스트",
            "content": "테스트",
            "password": "1234",
            "rating": 3.0
        }
        client.post("/api/v1/posts", json=post_data)
        
        # 조회
        response = client.get(
            "/api/v1/posts",
            params={"category": "쇼핑"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_categories(self):
        """카테고리 조회 테스트"""
        response = client.get("/api/v1/posts/categories")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
    
    def test_update_post_with_correct_password(self):
        """정확한 비밀번호로 게시글 수정 테스트"""
        # 게시글 생성
        post_data = {
            "category": "관광지",
            "title": "원본 제목",
            "content": "원본 내용",
            "password": "correct",
            "rating": 2.0
        }
        create_response = client.post("/api/v1/posts", json=post_data)
        post_id = create_response.json()["post_id"]
        
        # 수정
        update_data = {
            "title": "수정된 제목",
            "content": "수정된 내용",
            "password": "correct",
            "rating": 4.0
        }
        response = client.put(f"/api/v1/posts/{post_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "수정된 제목"
        assert data["rating"] == 4.0
    
    def test_update_post_with_wrong_password(self):
        """잘못된 비밀번호로 게시글 수정 테스트"""
        # 게시글 생성
        post_data = {
            "category": "관광지",
            "title": "테스트",
            "content": "테스트",
            "password": "correct",
            "rating": 2.0
        }
        create_response = client.post("/api/v1/posts", json=post_data)
        post_id = create_response.json()["post_id"]
        
        # 잘못된 비밀번호로 수정
        update_data = {
            "title": "변경",
            "password": "wrong",
            "content": "변경"
        }
        response = client.put(f"/api/v1/posts/{post_id}", json=update_data)
        assert response.status_code == 401
    
    def test_delete_post_with_correct_password(self):
        """정확한 비밀번호로 게시글 삭제 테스트"""
        # 게시글 생성
        post_data = {
            "category": "관광지",
            "title": "삭제할 게시글",
            "content": "테스트",
            "password": "delete123",
            "rating": 2.0
        }
        create_response = client.post("/api/v1/posts", json=post_data)
        post_id = create_response.json()["post_id"]
        
        # 삭제
        response = client.delete(
            f"/api/v1/posts/{post_id}",
            json={"password": "delete123"}
        )
        assert response.status_code == 204
    
    def test_invalid_rating(self):
        """유효하지 않은 평점 테스트"""
        post_data = {
            "category": "관광지",
            "title": "테스트",
            "content": "테스트",
            "password": "1234",
            "rating": 6.0  # 0~5 범위 벗어남
        }
        response = client.post("/api/v1/posts", json=post_data)
        assert response.status_code == 400


class TestLocation:
    """위치 기반 API 테스트"""
    
    def test_nearby_with_posts(self, setup_test_data):
        """근처 화장실과 게시글 조회 테스트"""
        response = client.get(
            "/api/v1/location/nearby",
            params={
                "latitude": 37.5,
                "longitude": 127.0,
                "distance": 10000
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "toilets" in data
        assert "posts_by_toilet" in data
        assert isinstance(data["toilets"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
