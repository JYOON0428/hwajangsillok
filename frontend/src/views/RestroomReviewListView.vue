<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import RestroomReviewCard from '../components/RestroomReviewCard.vue'
import RestroomMapPanel from '../components/RestroomMapPanel.vue'
import { getRestroom, getRestroomReviews } from '../services/locationApi'

const props = defineProps({
  id: {
    type: String,
    required: true,
  },
})

const router = useRouter()

const restroom = ref(null)
const reviews = ref([])
const reviewSort = ref('recent')
const reviewKeyword = ref('')
const loading = ref(true)
const reviewsLoading = ref(false)
const error = ref('')
const notice = ref('')
let noticeTimer = null

const filteredReviews = computed(() => {
  const keyword = reviewKeyword.value.trim().toLowerCase()
  if (!keyword) return reviews.value

  return reviews.value.filter((review) =>
    [review.title, review.content, review.nickname]
      .filter(Boolean)
      .join(' ')
      .toLowerCase()
      .includes(keyword),
  )
})

const reviewCount = computed(() =>
  Math.max(Number(restroom.value?.reviewCount || 0), reviews.value.length),
)

const shouldShowSearch = computed(() => reviews.value.length > 5)
const shouldShowSort = computed(() => reviews.value.length > 1)
const shouldShowContributeCard = computed(
  () => reviews.value.length > 0 && reviews.value.length < 5,
)

const selectedRestroomId = computed(() => {
  const id = Number(restroom.value?.id ?? props.id)
  return Number.isFinite(id) ? id : null
})

const mapRestrooms = computed(() => {
  if (!restroom.value) return []

  return [
    {
      ...restroom.value,
      id: selectedRestroomId.value,
      mapPosition: restroom.value.mapPosition || { x: 50, y: 50 },
    },
  ]
})

const facilityItems = computed(() => {
  const source = restroom.value?.facilities || {}

  return [
    { key: 'diaperTable', label: '기저귀 교환대', enabled: Boolean(source.diaperTable) },
    { key: 'accessible', label: '장애인용 시설', enabled: Boolean(source.accessible) },
    { key: 'emergencyBell', label: '비상벨', enabled: Boolean(source.emergencyBell) },
    { key: 'entranceCctv', label: '입구 CCTV', enabled: Boolean(source.entranceCctv) },
    { key: 'open24Hours', label: '24시간 개방', enabled: Boolean(source.open24Hours) },
  ].filter((item) => item.enabled)
})

function ratingClass(rating) {
  if (rating == null) return 'rating-none'
  if (rating >= 4) return 'rating-high'
  if (rating >= 3) return 'rating-mid'
  return 'rating-low'
}

function operationStatus(item) {
  if (item?.openNow === true) {
    return { label: '현재 개방', className: 'status-open' }
  }
  if (item?.openNow === false) {
    return { label: '현재 운영 종료', className: 'status-closed' }
  }
  return { label: '운영 여부 확인 필요', className: 'status-unknown' }
}

function normalizeRestroom(response) {
  return response?.data || response?.item || response || null
}

function normalizeReview(review) {
  const imageUrls = review.imageUrls
    ?? review.image_urls
    ?? (review.imageUrl ? [review.imageUrl] : [])

  return {
    ...review,
    postId: review.postId
      ?? review.post_id
      ?? review.communityPostId
      ?? review.community_post_id
      ?? null,
    cleanliness: review.cleanliness ?? review.rating ?? null,
    imageUrls: Array.isArray(imageUrls) ? imageUrls.filter(Boolean) : [],
    createdAtLabel: review.createdAtLabel
      ?? review.created_at_label
      ?? review.createdAt
      ?? review.created_at
      ?? '',
  }
}

async function loadRestroom() {
  const response = await getRestroom(props.id)
  restroom.value = normalizeRestroom(response)
}

async function loadReviews() {
  reviewsLoading.value = true

  try {
    const response = await getRestroomReviews(props.id, { sort: reviewSort.value })
    const items = Array.isArray(response)
      ? response
      : response?.items || response?.reviews || response?.data || []

    reviews.value = Array.isArray(items) ? items.map(normalizeReview) : []
  } catch (err) {
    reviews.value = []
    showNotice(err.message || '리뷰를 불러오지 못했습니다.')
  } finally {
    reviewsLoading.value = false
  }
}

async function loadPage() {
  loading.value = true
  error.value = ''

  try {
    await Promise.all([loadRestroom(), loadReviews()])
  } catch (err) {
    error.value = err.message || '화장실 리뷰 정보를 불러오지 못했습니다.'
  } finally {
    loading.value = false
  }
}

function writeReview() {
  if (!restroom.value) return

  router.push({
    name: 'post-create',
    query: {
      type: '화장실 리뷰',
      restroomId: restroom.value.id || props.id,
      restroomName: restroom.value.name,
    },
  })
}

