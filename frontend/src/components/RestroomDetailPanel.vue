<script setup>
import RestroomReviewCard from './RestroomReviewCard.vue'

defineProps({
  restroom: { type: Object, default: null },
  reviews: { type: Array, default: () => [] },
  reviewSort: { type: String, default: 'recent' },
  reviewsLoading: { type: Boolean, default: false },
})

const emit = defineEmits(['update:reviewSort', 'write-review', 'share'])

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
      <p>목록이나 지도 핀을 선택하면 시설 정보와 리뷰가 표시됩니다.</p>
    </div>

    <template v-else>
      <header class="restroom-detail-header">
        <div class="detail-title-row">
          <div>
            <span class="detail-eyebrow">선택한 화장실</span>
            <h2>{{ restroom.name }}</h2>
          </div>
          <span class="detail-distance">{{ restroom.distanceMeters }}m</span>
        </div>

        <div class="detail-summary-line">
          <strong :class="ratingClass(restroom.rating)">
            {{ restroom.rating == null ? '리뷰 없음' : `★ ${restroom.rating}` }}
          </strong>
          <span>리뷰 {{ restroom.reviewCount }}개</span>
          <span
            class="operation-status-badge"
            :class="operationStatus(restroom).className"
          >
            <i aria-hidden="true" />
            {{ operationStatus(restroom).label }}
          </span>
        </div>

        <p class="detail-address">{{ restroom.address }}</p>
        <p class="detail-hours">운영시간 {{ restroom.openingHours }}</p>

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
            이 화장실 리뷰 작성
          </button>
          <button
            type="button"
            class="detail-share-button"
            @click="emit('share')"
          >
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <circle cx="18" cy="5" r="2.5" stroke="currentColor" stroke-width="1.8" />
              <circle cx="6" cy="12" r="2.5" stroke="currentColor" stroke-width="1.8" />
              <circle cx="18" cy="19" r="2.5" stroke="currentColor" stroke-width="1.8" />
              <path d="m8.2 10.8 7.6-4.5M8.2 13.2l7.6 4.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
            </svg>
            공유
          </button>
        </div>
      </header>

      <div class="public-data-box">
        <div class="data-box-title">
          <strong>공공데이터 시설 정보</strong>
          <small>기준일 {{ restroom.dataReferenceDate }}</small>
        </div>
        <div class="facility-grid">
          <span :class="{ unavailable: !restroom.facilities.diaperTable }">기저귀 교환대</span>
          <span :class="{ unavailable: !restroom.facilities.accessible }">장애인용 시설</span>
          <span :class="{ unavailable: !restroom.facilities.emergencyBell }">비상벨</span>
          <span :class="{ unavailable: !restroom.facilities.entranceCctv }">입구 CCTV</span>
          <span :class="{ unavailable: !restroom.facilities.open24Hours }">24시간 개방</span>
        </div>
        <p>실제 운영 상태는 현장 상황과 다를 수 있습니다.</p>
      </div>

      <section class="reviews-section">
        <div class="reviews-heading">
          <div>
            <h3>이용자 리뷰</h3>
            <span>{{ reviews.length }}개 표시</span>
          </div>
          <select
            :value="reviewSort"
            aria-label="리뷰 정렬"
            @change="emit('update:reviewSort', $event.target.value)"
          >
            <option value="recent">최신순</option>
            <option value="cleanlinessHigh">청결도 높은 순</option>
            <option value="cleanlinessLow">청결도 낮은 순</option>
            <option value="comments">댓글 많은 순</option>
          </select>
        </div>

        <p v-if="reviewsLoading" class="search-state">리뷰를 불러오는 중입니다.</p>
        <div v-else-if="!reviews.length" class="empty-review-state">
          <strong>아직 등록된 리뷰가 없습니다.</strong>
          <p>첫 번째 리뷰를 남겨보세요.</p>
          <button type="button" class="primary-button" @click="emit('write-review')">리뷰 작성</button>
        </div>
        <div v-else class="review-card-list">
          <RestroomReviewCard
            v-for="review in reviews"
            :key="review.id"
            :review="review"
            :distance-meters="restroom.distanceMeters"
          />
        </div>
      </section>
    </template>
  </section>
</template>
