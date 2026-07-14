"""
API 사용 예제 및 테스트 스크립트
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def print_section(title):
    """섹션 제목 출력"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

# ============ 1. 근처 화장실 조회 ============
def test_nearby_toilets():
    """근처 화장실 조회 테스트"""
    print_section("1. 근처 화장실 조회 (강남역 기준)")
    
    # 강남역 좌표
    params = {
        "latitude": 37.4979,
        "longitude": 127.0276,
        "distance": 1000,  # 1km
        "limit": 10
    }
    
    response = requests.get(f"{BASE_URL}/restrooms/nearby", params=params)
    
    if response.status_code == 200:
        toilets = response.json()
        print(f"✓ 찾은 화장실 개수: {len(toilets)}")
        
        if toilets:
            for idx, toilet in enumerate(toilets[:3], 1):
                print(f"\n  [{idx}] {toilet['name']}")
                print(f"      주소: {toilet['address']}")
                print(f"      거리: {toilet['distance']}m")
                print(f"      평점: {toilet['average_rating']}")
    else:
        print(f"✗ 오류: {response.status_code}")
        print(response.text)


# ============ 2. 게시글 작성 ============
def test_create_post():
    """게시글 작성 테스트"""
    print_section("2. 게시글 작성")
    
    post_data = {
        "category": "관광지",
        "title": "남산타워 인근 화장실 리뷰",
        "content": "남산타워 방문 후 1층 화장실 사용했습니다. 깨끗하고 넓었으며 화장지도 충분했습니다.",
        "password": "1234",
        "rating": 4.5,
        "image_url": None
    }
    
    response = requests.post(f"{BASE_URL}/posts", json=post_data)
    
    if response.status_code == 201:
        post = response.json()
        print(f"✓ 게시글 작성 성공")
        print(f"  ID: {post['post_id']}")
        print(f"  제목: {post['title']}")
        print(f"  평점: {post['rating']}")
        return post['post_id']
    else:
        print(f"✗ 오류: {response.status_code}")
        print(response.text)
        return None


# ============ 3. 카테고리별 게시글 조회 ============
def test_get_posts_by_category():
    """카테고리별 게시글 조회 테스트"""
    print_section("3. 카테고리별 게시글 조회")
    
    categories = ["관광지", "문화시설", "축제/공연", "쇼핑"]
    
    for category in categories:
        params = {
            "category": category,
            "skip": 0,
            "limit": 5,
            "sort_by": "recent"
        }
        
        response = requests.get(f"{BASE_URL}/posts", params=params)
        
        if response.status_code == 200:
            posts = response.json()
            print(f"\n  [{category}] - {len(posts)}개 게시글")
            
            for post in posts[:2]:
                print(f"    - {post['title']} (평점: {post['rating']})")
        else:
            print(f"  [{category}] ✗ 오류: {response.status_code}")


# ============ 4. 게시글 상세 조회 ============
def test_get_post_detail(post_id):
    """게시글 상세 조회 테스트"""
    print_section("4. 게시글 상세 조회")
    
    response = requests.get(f"{BASE_URL}/posts/{post_id}")
    
    if response.status_code == 200:
        post = response.json()
        print(f"✓ 게시글 상세 조회 성공")
        print(f"  제목: {post['title']}")
        print(f"  내용: {post['content'][:100]}...")
        print(f"  평점: {post['rating']}")
        print(f"  작성일: {post['created_at']}")
    else:
        print(f"✗ 오류: {response.status_code}")


# ============ 5. 게시글 수정 ============
def test_update_post(post_id):
    """게시글 수정 테스트"""
    print_section("5. 게시글 수정")
    
    update_data = {
        "title": "남산타워 인근 화장실 리뷰 (수정됨)",
        "content": "재방문했는데 여전히 깨끗합니다!",
        "password": "1234",
        "rating": 5.0
    }
    
    response = requests.put(f"{BASE_URL}/posts/{post_id}", json=update_data)
    
    if response.status_code == 200:
        post = response.json()
        print(f"✓ 게시글 수정 성공")
        print(f"  제목: {post['title']}")
        print(f"  평점: {post['rating']}")
        print(f"  수정일: {post['updated_at']}")
    else:
        print(f"✗ 오류: {response.status_code}")
        print(response.text)


