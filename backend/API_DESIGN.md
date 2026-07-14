# 화장실 커뮤니티 백엔드 API 설계 문서

## 프로젝트 개요

**프로젝트명:** 화장실 커뮤니티 (화장실록)  
**기술 스택:** FastAPI, SQLAlchemy, SQLite, Python 3.11  
**목표:** 공중화장실 정보 제공 및 커뮤니티 기능 제공

---

## 데이터베이스 스키마

### 1. toilets 테이블 (공중화장실)

```sql
CREATE TABLE toilets (
    toilet_id INTEGER PRIMARY KEY,
    name VARCHAR(255),
    address VARCHAR(255),
    latitude FLOAT,
    longitude FLOAT,
    male_toilet_count INTEGER,
    female_toilet_count INTEGER,
    male_urinal_count INTEGER,
    female_urinal_count INTEGER,
    handicap_facility BOOLEAN,
    emergency_bell BOOLEAN,
    diaper_changing_table BOOLEAN,
    phone VARCHAR(20)
);
```

### 2. posts 테이블 (게시글 - 카테고리별 커뮤니티)

```sql
CREATE TABLE posts (
    post_id INTEGER PRIMARY KEY,
    category VARCHAR(50),           -- "관광지", "문화시설", "축제/공연", "쇼핑"
    title VARCHAR(255),
    content TEXT,
    password VARCHAR(255),          -- 평문 (실제 환경에선 해싱 필요)
    rating FLOAT,                   -- 0~5점
    image_url VARCHAR(500),
    toilet_id INTEGER,              -- FK: 연관 화장실
    created_at DATETIME,
    updated_at DATETIME
);
```

### 3. reviews 테이블 (화장실 평점)

```sql
CREATE TABLE reviews (
    review_id INTEGER PRIMARY KEY,
    toilet_id INTEGER,              -- FK: 화장실
    rating FLOAT,                   -- 0~5점
    content TEXT,
    created_at DATETIME
);
```

---

## API 엔드포인트

### 1. 화장실 API (`/api/v1/restrooms`)

#### 1-1. 근처 화장실 조회
```
GET /api/v1/restrooms/nearby

Parameters:
  - latitude (float, 필수): 사용자 위도
  - longitude (float, 필수): 사용자 경도
  - distance (int, 옵션): 검색 거리 (미터, 기본값: 1000)
  - limit (int, 옵션): 반환 개수 (기본값: 50)

Response:
[
  {
    "toilet_id": 1,
    "name": "강남역 1번출구 화장실",
    "address": "서울시 강남구 강남역",
    "latitude": 37.4979,
    "longitude": 127.0276,
    "distance": 234.5,           // 미터
    "average_rating": 4.5,
    "male_toilet_count": 2,
    "female_toilet_count": 2,
    "handicap_facility": true,
    ...
  }
]
```

#### 1-2. 화장실 상세 조회
```
GET /api/v1/restrooms/{toilet_id}

Response:
{
  "toilet_id": 1,
  "name": "강남역 1번출구 화장실",
  ...
}
```

#### 1-3. 화장실 생성 (관리자)
```
POST /api/v1/restrooms

Request Body:
{
  "name": "테스트 화장실",
  "address": "테스트 주소",
  "latitude": 37.5,
  "longitude": 127.0,
  "male_toilet_count": 1,
  "female_toilet_count": 1,
  "handicap_facility": false,
  "emergency_bell": true,
  "diaper_changing_table": false
}
```

---

### 2. 게시글 API (`/api/v1/posts`)

#### 2-1. 카테고리별 게시글 조회
```
GET /api/v1/posts

Parameters:
  - category (string, 필수): "관광지", "문화시설", "축제/공연", "쇼핑"
  - skip (int, 옵션): 페이지네이션 스킵 (기본값: 0)
  - limit (int, 옵션): 반환 개수 (기본값: 20)
  - sort_by (string, 옵션): "recent" 또는 "rating" (기본값: "recent")

Response:
[
  {
    "post_id": 1,
    "category": "관광지",
    "title": "남산타워 화장실 리뷰",
    "content": "깨끗하고 좋습니다...",
    "rating": 4.5,
    "image_url": null,
    "toilet_id": null,
    "created_at": "2026-07-14T12:00:00",
    "updated_at": "2026-07-14T12:00:00"
  }
]
```

#### 2-2. 게시글 상세 조회
```
GET /api/v1/posts/{post_id}

Response:
{
  "post_id": 1,
  "category": "관광지",
  "title": "남산타워 화장실 리뷰",
  "content": "깨끗하고 좋습니다...",
  "rating": 4.5,
  "image_url": null,
  "toilet_id": null,
  "created_at": "2026-07-14T12:00:00",
  "updated_at": "2026-07-14T12:00:00",
  "toilet": null  // 연관 화장실 정보
}
```

#### 2-3. 게시글 작성
```
POST /api/v1/posts

Request Body:
{
  "category": "관광지",
  "title": "남산타워 화장실 리뷰",
  "content": "깨끗하고 좋습니다.",
  "password": "1234",          // 수정/삭제 시 필요
  "rating": 4.5,               // 0~5
  "image_url": null,           // 선택
  "toilet_id": null            // 선택
}

Response (201 Created):
{
  "post_id": 1,
  "category": "관광지",
  ...
}
```

