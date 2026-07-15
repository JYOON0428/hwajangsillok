# 화장실록

서울 공공데이터 기반 화장실 검색 및 익명 커뮤니티 서비스입니다.

사용자는 카카오맵에서 주변 화장실을 확인하고, 화장실 이용 후기를 익명으로 작성할 수 있습니다. 홈 화면의 주변 화장실 기준 위치는 현재 GPS 대신 `역삼역 멀티캠퍼스`로 고정되어 있습니다.

## 기술 스택

- Frontend: Vue 3, Vite, Vue Router
- Backend: FastAPI, SQLAlchemy
- Database: SQLite
- Map/Geocoding: Kakao Maps JavaScript API, Kakao Local REST API
- Data: 서울특별시 공중화장실 공공데이터 CSV

## 프로젝트 구조

```text
2/
├─ backend/
│  ├─ app/
│  │  ├─ models/
│  │  ├─ routes/
│  │  └─ database.py
│  ├─ data/
│  │  ├─ toilet/공중화장실정보_서울특별시.csv
│  │  └─ seoul/*.json
│  ├─ load_data.py
│  ├─ main.py
│  ├─ requirements.txt
│  └─ .env.example
├─ frontend/
│  ├─ src/
│  ├─ package.json
│  └─ .env.example
└─ README.md
```

## 사전 준비

로컬 PC에 아래 프로그램이 설치되어 있어야 합니다.

- Python 3.11 이상
- Node.js 20 이상 권장
- Git
- VSCode

## 1. 프로젝트 클론

```powershell
git clone https://lab.ssafy.com/s16/a20/260714-startcamp-pjt/2.git
cd 2
```

## 2. .env 파일 생성

- 2/frontend, 2/backend 디렉토리에 각각 .env 파일을 만들고, 제공받은 내용을 붙여넣습니다.

### backend
```env
KAKAO_REST_API_KEY=여기에_카카오_REST_API_키
KAKAO_GEOCODE_DELAY=0.03
```

### Frontend
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_USE_MOCK_API=false
VITE_KAKAO_MAP_APP_KEY=여기에_카카오_JavaScript_키
```

## 4. 백엔드 설치 및 DB 생성

VSCode 터미널에서 실행합니다.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python load_data.py
```

`python load_data.py`는 다음 작업을 합니다.

- `backend/app.db` SQLite 파일 생성
- 서울 공중화장실 CSV 데이터 적재
- 카카오 Local API로 주소를 위도/경도로 변환
- 샘플 게시글과 리뷰 생성

처음 실행할 때는 데이터가 많아서 몇 분 걸릴 수 있습니다.

아래 출력과 비슷하게 나오면 성공입니다.

```text
Database tables recreated.
Loaded 500 toilets...
...
Geocoded by Kakao: 5424, fallback: 193
Loaded 5617 toilets.
Loaded 6 sample posts and reviews.
```

`app.db`, `data/geocode_cache.json`은 로컬 생성 파일이라 Git에 올리지 않습니다.

## 5. 백엔드 실행

백엔드 터미널에서 실행합니다.

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

정상 확인:

- API 상태: http://127.0.0.1:8000/health
- Swagger 문서: http://127.0.0.1:8000/docs

## 6. 프론트엔드 설치 및 실행

새 VSCode 터미널을 열고 실행합니다.

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

브라우저에서 아래 주소를 엽니다.

```text
http://localhost:5173
```

카카오 Web 플랫폼 도메인을 `http://localhost:5173`으로 등록했으므로, 브라우저도 가능하면 `localhost` 주소로 접속하세요. `127.0.0.1`은 카카오에서 다른 도메인으로 취급할 수 있습니다.

## 빠른 실행 요약

터미널 1, 백엔드:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

터미널 2, 프론트엔드:

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

접속:

```text
http://localhost:5173
```

## 주요 기능

- 서울 공중화장실 공공데이터 검색
- 카카오맵 기반 화장실 위치 표시
- 역삼역 멀티캠퍼스 기준 주변 화장실 표시
- 화장실 상세 정보, 편의시설, 운영 상태 표시
- 화장실 후기 작성
- 자유게시판 글 작성
- 익명 사용자 자동 표시
- 게시글 비밀번호 기반 수정/삭제
- 24시간 이내 상대 시간 표시, 이후 날짜 표시

## 테스트

백엔드 자동 테스트:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pytest tests
```

프론트엔드 빌드:

```powershell
cd frontend
npm run build
```

참고로 `backend/test_api_manual.py`는 별도 수동 API 테스트 파일입니다. `requests` 패키지가 없으면 전체 `pytest` 수집 단계에서 실패할 수 있으므로, 자동 테스트는 `python -m pytest tests`로 실행하세요.

## 자주 발생하는 문제

### 프론트에서 API 데이터를 못 가져오는 경우

`frontend/.env`를 확인합니다.

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_USE_MOCK_API=false
```

수정 후에는 프론트 dev 서버를 재시작해야 합니다.

### 지도가 안 뜨는 경우

아래를 확인합니다.

- `frontend/.env`의 `VITE_KAKAO_MAP_APP_KEY`
- Kakao Developers의 Web 플랫폼 도메인: `http://localhost:5173`
- 카카오맵/로컬 사용 설정
- 브라우저 접속 주소가 `http://localhost:5173`인지 여부

### 지오코딩이 전부 fallback으로 나오는 경우

아래를 확인합니다.

- `backend/.env`의 `KAKAO_REST_API_KEY`
- 카카오맵/로컬 사용 설정
- REST API 키가 JavaScript 키와 바뀌지 않았는지 여부

설정을 고친 뒤에는 실패 캐시를 삭제하고 다시 로드합니다.

```powershell
cd backend
Remove-Item .\data\geocode_cache.json -ErrorAction SilentlyContinue
python load_data.py
```

### 포트가 이미 사용 중인 경우

다른 터미널에서 기존 서버가 켜져 있을 수 있습니다.

- 백엔드 기본 포트: `8000`
- 프론트 기본 포트: `5173`

기존 프로세스를 종료하거나 다른 포트로 실행하세요.

## Git에 올리지 말아야 할 파일

아래 파일은 개인 로컬 파일이므로 커밋하지 않습니다.

- `backend/.env`
- `frontend/.env`
- `backend/app.db`
- `backend/data/geocode_cache.json`
- `backend/uploads/`
- `frontend/node_modules/`
- 로그 파일

이미 `.gitignore`에 포함되어 있습니다.
