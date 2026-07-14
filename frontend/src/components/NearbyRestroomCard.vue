<script setup>
import { computed } from 'vue'

const props = defineProps({
  restroom: { type: Object, required: true },
  radius: { type: Number, default: 500 },
  originKeyword: { type: String, default: '역삼역 멀티캠퍼스' },
})

const ratingClass = computed(() => {
  if (props.restroom.rating == null) return 'rating-none'
  if (props.restroom.rating >= 4) return 'rating-high'
  if (props.restroom.rating >= 3) return 'rating-mid'
  return 'rating-low'
})
</script>

<template>
  <RouterLink
    class="nearby-restroom-card"
    :to="{
      name: 'search',
      query: {
        q: originKeyword,
        radius,
        source: 'nearby-card',
        restroomId: restroom.id,
      },
    }"
  >
    <div class="nearby-card-top">
      <div>
        <span class="nearby-distance">도보 {{ restroom.distanceMeters }}m</span>
        <h3>{{ restroom.name }}</h3>
      </div>
      <strong :class="ratingClass">
        {{ restroom.rating == null ? '리뷰 없음' : `★ ${restroom.rating.toFixed(1)}` }}
      </strong>
    </div>

    <p v-if="restroom.latestReview" class="nearby-latest-review">“{{ restroom.latestReview }}”</p>
    <p v-else class="nearby-latest-review empty">아직 등록된 리뷰가 없습니다.</p>

    <div class="nearby-card-bottom">
      <span :class="restroom.openNow ? 'open-status' : 'closed-status'">
        {{ restroom.openNow ? '현재 개방' : '운영 종료' }}
      </span>
      <span>리뷰 {{ restroom.reviewCount }}개</span>
      <span v-if="restroom.latestReviewLabel">{{ restroom.latestReviewLabel }}</span>
    </div>
  </RouterLink>
</template>
