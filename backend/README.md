# 화장실 커뮤니티 백엔드 API

> 공공데이터 기반 서울 지역 공중화장실 정보 및 커뮤니티 서비스

## 📋 개요

이 프로젝트는 다음 3가지 주요 기능을 제공합니다:

1. **근처 화장실 검색**: 사용자 위치 기반으로 근처 공중화장실을 거리순으로 검색
2. **카테고리별 커뮤니티**: 관광지, 문화시설, 축제/공연, 쇼핑 카테고리별 게시판
3. **위치 기반 정보**: 특정 화장실 주변의 최근 게시글 및 평가 정보 제공

---

## 🛠️ 기술 스택

- **Backend Framework**: FastAPI 0.104.1
- **Database**: SQLite
- **ORM**: SQLAlchemy 2.0.36
- **Data Validation**: Pydantic 2.5.0
- **Testing**: Pytest 8.0.0
- **Server**: Uvicorn 0.24.0

---

## 📁 프로젝트 구조

```
backend/
├── main.py                    # FastAPI 애플리케이션 진입점
├── app/
│   ├── config.py              # 애플리케이션 설정
│   ├── database.py            # DB 연결 설정
│   ├── models/                # SQLAlchemy ORM 모델
│   │   └── __init__.py        # Toilet, Post, Review 모델
│   ├── schemas/               # Pydantic 데이터 스키마
│   │   └── __init__.py        # Request/Response 스키마
│   ├── repositories/          # 데이터 접근 계층
│   │   └── __init__.py        # ToiletRepository, PostRepository 등
│   ├── services/              # 비즈니스 로직 계층
│   │   └── __init__.py        # LocationService, PostService 등
│   └── routes/                # API 라우트
│       ├── restrooms.py       # 화장실 API
│       ├── posts.py           # 게시글 API
│       └── location.py        # 위치 기반 API
├── tests/
│   └── test_api.py            # 자동화 테스트
├── load_data.py               # CSV 데이터 로드 스크립트
├── test_api_manual.py         # 수동 테스트 스크립트
├── requirements.txt           # Python 의존성
└── API_DESIGN.md              # API 설계 문서
```

---

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 필수 패키지 설치
pip install -r requirements.txt
```

### 2. 데이터 로드

서울시 공중화장실 CSV 파일(5,617개)과 샘플 게시글을 DB에 로드합니다:

```bash
python load_data.py
```

**출력 예시:**
```
Database tables created!
Loaded 5617 toilets...
Loaded 4 sample posts!
```

### 3. 서버 실행

```bash
# 개발 모드 (자동 리로드 포함)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 또는
python main.py
```

**서버 실행 확인:**
```
INFO:     Application startup complete
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 4. API 문서 확인

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 📚 API 엔드포인트

### 화장실 API

#### 근처 화장실 조회
```bash
GET /api/v1/restrooms/nearby?latitude=37.4979&longitude=127.0276&distance=1000
```

**응답 예시:**
```json
[
  {
    "toilet_id": 1,
    "name": "강남역 1번출구 화장실",
    "address": "서울시 강남구 강남역",
    "latitude": 37.4979,
    "longitude": 127.0276,
    "distance": 234.5,
    "average_rating": 4.5,
    "male_toilet_count": 2,
    "female_toilet_count": 2,
    "handicap_facility": true,
    "emergency_bell": true,
    "diaper_changing_table": false
  }
]
```

### 게시글 API

#### 카테고리별 게시글 조회
```bash
GET /api/v1/posts?category=관광지&sort_by=recent&limit=20
```

#### 게시글 작성
```bash
POST /api/v1/posts
Content-Type: application/json

{
  "category": "관광지",
  "title": "남산타워 화장실 리뷰",
  "content": "깨끗하고 넓어서 좋습니다.",
  "password": "1234",
  "rating": 4.5
}
```

#### 게시글 수정 (비밀번호 필수)
```bash
PUT /api/v1/posts/1
Content-Type: application/json

{
  "title": "수정된 제목",
  "content": "수정된 내용",
  "password": "1234",
  "rating": 5.0
}
```

#### 게시글 삭제 (비밀번호 필수)
```bash
DELETE /api/v1/posts/1
Content-Type: application/json

{
  "password": "1234"
}
```

### 위치 기반 API

#### 근처 화장실 + 최근 게시글
```bash
GET /api/v1/location/nearby?latitude=37.4979&longitude=127.0276&distance=5000
```

**응답 예시:**
```json
{
  "toilets": [
    {
      "toilet_id": 1,
      "name": "강남역 1번출구 화장실",
      "distance": 234.5,
      "average_rating": 4.5,
      ...
    }
  ],
  "posts_by_toilet": {
    "1": [
      {
        "post_id": 5,
        "category": "관광지",
        "title": "강남역 화장실 리뷰",
        "rating": 4.5,
        "created_at": "2026-07-14T12:00:00"
      }
    ]
  }
}
```

---

## 🧪 테스트

### 자동화 테스트 (Pytest)

```bash
# 모든 테스트 실행
pytest tests/test_api.py -v

# 특정 테스트만 실행
pytest tests/test_api.py::TestPosts::test_create_post -v
```

### 수동 테스트

서버가 실행 중인 상태에서:

```bash
python test_api_manual.py
```

**출력 예시:**
```
============================================================
  화장실 커뮤니티 API 테스트
============================================================

✓ 모든 테스트 완료!
```

---

## 🎯 주요 기능 상세

### 1. 거리 계산 (Haversine 공식)

