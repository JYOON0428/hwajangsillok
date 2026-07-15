<script setup>
const props = defineProps({
  review: { type: Object, required: true },
  distanceMeters: { type: Number, default: null },
  showDistance: { type: Boolean, default: true },
  showChevron: { type: Boolean, default: false },
  variant: { type: String, default: 'card' },
})

const emit = defineEmits(['open-post'])

function ratingClass(rating) {
  if (rating == null) return 'rating-none'
  if (rating >= 4) return 'rating-high'
  if (rating >= 3) return 'rating-mid'
  return 'rating-low'
}

function openPost() {
  emit('open-post', props.review)
}

function handleKeydown(event) {
  if (event.key !== 'Enter' && event.key !== ' ') return
  event.preventDefault()
  openPost()
}
</script>

<template>
  <article
    class="restroom-review-card restroom-review-card--link"
    :class="`restroom-review-card--${variant}`"
    role="link"
    tabindex="0"
    :aria-label="`${review.title} 게시글로 이동`"
    @click="openPost"
    @keydown="handleKeydown"
  >
    <header class="restroom-review-card__header">
      <div class="restroom-review-card__title-group">
        <h4>{{ review.title }}</h4>
        <div class="review-card-meta">
          <strong :class="ratingClass(review.cleanliness)">
            {{ review.cleanliness == null ? '평점 없음' : `★ ${review.cleanliness}` }}
          </strong>
          <span v-if="review.nickname">{{ review.nickname }}</span>
          <span v-if="showDistance && distanceMeters != null">{{ distanceMeters }}m</span>
          <span v-if="review.createdAtLabel">{{ review.createdAtLabel }}</span>
        </div>
      </div>

      <span v-if="showChevron" class="restroom-review-card__chevron" aria-hidden="true">
        <svg viewBox="0 0 20 20" fill="none">
          <path d="m8 5 5 5-5 5" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </span>
    </header>

    <p>{{ review.content }}</p>

    <div
      v-if="review.imageUrls?.length"
      class="review-image-grid"
      :class="`count-${Math.min(review.imageUrls.length, 3)}`"
    >
      <img
        v-for="(imageUrl, index) in review.imageUrls.slice(0, 3)"
        :key="imageUrl"
        :src="imageUrl"
        :alt="`${review.title} 사진 ${index + 1}`"
      />
      <span v-if="review.imageUrls.length > 3" class="more-images">
        +{{ review.imageUrls.length - 3 }}
      </span>
    </div>
  </article>
</template>
