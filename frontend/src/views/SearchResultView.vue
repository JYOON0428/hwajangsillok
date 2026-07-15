<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import RestroomDetailPanel from '../components/RestroomDetailPanel.vue'
import RestroomMapPanel from '../components/RestroomMapPanel.vue'
import RestroomResultList from '../components/RestroomResultList.vue'
import { getRestroomReviews, searchRestrooms } from '../services/locationApi'

const route = useRoute()
const router = useRouter()
const FIXED_NEARBY_LOCATION = {
  label: '역삼역 멀티캠퍼스',
  keyword: '역삼역 멀티캠퍼스',
  latitude: 37.5012743,
  longitude: 127.039585,
}

const keyword = ref(String(route.query.q || '화장실'))
const sort = ref('distance')
const radius = ref(Number(route.query.radius || 1000))
const filters = reactive({
  openNow: false,
  diaperTable: false,
  accessible: false,
  emergencyBell: false,
  recentReview: false,
})

const restrooms = ref([])
const selectedId = ref(null)
const reviews = ref([])
const reviewSort = ref('recent')
const loading = ref(false)
const reviewsLoading = ref(false)
const error = ref('')
const notice = ref('')
const mobileMode = ref('list')
const filterChipRow = ref(null)
let noticeTimer = null

const selectedRestroom = computed(
  () => restrooms.value.find((item) => item.id === selectedId.value) || null,
)

const activeFilterCount = computed(
  () => Object.values(filters).filter(Boolean).length,
)

const resultPlaceName = computed(() => normalizePlaceKeyword(route.query.q || keyword.value))
// 홈의 지도 마커나 주변 화장실 카드를 통해 진입해도
// 선택한 화장실만 고립시키지 않고 같은 반경의 전체 목록을 함께 표시한다.
const selectedOnlyMapMode = computed(() => false)
const mapRestrooms = computed(() => restrooms.value)
const searchAnchorLocation = computed(() => {
  const center = restrooms.value[0]?.searchCenter
  if (center?.latitude && center?.longitude) {
    return {
      label: selectedOnlyMapMode.value ? '나의 위치' : resultPlaceName.value || center.label || '검색 위치',
      latitude: Number(center.latitude),
      longitude: Number(center.longitude),
    }
  }

  const rawKeyword = String(route.query.q || keyword.value || '')
  if (rawKeyword.includes('역삼역') || rawKeyword.includes('멀티캠퍼스')) {
    return {
      ...FIXED_NEARBY_LOCATION,
      label: selectedOnlyMapMode.value ? '나의 위치' : FIXED_NEARBY_LOCATION.label,
    }
  }
  return null
})

