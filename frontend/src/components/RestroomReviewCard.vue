<script setup>
defineProps({
  review: { type: Object, required: true },
  distanceMeters: { type: Number, required: true },
})

function ratingClass(rating) {
  if (rating >= 4) return 'rating-high'
  if (rating >= 3) return 'rating-mid'
  return 'rating-low'
}
</script>

<template>
  <article class="restroom-review-card">
    <header>
      <div>
        <h4>{{ review.title }}</h4>
        <div class="review-card-meta">
          <strong :class="ratingClass(review.cleanliness)">★ 청결도 {{ review.cleanliness }}</strong>
          <span>{{ distanceMeters }}m</span>
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

    <footer>
      <button type="button">댓글 {{ review.commentCount }}</button>
    </footer>
  </article>
</template>