# ============ 6. 위치 기반 조회 ============
def test_nearby_with_posts():
    """위치 기반 화장실과 최근 게시글 조회"""
    print_section("6. 위치 기반 화장실 + 최근 게시글 조회")
    
    params = {
        "latitude": 37.4979,
        "longitude": 127.0276,
        "distance": 5000,  # 5km
        "limit": 5
    }
    
    response = requests.get(f"{BASE_URL}/location/nearby", params=params)
    
    if response.status_code == 200:
        data = response.json()
        toilets = data['toilets']
        posts_by_toilet = data['posts_by_toilet']
        
        print(f"✓ 찾은 화장실: {len(toilets)}개")
        
        for toilet in toilets[:3]:
            print(f"\n  [{toilet['name']}]")
            print(f"    거리: {toilet['distance']}m")
            print(f"    평점: {toilet['average_rating']}")
            
            if str(toilet['toilet_id']) in posts_by_toilet:
                posts = posts_by_toilet[str(toilet['toilet_id'])]
                print(f"    최근 게시글 {len(posts)}개:")
                for post in posts[:2]:
                    print(f"      - {post['title']}")
    else:
        print(f"✗ 오류: {response.status_code}")


# ============ 7. 모든 카테고리 조회 ============
def test_get_all_categories():
    """모든 카테고리 조회"""
    print_section("7. 모든 카테고리 조회")
    
    response = requests.get(f"{BASE_URL}/posts/categories")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ 카테고리: {', '.join(data['categories'])}")
    else:
        print(f"✗ 오류: {response.status_code}")


# ============ 8. 화장실 상세 정보 ============
def test_get_toilet_detail():
    """화장실 상세 정보 조회"""
    print_section("8. 화장실 상세 정보 조회")
    
    # 첫 번째 화장실 정보 조회
    response = requests.get(f"{BASE_URL}/restrooms/1")
    
    if response.status_code == 200:
        toilet = response.json()
        print(f"✓ 화장실 상세 정보")
        print(f"  이름: {toilet['name']}")
        print(f"  주소: {toilet['address']}")
        print(f"  좌표: ({toilet['latitude']}, {toilet['longitude']})")
        print(f"  남성 변기: {toilet['male_toilet_count']}")
        print(f"  여성 변기: {toilet['female_toilet_count']}")
        print(f"  장애인시설: {'있음' if toilet['handicap_facility'] else '없음'}")
        print(f"  비상벨: {'있음' if toilet['emergency_bell'] else '없음'}")
        print(f"  기저귀교환대: {'있음' if toilet['diaper_changing_table'] else '없음'}")
    else:
        print(f"✗ 오류: {response.status_code}")


if __name__ == "__main__":
    print("\n")
    print("███████████████████████████████████████████████████████████")
    print("█                                                         █")
    print("█   화장실 커뮤니티 API 테스트                             █")
    print("█                                                         █")
    print("███████████████████████████████████████████████████████████")
    
    try:
        # 테스트 순서
        test_get_all_categories()
        test_get_toilet_detail()
        test_nearby_toilets()
        post_id = test_create_post()
        test_get_posts_by_category()
        
        if post_id:
            test_get_post_detail(post_id)
            test_update_post(post_id)
        
        test_nearby_with_posts()
        
        print_section("✓ 모든 테스트 완료!")
        
    except requests.exceptions.ConnectionError:
        print("\n✗ 서버에 연결할 수 없습니다.")
        print("  확인: 'uvicorn main:app --host 0.0.0.0 --port 8000' 명령으로 서버를 실행해주세요.")
    except Exception as e:
        print(f"\n✗ 오류 발생: {e}")