function openMapSearch() {
  if (!restroom.value) return

  router.push({
    name: 'search',
    query: {
      q: restroom.value.name,
      radius: 1000,
      restroomId: restroom.value.id || props.id,
    },
  })
}

function openReviewPost(review) {
  const postId = Number(
    review?.postId
      ?? review?.post_id
      ?? review?.communityPostId
      ?? review?.community_post_id,
  )

  if (!Number.isFinite(postId) || postId <= 0) {
    showNotice('연결된 원문 게시글 정보를 찾을 수 없습니다.')
    return
  }

  router.push({
    name: 'post-detail',
    params: { id: String(postId) },
  })
}

function showNotice(message, duration = 2400) {
  notice.value = message
  window.clearTimeout(noticeTimer)
  noticeTimer = window.setTimeout(() => {
    notice.value = ''
  }, duration)
}

async function copyText(text) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text)
    return
  }

  const textarea = document.createElement('textarea')
  textarea.value = text
  textarea.setAttribute('readonly', '')
  textarea.style.position = 'fixed'
  textarea.style.opacity = '0'
  document.body.appendChild(textarea)
  textarea.select()
  document.execCommand('copy')
  textarea.remove()
}

async function shareRestroom() {
  if (!restroom.value) return

  const resolved = router.resolve({
    name: 'restroom-reviews',
    params: { id: restroom.value.id || props.id },
  })
  const url = new URL(resolved.href, window.location.origin).href
  const shareData = {
    title: `${restroom.value.name} 이용자 리뷰 | 화장실록`,
    text: `${restroom.value.name}\n${restroom.value.address || ''}`.trim(),
    url,
  }

  if (navigator.share) {
    try {
      await navigator.share(shareData)
      showNotice('화장실 리뷰 페이지를 공유했습니다.')
      return
    } catch (err) {
      if (err?.name === 'AbortError') return
    }
  }

  try {
    await copyText(`${shareData.text}\n${url}`)
    showNotice('화장실 리뷰 페이지 링크를 복사했습니다.')
  } catch {
    showNotice('링크를 복사하지 못했습니다.')
  }
}

watch(reviewSort, loadReviews)
watch(() => props.id, loadPage)
onMounted(loadPage)
</script>

