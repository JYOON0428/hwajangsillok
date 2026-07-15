<script setup>
import { computed } from 'vue'
import ImageCarousel from './ImageCarousel.vue'
import PostVoteControl from './PostVoteControl.vue'

const props = defineProps({
  post: { type: Object, required: true },
})

const emit = defineEmits(['share'])

const detailRoute = computed(() => ({
  name: 'post-detail',
  params: { id: props.post.id },
}))

const commentsRoute = computed(() => ({
  ...detailRoute.value,
  hash: '#comments',
}))

const restroomReviewsRoute = computed(() => {
  if (!props.post.restroomId) return detailRoute.value

  return {
    name: 'restroom-reviews',
    params: { id: props.post.restroomId },
  }
})

const hasRestroomReviewLink = computed(
  () => Boolean(props.post.restroomId && props.post.restroomName),
)

const isFreeBoard = computed(() => props.post.category === '자유게시판')

function getCategoryLabel(value) {
  return value === '일반 게시판' || value === '일반'
    ? '일반'
    : value
}

const categoryBadgeLabel = computed(() => getCategoryLabel(props.post.category))
const typeBadgeLabel = computed(() => getCategoryLabel(props.post.postType))

const showTypeBadge = computed(() => {
  const type = String(props.post.postType || '').trim()
  if (!type) return false
  if (getCategoryLabel(type) === categoryBadgeLabel.value) return false
  if (type === '화장실 리뷰') return false
  return true
})

const showRating = computed(
  () => !isFreeBoard.value && props.post.rating != null,
)

const primaryLocation = computed(
  () => props.post.restroomName || props.post.relatedPlace || '',
)

const secondaryLocation = computed(() => {
  if (!props.post.restroomName || !props.post.relatedPlace) return ''
  if (props.post.restroomName === props.post.relatedPlace) return ''
  return props.post.relatedPlace
})

const showLocation = computed(
  () => !isFreeBoard.value && Boolean(primaryLocation.value),
)

const ratingClass = computed(() => {
  if (props.post.rating == null) return 'rating-none'
  if (props.post.rating >= 4) return 'rating-high'
  if (props.post.rating >= 3) return 'rating-mid'
  return 'rating-low'
})

const timeLabel = computed(() => {
  const createdAt = new Date(props.post.createdAt)
  if (Number.isNaN(createdAt.getTime())) return props.post.createdAtLabel || ''
  const diff = Date.now() - createdAt.getTime()
  const minutes = Math.max(0, Math.floor(diff / 60000))

  if (minutes < 1) return '방금 전'
  if (minutes < 60) return `${minutes}분 전`

  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}시간 전`

  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}일 전`

  return new Intl.DateTimeFormat('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(createdAt)
})

const images = computed(() => {
  if (Array.isArray(props.post.imageUrls) && props.post.imageUrls.length) {
    return props.post.imageUrls.filter(Boolean)
  }
  return props.post.imageUrl ? [props.post.imageUrl] : []
})

const commentPreview = computed(() => {
  const source = Array.isArray(props.post.commentPreview)
    ? props.post.commentPreview
    : Array.isArray(props.post.comments)
      ? props.post.comments
      : []
  return source.slice(0, 1)
})
</script>

<template>
  <article class="community-post-card">
    <header class="community-post-card__header">
      <div class="community-post-card__badges">
        <span class="category">{{ categoryBadgeLabel }}</span>
        <span v-if="showTypeBadge" class="type">{{ typeBadgeLabel }}</span>
      </div>

      <div class="community-post-card__meta">
        <span>{{ post.nickname || '익명 사용자' }}</span>
        <span aria-hidden="true">·</span>
        <time :datetime="post.createdAt">{{ timeLabel }}</time>
      </div>
    </header>

    <RouterLink :to="detailRoute" class="community-post-card__title-link">
      <h2>{{ post.title }}</h2>
    </RouterLink>

    <RouterLink class="community-post-card__content-link" :to="detailRoute">
      <p>{{ post.content }}</p>
    </RouterLink>

    <div v-if="showLocation || showRating" class="community-post-card__context-row">
      <RouterLink
        v-if="showLocation"
        class="community-post-card__location-row"
        :to="restroomReviewsRoute"
        :aria-label="hasRestroomReviewLink ? `${primaryLocation} 화장실 후기 보기` : `${primaryLocation} 관련 게시글 보기`"
      >
        <span class="community-post-card__location-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none">
            <path d="M12 21s7-6.1 7-12a7 7 0 1 0-14 0c0 5.9 7 12 7 12Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" />
            <circle cx="12" cy="9" r="2.4" stroke="currentColor" stroke-width="1.8" />
          </svg>
        </span>
        <span class="community-post-card__location-copy">
          <strong>{{ primaryLocation }}</strong>
          <small v-if="secondaryLocation">{{ secondaryLocation }}</small>
        </span>
      </RouterLink>

      <span
        v-if="showRating"
        class="community-post-card__rating-inline"
        :class="ratingClass"
        aria-label="청결도 평점"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="m12 2.8 2.8 5.7 6.3.9-4.6 4.4 1.1 6.2-5.6-3-5.6 3 1.1-6.2-4.6-4.4 6.3-.9L12 2.8Z" fill="currentColor" />
        </svg>
        <span>청결도</span>
        <strong>{{ Number(post.rating).toFixed(1) }}</strong>
      </span>
    </div>

    <ImageCarousel
      v-if="images.length"
      :images="images"
      :alt="post.title"
      variant="feed"
    />

    <footer class="community-post-card__actions">
      <PostVoteControl
        :post-id="post.id"
        :score="post.recommendationCount || 0"
        :downvotes="post.dislikeCount || 0"
      />

      <RouterLink class="community-action-button" :to="commentsRoute">
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M5 5h14v11H9l-4 3V5Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" />
        </svg>
        댓글 {{ post.commentCount || 0 }}
      </RouterLink>

      <button class="community-action-button" type="button" @click="emit('share', post)">
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <circle cx="18" cy="5" r="2.2" stroke="currentColor" stroke-width="1.8" />
          <circle cx="6" cy="12" r="2.2" stroke="currentColor" stroke-width="1.8" />
          <circle cx="18" cy="19" r="2.2" stroke="currentColor" stroke-width="1.8" />
          <path d="m8 11 8-5M8 13l8 5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
        </svg>
        공유
      </button>
    </footer>

    <section v-if="commentPreview.length" class="community-comment-preview" aria-label="최근 댓글 미리보기">
      <RouterLink
        v-for="comment in commentPreview"
        :key="comment.id"
        :to="commentsRoute"
        class="community-comment-preview__row"
      >
        <span class="community-comment-preview__icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none">
            <path
              d="M5 5h14v11H9l-4 3V5Z"
              stroke="currentColor"
              stroke-width="1.8"
              stroke-linejoin="round"
            />
          </svg>
        </span>

        <span class="community-comment-preview__label">최근 댓글</span>
        <strong>{{ comment.nickname || '익명 사용자' }}</strong>
        <p>{{ comment.content }}</p>

        <span class="community-comment-preview__more">
          댓글 {{ post.commentCount || commentPreview.length }}개
          <span aria-hidden="true">›</span>
        </span>
      </RouterLink>
    </section>
  </article>
</template>