#### 2-4. 게시글 수정 (비밀번호 검증)
```
PUT /api/v1/posts/{post_id}

Request Body:
{
  "title": "수정된 제목",
  "content": "수정된 내용",
  "password": "1234",     // 필수 검증
  "rating": 5.0           // 선택
}

Response:
{
  "post_id": 1,
  ...
}

Error (401):
{
  "detail": "Invalid password or post not found"
}
```

#### 2-5. 게시글 삭제 (비밀번호 검증)
```
DELETE /api/v1/posts/{post_id}

Request Body:
{
  "password": "1234"      // 필수 검증
}

Response (204 No Content)
```

#### 2-6. 모든 카테고리 조회
```
GET /api/v1/posts/categories

Response:
{
  "categories": ["관광지", "문화시설", "축제/공연", "쇼핑"]
}
```

---

### 3. 위치 기반 API (`/api/v1/location`)

#### 3-1. 근처 화장실 + 최근 게시글
```
GET /api/v1/location/nearby

Parameters:
  - latitude (float, 필수): 사용자 위도
  - longitude (float, 필수): 사용자 경도
  - distance (int, 옵션): 검색 거리 (미터, 기본값: 1000)
  - limit (int, 옵션): 화장실 개수 (기본값: 20)

Response:
{
  "toilets": [
    {
      "toilet_id": 1,
      "name": "강남역 1번출구 화장실",
      "address": "서울시 강남구 강남역",
      "latitude": 37.4979,
      "longitude": 127.0276,
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

## 주요 기능

### 1. 거리 계산 (Haversine 공식)
- 위도, 경도 기반으로 실제 지표면 거리 계산
- 미터 단위로 반환
- LocationService에서 구현

### 2. 비밀번호 기반 권한 확인
- 게시글 수정/삭제 시 비밀번호 검증
- 평문 저장 (프로덕션 환경에선 bcrypt 등으로 해싱 필요)

### 3. 평점 기반 시각화 (프론트엔드)
- 0~2.5점: 빨강
- 2.5~4점: 초록
- 4~5점: 파랑

### 4. 페이지네이션
- skip/limit 방식
- limit 최대 100

### 5. 정렬 옵션
- 최신순 (created_at DESC)
- 평점순 (rating DESC)

---

## 프로젝트 구조

```
2_pjy/backend/
├── main.py                          # FastAPI 애플리케이션
├── app/
│   ├── __init__.py
│   ├── config.py                    # 설정
│   ├── database.py                  # DB 연결
│   ├── models/
│   │   └── __init__.py              # SQLAlchemy 모델 (Toilet, Post, Review)
│   ├── schemas/
│   │   └── __init__.py              # Pydantic 스키마
│   ├── repositories/
│   │   └── __init__.py              # 데이터 접근 계층
│   ├── services/
│   │   └── __init__.py              # 비즈니스 로직
│   └── routes/
│       ├── __init__.py
│       ├── restrooms.py             # 화장실 API
│       ├── posts.py                 # 게시글 API
│       └── location.py              # 위치 기반 API
├── tests/
│   ├── __init__.py
│   └── test_api.py                  # 자동화 테스트
├── load_data.py                     # 데이터 로드 스크립트
├── test_api_manual.py               # 수동 테스트 스크립트
├── requirements.txt                 # 의존성
├── app.db                           # SQLite DB 파일
└── README.md                        # 문서
```

---

## 기술 사항

### 거리 계산
Haversine 공식을 사용하여 두 지점 간의 대원 거리를 계산합니다.

```python
def calculate_distance(lat1, lon1, lat2, lon2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371000  # 지구 반지름 (미터)
    return c * r
```

### 데이터 검증
- Pydantic을 사용한 입력 검증
- 평점은 0~5 범위 확인
- 카테고리는 허용된 값만 수용

---

## 사용 방법

### 1. 설치
```bash
pip install -r requirements.txt
```

### 2. 데이터 로드
```bash
python load_data.py
```

### 3. 서버 실행
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 4. API 문서 확인
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 5. 수동 테스트
```bash
python test_api_manual.py
```

---

## 설계 특징

1. **계층화 아키텍처**
   - Routes → Services → Repositories → Models
   - 각 계층의 책임이 명확

2. **비즈니스 로직 분리**
   - Services에 거리 계산, 비밀번호 검증 등 로직 포함
   - Controllers는 HTTP만 처리

3. **확장성**
   - 새로운 카테고리 추가 용이
   - Repository 패턴으로 DB 교체 가능

4. **에러 처리**
   - 명확한 HTTP 상태 코드
   - 상세한 에러 메시지

5. **데이터 검증**
   - Pydantic을 통한 자동 검증
   - 타입 안정성 보장

---

## 향후 개선 사항

1. **보안**
   - bcrypt를 사용한 비밀번호 해싱
   - JWT 토큰 기반 인증

2. **캐싱**
   - Redis를 통한 근처 화장실 캐싱
   - 평점 계산 캐싱

3. **검색 최적화**
   - 공간 인덱싱 (Spatial Index)
   - ElasticSearch 통합

4. **API 개선**
   - 필터링 기능 강화 (시설별 필터)
   - 검색 기능 추가

5. **모니터링**
   - 로깅 시스템
   - 성능 메트릭 수집
