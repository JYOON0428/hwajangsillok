<script setup>
import { computed } from 'vue'

const props = defineProps({
  post: { type: Object, required: true },
})

const ratingClass = computed(() => {
  if (props.post.rating == null) return 'rating-none'
  if (props.post.rating >= 4) return 'rating-high'
  if (props.post.rating >= 3) return 'rating-mid'
  return 'rating-low'
})

const timeLabel = computed(() => {
  const diff = Date.now() - new Date(props.post.createdAt).getTime()
  const minutes = Math.max(1, Math.floor(diff / 60000))
  if (minutes < 60) return `${minutes}분 전`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}시간 전`
  return new Intl.DateTimeFormat('ko-KR', { month: '2-digit', day: '2-digit' }).format(
    new Date(props.post.createdAt),
  )
})
</script>

<template>
  <RouterLink class="post-card" :to="{ name: 'post-detail', params: { id: post.id } }">
    <div
      v-if="post.imageUrl"
      class="post-image"
      :style="{ backgroundImage: `url(${post.imageUrl})` }"
      aria-hidden="true"
    />
    <div class="post-body">
      <div class="post-badges">
        <span>{{ post.category }}</span>
        <span class="post-type">{{ post.postType }}</span>
      </div>
      <h3>{{ post.title }}</h3>
      <p>{{ post.content }}</p>
      <div v-if="post.relatedPlace" class="related-place">{{ post.relatedPlace }}</div>
      <div v-if="post.restroomName" class="related-place">{{ post.restroomName }}</div>
      <div class="post-card-footer">
        <div class="post-rating" :class="ratingClass">
          <template v-if="post.rating != null">★ {{ post.rating.toFixed(1) }}</template>
          <template v-else>댓글 {{ post.commentCount }}개</template>
        </div>
        <div class="post-meta">
          <span>댓글 {{ post.commentCount }}</span>
          <span>{{ timeLabel }}</span>
        </div>
      </div>
    </div>
  </RouterLink>
</template>