두 좌표 사이의 실제 지표면 거리를 계산합니다:

```python
distance = calculate_distance(
    lat1=37.4979,   # 사용자 위도
    lon1=127.0276,  # 사용자 경도
    lat2=37.5,      # 화장실 위도
    lon2=127.03     # 화장실 경도
)
# 결과: 3541.23 (미터)
```

### 2. 비밀번호 기반 권한 관리

게시글 수정/삭제 시 비밀번호를 평문으로 저장하여 검증합니다:

```python
# 게시글 작성 시
password = "1234"  # 사용자가 지정

# 수정/삭제 시
if stored_password == provided_password:
    allow_operation()
else:
    raise UnauthorizedError()
```

### 3. 카테고리별 커뮤니티

4가지 카테고리로 분류된 게시판:

- **관광지**: 관광지 주변 화장실 정보
- **문화시설**: 박물관, 극장 등 문화시설 관련
- **축제/공연**: 이벤트, 공연장 근처 화장실
- **쇼핑**: 백화점, 쇼핑몰 화장실

### 4. 평점 기반 시각화

화장실 평가(0~5점)에 따라 다양한 색상으로 표시:

- 🔴 **0~2.5점**: 빨강 (낮음)
- 🟢 **2.5~4점**: 초록 (중간)
- 🔵 **4~5점**: 파랑 (높음)

---

## 💾 데이터베이스

### 포함된 데이터

1. **화장실 데이터 (5,617개)**
   - 출처: 서울시 공공데이터
   - 포함 정보: 위치, 시설, 연락처 등

2. **샘플 게시글 (4개)**
   - 각 카테고리별 1개씩
   - 테스트용 데이터

### 테이블 구조

```sql
-- 공중화장실 테이블
CREATE TABLE toilets (
    toilet_id INTEGER PRIMARY KEY,
    name VARCHAR(255),
    latitude FLOAT,
    longitude FLOAT,
    ...
);

-- 게시글 테이블
CREATE TABLE posts (
    post_id INTEGER PRIMARY KEY,
    category VARCHAR(50),
    title VARCHAR(255),
    password VARCHAR(255),
    rating FLOAT,
    ...
);

-- 리뷰 테이블
CREATE TABLE reviews (
    review_id INTEGER PRIMARY KEY,
    toilet_id INTEGER,
    rating FLOAT,
    ...
);
```

---

## 🔧 설정

### config.py

```python
DATABASE_URL = "sqlite:///./app.db"
API_V1_STR = "/api/v1"
DEBUG = True
```

---

## 📖 API 사용 예시

### cURL로 테스트

```bash
# 근처 화장실 조회
curl "http://localhost:8000/api/v1/restrooms/nearby?latitude=37.4979&longitude=127.0276&distance=1000"

# 게시글 작성
curl -X POST "http://localhost:8000/api/v1/posts" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "관광지",
    "title": "테스트",
    "content": "테스트 글입니다",
    "password": "1234",
    "rating": 4.5
  }'

# 게시글 조회
curl "http://localhost:8000/api/v1/posts?category=관광지"
```

### Python으로 테스트

```python
import requests

# 근처 화장실 조회
response = requests.get(
    "http://localhost:8000/api/v1/restrooms/nearby",
    params={
        "latitude": 37.4979,
        "longitude": 127.0276,
        "distance": 1000
    }
)
toilets = response.json()

# 게시글 작성
response = requests.post(
    "http://localhost:8000/api/v1/posts",
    json={
        "category": "관광지",
        "title": "테스트",
        "content": "테스트",
        "password": "1234",
        "rating": 4.5
    }
)
post = response.json()
```

---

## 🚨 에러 처리

### 일반적인 에러 응답

```json
{
  "detail": "Invalid password or post not found"
}
```

### HTTP 상태 코드

- `200 OK`: 성공
- `201 Created`: 리소스 생성 성공
- `204 No Content`: 삭제 성공
- `400 Bad Request`: 요청 데이터 오류
- `401 Unauthorized`: 인증 실패 (잘못된 비밀번호)
- `404 Not Found`: 리소스 없음
- `500 Internal Server Error`: 서버 오류

---

## 📊 성능 최적화

1. **인덱싱**: SQLite 인덱싱으로 조회 성능 향상
2. **페이지네이션**: skip/limit으로 메모리 효율화
3. **거리 기반 필터링**: 불필요한 데이터 로드 최소화

---

## 🔐 보안 참고사항

**프로덕션 환경에서는 다음을 구현해야 합니다:**

1. ✅ 비밀번호 해싱 (bcrypt, argon2)
2. ✅ JWT 토큰 기반 인증
3. ✅ HTTPS 사용
4. ✅ Rate Limiting
5. ✅ 입력 데이터 검증 강화
6. ✅ SQL Injection 방지 (현재 ORM 사용 중)

---

## 📝 라이선스

MIT License

---

## 👨‍💻 개발자 정보

**프로젝트 타입**: 교육용 프로젝트  
**개발 환경**: Windows, Python 3.11  
**마지막 수정**: 2026-07-14

---

## 🤝 기여

버그 리포트 및 개선 제안은 이슈로 등록해주세요.

---

## 📞 연락처

프로젝트에 대한 질문이 있으시면 이슈를 생성해주세요.

---

## 🎓 학습 리소스

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [SQLAlchemy 문서](https://docs.sqlalchemy.org/)
- [Pydantic 문서](https://docs.pydantic.dev/)

---

**Happy coding! 🚀**