function normalizePlaceKeyword(rawKeyword) {
  const original = String(rawKeyword || '').trim()
  if (!original) return '검색 위치'

  let value = original
    .replace(/[‘’'"“”]/g, '')
    .replace(/\s+/g, ' ')
    .trim()

  const removablePhrases = [
    '최근 리뷰 있는 곳',
    '최근 리뷰 있음',
    '리뷰 있는 곳',
    '기저귀 교환대',
    '장애인용 시설',
    '장애인용',
    '24시간 개방',
    '24시간',
    '비상벨',
    '현재 개방',
    '가까운 순',
    '청결도 높은 순',
    '리뷰 많은 순',
  ]

  removablePhrases.forEach((phrase) => {
    value = value.replaceAll(phrase, ' ')
  })

  value = value
    .replace(/\d+(?:\.\d+)?\s*(?:km|m|킬로미터|미터)\s*(?:이내|내)?/gi, ' ')
    .replace(/(?:에서\s*)?(?:가장\s*)?(?:가까운|근처|주변|인근|부근|근방)/g, ' ')
    .replace(/(?:공중|개방)?\s*화장실(?:을|를|이|가|은|는)?/g, ' ')
    .replace(/(?:찾아\s*줘|찾아주세요|검색해\s*줘|검색해 주세요|검색)/g, ' ')
    .replace(/[?!.]+$/g, '')
    .replace(/\s+/g, ' ')
    .trim()

  return value || original
}

function showNotice(message, duration = 2400) {
  notice.value = message
  window.clearTimeout(noticeTimer)
  noticeTimer = window.setTimeout(() => {
    notice.value = ''
  }, duration)
}

async function loadRestrooms({ preserveSelection = true } = {}) {
  loading.value = true
  error.value = ''

  try {
    const queryRestroomId = Number(route.query.restroomId || route.query.selected) || null
    const preferredId = preserveSelection ? selectedId.value : queryRestroomId
    const items = await searchRestrooms({
      keyword: keyword.value,
      radius: radius.value,
      sort: sort.value,
      ...filters,
    })

    restrooms.value = items
    selectedId.value = items.some((item) => item.id === preferredId)
      ? preferredId
      : items[0]?.id ?? null
  } catch (err) {
    error.value = err.message || '화장실 검색 중 오류가 발생했습니다.'
    restrooms.value = []
    selectedId.value = null
  } finally {
    loading.value = false
  }
}

async function loadReviews() {
  if (!selectedId.value) {
    reviews.value = []
    return
  }

  reviewsLoading.value = true
  try {
    reviews.value = await getRestroomReviews(selectedId.value, { sort: reviewSort.value })
  } catch (err) {
    reviews.value = []
    showNotice(err.message || '리뷰를 불러오지 못했습니다.')
  } finally {
    reviewsLoading.value = false
  }
}

function submitSearch() {
  router.replace({
    name: 'search',
    query: { q: keyword.value.trim() || '화장실', radius: radius.value },
  })
}

function selectRestroom(id) {
  const restroomId = Number(id)
  selectedId.value = restroomId

  router.replace({
    name: 'search',
    query: {
      ...route.query,
      q: keyword.value.trim() || '화장실',
      radius: radius.value,
      restroomId,
    },
  })
}

function toggleFilter(name) {
  filters[name] = !filters[name]
}

function clearFilters() {
  Object.keys(filters).forEach((key) => {
    filters[key] = false
  })
}

function scrollFilters(direction) {
  filterChipRow.value?.scrollBy({
    left: direction * 180,
    behavior: 'smooth',
  })
}

function searchCurrentMap() {
  showNotice('현재 지도 영역을 기준으로 결과를 다시 검색했습니다.')
  loadRestrooms()
}

function writeReview() {
  if (!selectedRestroom.value) return
  router.push({
    name: 'post-create',
    query: {
      type: '화장실 리뷰',
      restroomId: selectedRestroom.value.id,
      restroomName: selectedRestroom.value.name,
    },
  })
}

function openReviewPost(review) {
  const postId = Number(
    review?.postId
      ?? review?.post_id
      ?? review?.communityPostId
      ?? review?.community_post_id
      ?? review?.id,
  )

  if (!postId) {
    router.push({
      name: 'community',
      query: {
        keyword: review?.title || selectedRestroom.value?.name || '',
      },
    })
    return
  }

  router.push({
    name: 'post-detail',
    params: { id: postId },
  })
}

async function shareSelectedRestroom() {
  if (!selectedRestroom.value) return

  const restroom = selectedRestroom.value
  const resolved = router.resolve({
    name: 'search',
    query: {
      ...route.query,
      q: keyword.value.trim() || '화장실',
      radius: radius.value,
      restroomId: restroom.id,
    },
  })
  const shareUrl = new URL(resolved.href, window.location.origin).href
  const shareData = {
    title: `${restroom.name} | 화장실록`,
    text: `${restroom.name}\n${restroom.address}`,
    url: shareUrl,
  }

  if (navigator.share) {
    try {
      await navigator.share(shareData)
      showNotice('화장실 정보를 공유했습니다.')
      return
    } catch (error) {
      if (error?.name === 'AbortError') return
    }
  }

  try {
    await navigator.clipboard.writeText(`${shareData.text}\n${shareUrl}`)
    showNotice('화장실 위치와 페이지 링크를 복사했습니다.')
  } catch {
    const textarea = document.createElement('textarea')
    textarea.value = `${shareData.text}\n${shareUrl}`
    textarea.setAttribute('readonly', '')
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    textarea.remove()
    showNotice('화장실 위치와 페이지 링크를 복사했습니다.')
  }
}

function openSelectedDetailOnMobile() {
  mobileMode.value = 'list'
  requestAnimationFrame(() => {
    document.querySelector('.restroom-detail-panel')?.scrollIntoView({ behavior: 'smooth' })
  })
}

watch(
  () => [route.query.q, route.query.radius, route.query.restroomId, route.query.selected, route.query.source],
  () => {
    keyword.value = String(route.query.q || '화장실')
    radius.value = Number(route.query.radius || radius.value || 1000)
    loadRestrooms({ preserveSelection: false })
  },
)
watch([sort, radius], () => loadRestrooms())
watch(filters, () => loadRestrooms(), { deep: true })
watch(selectedId, loadReviews)
watch(reviewSort, loadReviews)

onMounted(() => loadRestrooms({ preserveSelection: false }))
</script>

<template>
  <main class="map-search-view">
    <form class="map-search-toolbar" @submit.prevent="submitSearch">
      <button class="map-back-button" type="button" aria-label="홈으로" @click="router.push('/')">←</button>
      <div class="map-search-input-wrap">
        <span aria-hidden="true">⌕</span>
        <input v-model="keyword" type="search" aria-label="검색어" placeholder="지역명, 역명, 관광지 또는 화장실명" />
      </div>
      <button class="map-search-submit" type="submit">검색</button>
    </form>

    <div class="mobile-result-tabs" aria-label="모바일 검색 화면 전환">
      <button :class="{ active: mobileMode === 'list' }" type="button" @click="mobileMode = 'list'">목록·리뷰</button>
      <button :class="{ active: mobileMode === 'map' }" type="button" @click="mobileMode = 'map'">지도</button>
    </div>

    <div
      class="map-search-workspace"
      :class="[
        `mobile-${mobileMode}`,
        { 'map-search-workspace--focused': selectedOnlyMapMode },
      ]"
    >
      <aside v-if="!selectedOnlyMapMode" class="restroom-list-pane">
        <header class="result-control-panel">
          <div class="result-count-row">
            <div class="result-title-block">
              <strong>{{ resultPlaceName }} 주변 화장실</strong>
              <span>{{ restrooms.length }}곳</span>
            </div>
            <select v-model="sort" aria-label="화장실 정렬">
              <option value="distance">가까운 순</option>
              <option value="cleanliness">청결도 높은 순</option>
              <option value="reviews">리뷰 많은 순</option>
            </select>
          </div>

          <div class="filter-chip-scroller">
            <button
              class="filter-scroll-button"
              type="button"
              aria-label="이전 검색 조건 보기"
              @click="scrollFilters(-1)"
            >
              ‹
            </button>

            <div ref="filterChipRow" class="filter-chip-row">
              <button :class="{ active: filters.openNow }" type="button" @click="toggleFilter('openNow')">현재 개방</button>
              <button :class="{ active: filters.diaperTable }" type="button" @click="toggleFilter('diaperTable')">기저귀 교환대</button>
              <button :class="{ active: filters.accessible }" type="button" @click="toggleFilter('accessible')">장애인용</button>
              <button :class="{ active: filters.emergencyBell }" type="button" @click="toggleFilter('emergencyBell')">비상벨</button>
              <button :class="{ active: filters.recentReview }" type="button" @click="toggleFilter('recentReview')">리뷰 있는 곳</button>
            </div>

            <button
              class="filter-scroll-button"
              type="button"
              aria-label="다음 검색 조건 보기"
              @click="scrollFilters(1)"
            >
              ›
            </button>
          </div>

          <div class="radius-and-reset">
            <label>
              검색 반경
              <select v-model="radius">
                <option :value="200">200m</option>
                <option :value="500">500m</option>
                <option :value="1000">1km</option>
                <option :value="2000">2km</option>
              </select>
            </label>
            <button v-if="activeFilterCount" type="button" @click="clearFilters">필터 초기화</button>
          </div>
        </header>

        <RestroomResultList
          :restrooms="restrooms"
          :selected-id="selectedId"
          :loading="loading"
          :error="error"
          @select="selectRestroom"
        />
      </aside>

      <RestroomDetailPanel
        class="restroom-detail-pane"
        :restroom="selectedRestroom"
        :reviews="reviews"
        :review-sort="reviewSort"
        :reviews-loading="reviewsLoading"
        @update:review-sort="reviewSort = $event"
        @write-review="writeReview"
        @share="shareSelectedRestroom"
        @open-review-post="openReviewPost"
      />

      <div class="restroom-map-pane">
        <RestroomMapPanel
          :restrooms="mapRestrooms"
          :selected-id="selectedId"
          :anchor-location="searchAnchorLocation"
          :selected-only="selectedOnlyMapMode"
          :show-research-button="!selectedOnlyMapMode"
          @select="selectRestroom"
          @search-current-map="searchCurrentMap"
          @open-detail="openSelectedDetailOnMobile"
        />
      </div>
    </div>

    <p v-if="notice" class="map-search-toast" role="status">{{ notice }}</p>
  </main>
</template>
