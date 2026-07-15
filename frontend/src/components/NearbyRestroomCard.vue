<script setup>
import { computed } from 'vue'

const props = defineProps({
  restroom: { type: Object, required: true },
  radius: { type: Number, default: 500 },
  originKeyword: { type: String, default: '역삼역 멀티캠퍼스' },
  selected: { type: Boolean, default: false },
})

const emit = defineEmits(['select'])

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
    :class="{ selected }"
    :aria-current="selected ? 'true' : undefined"
    @click="emit('select', restroom.id)"
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
      <h3>{{ restroom.name }}</h3>
      <span class="nearby-distance">도보 {{ restroom.distanceMeters }}m</span>
    </div>

    <div class="nearby-card-summary">
      <strong v-if="restroom.rating != null" :class="ratingClass">
        ★ {{ restroom.rating.toFixed(1) }}
      </strong>
      <span :class="restroom.openNow ? 'open-status' : 'closed-status'">
        <i aria-hidden="true"></i>
        {{ restroom.openNow ? '현재 개방' : '운영 종료' }}
      </span>
      <span class="nearby-review-count">
        {{ restroom.reviewCount ? `리뷰 ${restroom.reviewCount}개` : '리뷰 없음' }}
      </span>
    </div>

    <p v-if="restroom.latestReview" class="nearby-latest-review">“{{ restroom.latestReview }}”</p>

    <div v-if="restroom.latestReviewLabel" class="nearby-card-bottom">
      <span>{{ restroom.latestReviewLabel }}</span>
    </div>
  </RouterLink>
</template>
