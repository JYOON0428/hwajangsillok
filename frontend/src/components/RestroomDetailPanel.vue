<script setup>
import { computed } from 'vue'
import RestroomReviewCard from './RestroomReviewCard.vue'

const props = defineProps({
  restroom: { type: Object, default: null },
  reviews: { type: Array, default: () => [] },
  reviewSort: { type: String, default: 'recent' },
  reviewsLoading: { type: Boolean, default: false },
  closable: { type: Boolean, default: true },
})

const emit = defineEmits([
  'update:reviewSort',
  'write-review',
  'share',
  'close',
  'open-reviews',
  'open-review-post',
])

const recentReviews = computed(() => props.reviews.slice(0, 2))

const availableFacilities = computed(() => {
  const facilities = props.restroom?.facilities || {}
  return [
    ['diaperTable', '기저귀 교환대'],
    ['accessible', '장애인용 시설'],
    ['emergencyBell', '비상벨'],
    ['entranceCctv', '입구 CCTV'],
    ['open24Hours', '24시간 개방'],
  ]
    .filter(([key]) => Boolean(facilities[key]))
    .map(([, label]) => label)
})

function ratingClass(rating) {
  if (rating == null) return 'rating-none'
  if (rating >= 4) return 'rating-high'
  if (rating >= 3) return 'rating-mid'
  return 'rating-low'
}

function operationStatus(restroom) {
  if (restroom.openNow === true) {
    return { label: '현재 개방', className: 'status-open' }
  }
  if (restroom.openNow === false) {
    return { label: '현재 운영 종료', className: 'status-closed' }
  }
  return { label: '운영 여부 확인 필요', className: 'status-unknown' }
}
</script>

<template>
  <section class="restroom-detail-panel">
    <div v-if="!restroom" class="detail-placeholder">
      <strong>화장실을 선택하세요.</strong>
      <p>목록이나 지도 핀을 선택하면 시설 정보와 최근 리뷰가 표시됩니다.</p>
    </div>

    <template v-else>
      <header class="restroom-detail-header restroom-detail-header--refined">
        <div class="restroom-detail-header__top">
          <span class="detail-eyebrow">선택한 화장실</span>
          <button
            v-if="closable"
            class="restroom-detail-close"
            type="button"
            aria-label="화장실 상세 닫기"
            @click="emit('close')"
          >
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="m7 7 10 10M17 7 7 17" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
            </svg>
          </button>
        </div>

        <div class="detail-title-row">
          <h2>{{ restroom.name }}</h2>
          <span class="detail-distance">{{ restroom.distanceMeters }}m</span>
        </div>

        <div class="detail-summary-line">
          <strong :class="ratingClass(restroom.rating)">
            {{ restroom.rating == null ? '리뷰 없음' : `★ ${restroom.rating}` }}
          </strong>
          <span v-if="restroom.rating != null">리뷰 {{ restroom.reviewCount }}개</span>
          <span
            class="operation-status-badge"
            :class="operationStatus(restroom).className"
          >
            <i aria-hidden="true" />
            {{ operationStatus(restroom).label }}
          </span>
        </div>

        <div class="restroom-detail-meta-list">
          <p class="detail-address">{{ restroom.address }}</p>
          <p class="detail-hours">운영시간 {{ restroom.openingHours }}</p>
        </div>

        <div class="detail-actions refined-detail-actions">
          <button
            type="button"
            class="detail-review-button"
            @click="emit('write-review')"
          >
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M4 20h4l10.7-10.7a2.1 2.1 0 0 0-3-3L5 17v3Z" stroke="currentColor" stroke-width="1.9" stroke-linejoin="round" />
              <path d="m14.5 7.5 3 3" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" />
            </svg>
            리뷰 쓰기
          </button>
          <button
            type="button"
            class="detail-share-button"
            aria-label="화장실 정보 공유"
            @click="emit('share')"
          >
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <circle cx="18" cy="5" r="2.5" stroke="currentColor" stroke-width="1.8" />
              <circle cx="6" cy="12" r="2.5" stroke="currentColor" stroke-width="1.8" />
              <circle cx="18" cy="19" r="2.5" stroke="currentColor" stroke-width="1.8" />
              <path d="m8.2 10.8 7.6-4.5M8.2 13.2l7.6 4.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
            </svg>
            <span>공유</span>
          </button>
        </div>
      </header>

      <section class="restroom-detail-section restroom-detail-facilities">
        <div class="restroom-detail-section__heading">
          <strong>시설 정보</strong>
          <small>기준일 {{ restroom.dataReferenceDate }}</small>
        </div>

        <div v-if="availableFacilities.length" class="facility-list-refined">
          <span v-for="facility in availableFacilities" :key="facility">
            <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
              <path d="m5 10 3 3 7-7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
            {{ facility }}
          </span>
        </div>
        <p v-else class="facility-empty">확인된 편의시설 정보가 없습니다.</p>

        <p class="restroom-detail-data-note">공공데이터 기준 정보이며 실제 현장 상황과 다를 수 있습니다.</p>
      </section>

      <section class="reviews-section reviews-section--recent">
        <div class="reviews-heading reviews-heading--recent">
          <div>
            <h3>최근 리뷰</h3>
            <span>{{ restroom.reviewCount ?? reviews.length }}개</span>
          </div>
          <button
            v-if="(restroom.reviewCount ?? reviews.length) > 0"
            class="reviews-all-link"
            type="button"
            @click="emit('open-reviews')"
          >
            전체 보기
            <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
              <path d="m8 5 5 5-5 5" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </button>
        </div>

        <p v-if="reviewsLoading" class="search-state">리뷰를 불러오는 중입니다.</p>
        <div v-else-if="!reviews.length" class="empty-review-state empty-review-state--compact">
          <strong>아직 등록된 리뷰가 없습니다.</strong>
          <p>첫 이용 경험을 남겨 다른 방문자에게 도움을 주세요.</p>
          <button type="button" class="primary-button" @click="emit('write-review')">리뷰 쓰기</button>
        </div>
        <div v-else class="review-card-list review-card-list--recent">
          <RestroomReviewCard
            v-for="review in recentReviews"
            :key="review.id"
            :review="review"
            :show-distance="false"
            :show-chevron="true"
            variant="compact"
            @open-post="emit('open-review-post', $event)"
          />
        </div>

        <button
          v-if="reviews.length > 2"
          class="reviews-more-button"
          type="button"
          @click="emit('open-reviews')"
        >
          리뷰 {{ restroom.reviewCount ?? reviews.length }}개 모두 보기
        </button>
      </section>
    </template>
  </section>
</template>
