<script setup>
const props = defineProps({
  review: { type: Object, required: true },
  distanceMeters: { type: Number, default: null },
})

const emit = defineEmits(['open-post'])

function ratingClass(rating) {
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
    role="link"
    tabindex="0"
    :aria-label="`${review.title} 게시글로 이동`"
    @click="openPost"
    @keydown="handleKeydown"
  >
    <header>
      <div>
        <h4>{{ review.title }}</h4>
        <div class="review-card-meta">
          <strong :class="ratingClass(review.cleanliness)">★ 청결도 {{ review.cleanliness }}</strong>
          <span v-if="distanceMeters != null">{{ distanceMeters }}m</span>
          <span>{{ review.createdAtLabel }}</span>
        </div>
      </div>

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
      <span v-if="review.imageUrls.length > 3" class="more-images">+{{ review.imageUrls.length - 3 }}</span>
    </div>
  </article>
</template>

<style scoped>
.restroom-review-card--link {
  cursor: pointer;
  transition:
    border-color 0.16s ease,
    box-shadow 0.16s ease,
    transform 0.16s ease;
}

.restroom-review-card--link:hover,
.restroom-review-card--link:focus-visible {
  border-color: var(--sky-300);
  box-shadow: 0 10px 24px rgba(31, 99, 136, 0.1);
  transform: translateY(-1px);
  outline: none;
}
</style>