<template>
  <main class="restroom-review-page restroom-review-page--home-theme">
    <div class="page-container restroom-review-page__shell">
      <button
        class="community-detail-back restroom-review-page__back"
        type="button"
        aria-label="뒤로 가기"
        @click="router.back()"
      >
        <span class="community-detail-back__icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none">
            <path
              d="m14.5 5-7 7 7 7"
              stroke="currentColor"
              stroke-width="1.9"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </span>
        <span>뒤로</span>
      </button>

      <p v-if="loading" class="state-message">화장실 리뷰를 불러오는 중입니다.</p>

      <section v-else-if="error" class="restroom-review-page__error">
        <strong>페이지를 불러오지 못했습니다.</strong>
        <p>{{ error }}</p>
        <button type="button" @click="loadPage">다시 시도</button>
      </section>

      <template v-else-if="restroom">
        <header class="restroom-review-hero restroom-review-hero--compact">
          <div class="restroom-review-hero__main">
            <span class="restroom-review-hero__eyebrow">화장실 리뷰 모아보기</span>
            <h1>{{ restroom.name }}</h1>

            <div class="restroom-review-hero__metrics">
              <strong :class="ratingClass(restroom.rating)">
                {{ restroom.rating == null ? '평점 없음' : `★ ${restroom.rating}` }}
              </strong>
              <span>리뷰 {{ reviewCount }}개</span>
              <span
                class="operation-status-badge"
                :class="operationStatus(restroom).className"
              >
                <i aria-hidden="true"></i>
                {{ operationStatus(restroom).label }}
              </span>
            </div>

            <div class="restroom-review-hero__location-meta">
              <span v-if="restroom.address">{{ restroom.address }}</span>
              <span v-if="restroom.openingHours">운영시간 {{ restroom.openingHours }}</span>
            </div>
          </div>

          <div class="restroom-review-hero__actions">
            <button class="restroom-review-primary-action" type="button" @click="writeReview">
              <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path d="M4 20h4l10.7-10.7a2.1 2.1 0 0 0-3-3L5 17v3Z" stroke="currentColor" stroke-width="1.9" stroke-linejoin="round" />
                <path d="m14.5 7.5 3 3" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" />
              </svg>
              <span>리뷰 작성</span>
            </button>

            <button
              class="restroom-review-share-action"
              type="button"
              aria-label="리뷰 페이지 공유"
              title="공유"
              @click="shareRestroom"
            >
              <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <circle cx="18" cy="5" r="2.2" stroke="currentColor" stroke-width="1.8" />
                <circle cx="6" cy="12" r="2.2" stroke="currentColor" stroke-width="1.8" />
                <circle cx="18" cy="19" r="2.2" stroke="currentColor" stroke-width="1.8" />
                <path d="m8 11 8-5M8 13l8 5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
              </svg>
            </button>
          </div>
        </header>

        <div class="restroom-review-layout restroom-review-layout--refined">
          <aside class="restroom-review-place-panel">
            <section class="restroom-review-place-card">
              <header class="restroom-review-place-card__header">
                <div>
                  <span>장소 정보</span>
                  <h2>시설과 위치</h2>
                </div>
                <small v-if="restroom.dataReferenceDate">
                  기준일 {{ restroom.dataReferenceDate }}
                </small>
              </header>

              <div class="restroom-review-place-card__section">
                <h3>제공 시설</h3>
                <div v-if="facilityItems.length" class="restroom-review-facilities">
                  <span v-for="item in facilityItems" :key="item.key">
                    <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
                      <path d="m5 10 3 3 7-7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
                    </svg>
                    {{ item.label }}
                  </span>
                </div>
                <p v-else class="restroom-review-place-card__empty">
                  확인된 편의시설 정보가 없습니다.
                </p>
                <p class="restroom-review-place-card__notice">
                  공공데이터 기준 정보이며 실제 현장 상황과 다를 수 있습니다.
                </p>
              </div>

              <div class="restroom-review-place-card__section restroom-review-place-card__map-section">
                <div class="restroom-review-map-card__heading">
                  <div>
                    <span>위치</span>
                    <h3>{{ restroom.address || '주소 정보 없음' }}</h3>
                  </div>
                  <button type="button" @click="openMapSearch">
                    큰 지도 보기
                    <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
                      <path d="m8 5 5 5-5 5" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" />
                    </svg>
                  </button>
                </div>

                <div class="restroom-review-map-card__canvas">
                  <RestroomMapPanel
                    :restrooms="mapRestrooms"
                    :selected-id="selectedRestroomId"
                    :selected-only="true"
                    :show-research-button="false"
                  />
                </div>
              </div>
            </section>
          </aside>

          <section class="restroom-review-feed restroom-review-feed--flat" aria-label="이용자 리뷰 목록">
            <header class="restroom-review-feed__header">
              <div class="restroom-review-feed__title-block">
                <span>이용자 리뷰</span>
                <h2>이 화장실을 이용한 후기</h2>
                <p>실제 이용 경험과 최신 상태를 확인하세요.</p>
              </div>

              <div
                v-if="shouldShowSearch || shouldShowSort"
                class="restroom-review-feed__controls"
              >
                <label v-if="shouldShowSearch" class="restroom-review-feed__search">
                  <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <circle cx="11" cy="11" r="6.5" stroke="currentColor" stroke-width="1.8" />
                    <path d="m16 16 4 4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
                  </svg>
                  <input
                    v-model="reviewKeyword"
                    type="search"
                    placeholder="후기 내용 검색"
                    aria-label="이 화장실 후기 검색"
                  />
                </label>

                <select v-if="shouldShowSort" v-model="reviewSort" aria-label="리뷰 정렬">
                  <option value="recent">최신순</option>
                  <option value="cleanlinessHigh">청결도 높은 순</option>
                  <option value="cleanlinessLow">청결도 낮은 순</option>
                </select>
              </div>
            </header>

            <div class="restroom-review-feed__summary-row">
              <strong>{{ filteredReviews.length }}개 후기</strong>
              <span v-if="reviewKeyword">검색 결과</span>
            </div>

            <p v-if="reviewsLoading" class="search-state">리뷰를 불러오는 중입니다.</p>

            <section v-else-if="!filteredReviews.length" class="restroom-review-empty">
              <strong>
                {{ reviewKeyword ? '검색 조건에 맞는 후기가 없습니다.' : '아직 등록된 후기가 없습니다.' }}
              </strong>
              <p>
                {{ reviewKeyword ? '다른 검색어로 확인해보세요.' : '첫 번째 이용 후기를 남겨보세요.' }}
              </p>
              <button v-if="!reviewKeyword" type="button" @click="writeReview">리뷰 작성</button>
            </section>

            <div v-else class="restroom-review-feed__list">
              <RestroomReviewCard
                v-for="review in filteredReviews"
                :key="review.id"
                :review="review"
                :show-distance="false"
                :show-chevron="true"
                variant="flat"
                @open-post="openReviewPost"
              />
            </div>

            <section v-if="shouldShowContributeCard" class="restroom-review-contribute">
              <div>
                <strong>최근 이용 경험이 있나요?</strong>
                <p>청결도와 편의시설 정보를 남기면 다음 이용자에게 도움이 됩니다.</p>
              </div>
              <button type="button" @click="writeReview">리뷰 작성</button>
            </section>
          </section>
        </div>
      </template>
    </div>

    <p v-if="notice" class="community-feed-toast" role="status">{{ notice }}</p>
  </main>
</template>
