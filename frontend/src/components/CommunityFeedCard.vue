<script setup>
import { computed } from 'vue'
import ImageCarousel from './ImageCarousel.vue'
import PostVoteControl from './PostVoteControl.vue'

const props = defineProps({
  post: { type: Object, required: true },
})

const emit = defineEmits(['share'])

const ratingClass = computed(() => {
  if (props.post.rating == null) return 'rating-none'
  if (props.post.rating >= 4) return 'rating-high'
  if (props.post.rating >= 3) return 'rating-mid'
  return 'rating-low'
})

const timeLabel = computed(() => {
  const createdAt = new Date(props.post.createdAt)
  const diff = Date.now() - createdAt.getTime()
  const minutes = Math.max(1, Math.floor(diff / 60000))

  if (minutes < 60) return `${minutes}분 전`

  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}시간 전`

  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}일 전`

  return new Intl.DateTimeFormat('ko-KR', {
    month: 'long',
    day: 'numeric',
  }).format(createdAt)
})

const locationLabel = computed(
  () => props.post.restroomName || props.post.relatedPlace || '',
)

const images = computed(() => {
  if (Array.isArray(props.post.imageUrls) && props.post.imageUrls.length) {
    return props.post.imageUrls.filter(Boolean)
  }
  return props.post.imageUrl ? [props.post.imageUrl] : []
})
</script>

<template>
  <article class="reddit-feed-card">
    <PostVoteControl
      class="reddit-feed-card__votes"
      :post-id="post.id"
      :score="post.recommendationCount || 0"
    />

    <div class="reddit-feed-card__body">
      <header class="reddit-feed-card__meta">
        <div class="reddit-feed-card__meta-left">
          <span class="reddit-feed-card__category">{{ post.category }}</span>
          <span class="reddit-feed-card__type">{{ post.postType }}</span>
          <span class="reddit-feed-card__author">{{ post.nickname || '익명 사용자' }}</span>
          <time :datetime="post.createdAt">{{ timeLabel }}</time>
        </div>
      </header>

      <RouterLink
        v-if="locationLabel"
        class="reddit-feed-card__location"
        :to="{ name: 'post-detail', params: { id: post.id } }"
      >
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path
            d="M12 21s7-6.1 7-12a7 7 0 1 0-14 0c0 5.9 7 12 7 12Z"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linejoin="round"
          />
          <circle cx="12" cy="9" r="2.4" stroke="currentColor" stroke-width="1.8" />
        </svg>
        {{ locationLabel }}
      </RouterLink>

      <div class="reddit-feed-card__title-row">
        <RouterLink :to="{ name: 'post-detail', params: { id: post.id } }">
          <h2>{{ post.title }}</h2>
        </RouterLink>

        <span
          v-if="post.rating != null"
          class="reddit-cleanliness-score"
          :class="ratingClass"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="m12 2.8 2.8 5.7 6.3.9-4.6 4.4 1.1 6.2-5.6-3-5.6 3 1.1-6.2-4.6-4.4 6.3-.9L12 2.8Z" fill="currentColor" />
          </svg>
          <span>청결도</span>
          <strong>{{ Number(post.rating).toFixed(1) }}</strong>
        </span>
      </div>

      <RouterLink
        class="reddit-feed-card__text-link"
        :to="{ name: 'post-detail', params: { id: post.id } }"
      >
        <p>{{ post.content }}</p>
      </RouterLink>

      <ImageCarousel
        v-if="images.length"
        :images="images"
        :alt="post.title"
        variant="feed"
      />

      <footer class="reddit-feed-card__actions">
        <RouterLink
          class="reddit-action-button"
          :to="{ name: 'post-detail', params: { id: post.id } }"
        >
          <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M5 5h14v11H9l-4 3V5Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" />
          </svg>
          댓글 {{ post.commentCount || 0 }}
        </RouterLink>

        <button class="reddit-action-button" type="button" @click="emit('share', post)">
          <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <circle cx="18" cy="5" r="2.2" stroke="currentColor" stroke-width="1.8" />
            <circle cx="6" cy="12" r="2.2" stroke="currentColor" stroke-width="1.8" />
            <circle cx="18" cy="19" r="2.2" stroke="currentColor" stroke-width="1.8" />
            <path d="m8 11 8-5M8 13l8 5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
          </svg>
          공유
        </button>
      </footer>
    </div>
  </article>
</template>
