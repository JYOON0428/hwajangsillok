# 화장실록 Vue 3 UI v0.4

Vue.js 3 + Vue Router 기반 프론트엔드 프로젝트입니다.

## 이번 버전 변경사항

- 헤더의 `홈` 텍스트 제거
- 임시 화장실 SVG 로고와 `화장실록`만 노출
- 홈 검색창과 검색 버튼 전면 리디자인
- 검색 버튼 높이 52px, 모바일 최소 터치 영역 50px 적용
- 검색과 AI 조건 검색의 시각적 역할 분리
- 홈 히어로, 카테고리 탭, 게시글 카드, 주변 화장실 영역 디자인 개선
- 게시글 이미지가 없으면 이미지 영역을 표시하지 않음
- 주변 화장실 카드에 작성자 정보 미표시
- 하늘색 중심의 저채도 색상과 일관된 간격·라운드·그림자 적용
- 정적 Python 서버용 `serve_vue.py` 포함

## 개발 서버 실행

```bash
npm install
npm run dev
```

PowerShell 정책 문제 시:

```powershell
npm.cmd install
npm.cmd run dev
```

## npm 설치 없이 빌드 결과 확인

프로젝트 루트에서:

```powershell
py serve_vue.py --port 4173 --directory dist
```

브라우저:

```text
http://127.0.0.1:4173/
```

## 환경변수

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_USE_MOCK_API=true
```

백엔드 연결 시 `VITE_USE_MOCK_API=false`로 변경합니다.

## 글쓰기 화면 추가 사항

- 검색 결과의 리뷰 작성 버튼은 `#/community/new?restroomId=101&restroomName=서울숲...` 형태로 이동합니다.
- 해당 경로로 들어오면 화장실이 미리 선택되며, 작성 화면에서 다른 화장실로 변경할 수 있습니다.
- 필수 입력값: 닉네임, 수정용 비밀번호, 카테고리, 관련 화장실, 청결도, 제목, 내용
- 사진은 선택이며 JPG/PNG/WEBP 1장, 5MB 이하로 제한합니다.
- 실 API에서 사진을 첨부하면 `multipart/form-data`로 `/api/posts` 또는 `/api/posts/{id}`에 전송합니다.
- 사진이 없으면 기존 JSON 요청을 유지합니다.

### 백엔드 요청 필드

`nickname`, `password`, `category`, `postType`, `title`, `content`, `rating`, `restroomId`, `restroomName`, `relatedPlace`, 선택 파일 `image`

## 홈 주변 화장실 영역
- 지도 미리보기 유지
- 우측에 가까운 화장실 3개 표시
- 반경별 전체 결과는 `지도에서 N곳 보기`로 검색 지도 화면에 연결

## 반경 변경 동작

200m·500m·1km 버튼을 바꿀 때 지도와 화장실 카드 영역을 DOM에서 제거하지 않습니다.
기존 결과를 유지한 상태에서 새 데이터가 준비되면 핀·카드·개수만 한 번에 교체하므로 화면이 깜빡이지 않습니다.
연속 클릭 시에는 마지막으로 선택한 반경의 요청만 반영합니다.


## 카테고리 커뮤니티 피드

- 홈의 전체/관광지/문화시설/축제·공연/쇼핑 카테고리를 누르면 `/community` 피드로 이동합니다.
- 목록 정렬: `recent`(최신순), `popular`(인기순), `rating`(평점순)
- 검색 대상: 제목, 본문, 관련 장소, 화장실명, 닉네임
- 게시글 공유: Web Share API 지원 환경에서는 시스템 공유창, 그 외에는 상세 링크 복사
- 사진이 없는 게시글은 이미지 영역을 만들지 않습니다.

실제 백엔드 목록 API 예시:

```text
GET /api/posts?category=관광지&keyword=서울숲&sort=recent&page=1&size=6
```

## Reddit-style community feed revision

- Category feed posts use a left vote rail and full-width content body.
- Attached images are shown in a large centered carousel with arrows, counter, dots, and keyboard navigation.
- Post writing supports up to 5 JPG/PNG/WEBP files, each up to 5 MB.
- Cleanliness scores are displayed as prominent rating badges.
- Post detail pages use the same feed visual language and include recommendation, downvote, comments count, and sharing controls.
- Mock recommendation state is stored in browser localStorage. A real backend should expose a vote endpoint and return the updated score.
- A real multipart backend should receive repeated `images` fields and an `imageUrls` JSON string for retained images during editing.
