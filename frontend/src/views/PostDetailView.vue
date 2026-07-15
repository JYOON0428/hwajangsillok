<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { deletePost, getPost, verifyPostPassword } from '../services/postApi'
import ImageCarousel from '../components/ImageCarousel.vue'
import PasswordModal from '../components/PasswordModal.vue'
import PostVoteControl from '../components/PostVoteControl.vue'

const props = defineProps({ id: { type: String, required: true } })
const route = useRoute()
const router = useRouter()
const post = ref(null)
const loading = ref(true)
const error = ref('')
const deleteModalOpen = ref(false)
const deleteBusy = ref(false)
const deleteError = ref('')
const editModalOpen = ref(false)
const editBusy = ref(false)
const editError = ref('')
const notice = ref('')
let noticeTimer = null

const images = computed(() => {
  if (!post.value) return []
  if (Array.isArray(post.value.imageUrls) && post.value.imageUrls.length) {
    return post.value.imageUrls.filter(Boolean)
  }
  return post.value.imageUrl ? [post.value.imageUrl] : []
})

const comments = computed(() => {
  if (!post.value) return []
  if (Array.isArray(post.value.comments)) return post.value.comments
  if (Array.isArray(post.value.commentPreview)) return post.value.commentPreview
  return []
})

const ratingClass = computed(() => {
  const rating = post.value?.rating
  if (rating == null) return 'rating-none'
  if (rating >= 4) return 'rating-high'
  if (rating >= 3) return 'rating-mid'
  return 'rating-low'
})

const createdAtLabel = computed(() => {
  if (!post.value?.createdAt) return ''
  const createdAt = new Date(post.value.createdAt)
  if (Number.isNaN(createdAt.getTime())) return post.value.createdAtLabel || ''
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

async function load() {
  loading.value = true
  error.value = ''
  try {
    post.value = await getPost(props.id)
    await nextTick()
    if (route.hash === '#comments') {
      document.querySelector('#comments')?.scrollIntoView({ block: 'start' })
    }
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function confirmDelete(password) {
  deleteBusy.value = true
  deleteError.value = ''
  try {
    await deletePost(props.id, password)
    router.push({ name: 'community' })
  } catch (err) {
    deleteError.value = err.message
  } finally {
    deleteBusy.value = false
  }
}

async function confirmEdit(password) {
  editBusy.value = true
  editError.value = ''
  try {
    await verifyPostPassword(props.id, password)
    sessionStorage.setItem(`post-edit-password-${props.id}`, password)
    editModalOpen.value = false
    router.push({ name: 'post-edit', params: { id: props.id } })
  } catch (err) {
    editError.value = err.message || '비밀번호가 일치하지 않습니다.'
  } finally {
    editBusy.value = false
  }
}

function showNotice(message) {
  notice.value = message
  window.clearTimeout(noticeTimer)
  noticeTimer = window.setTimeout(() => {
    notice.value = ''
  }, 2400)
}

async function copyText(text) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text)
    return
  }

  const textarea = document.createElement('textarea')
  textarea.value = text
  textarea.setAttribute('readonly', '')
  textarea.style.position = 'fixed'
  textarea.style.opacity = '0'
  document.body.appendChild(textarea)
  textarea.select()
  document.execCommand('copy')
  textarea.remove()
}

async function sharePost() {
  if (!post.value) return

  const url = window.location.href
  const shareData = {
    title: `${post.value.title} | 화장실록`,
    text: post.value.restroomName
      ? `${post.value.title}\n${post.value.restroomName}`
      : post.value.title,
    url,
  }

  if (navigator.share) {
    try {
      await navigator.share(shareData)
      showNotice('게시글을 공유했습니다.')
      return
    } catch (shareError) {
      if (shareError?.name === 'AbortError') return
    }
  }

  try {
    await copyText(`${shareData.text}\n${url}`)
    showNotice('게시글 링크를 복사했습니다.')
  } catch {
    showNotice('링크를 복사하지 못했습니다.')
  }
}

function openAiForPost() {
  if (!post.value) return
  window.dispatchEvent(
    new CustomEvent('open-ai-chat', {
      detail: `${post.value.title} 관련 화장실과 최근 리뷰를 요약해줘.`,
    }),
  )
}

onMounted(load)
</script>

<template>
  <main class="community-detail-page">
    <div class="page-container community-detail-shell">
      <button class="community-detail-back" type="button" @click="router.back()">
        <span aria-hidden="true">←</span>
        목록으로
      </button>

      <p v-if="loading" class="state-message">게시글을 불러오는 중입니다.</p>
      <p v-else-if="error" class="state-message error">{{ error }}</p>

      <template v-else-if="post">
        <article class="community-detail-card">
          <header class="community-detail-meta">
            <div class="community-post-card__badges">
              <span class="category">{{ post.category }}</span>
              <span class="type">{{ post.postType || '게시글' }}</span>
            </div>
            <p>{{ post.nickname || '익명 사용자' }} · {{ createdAtLabel }}</p>
          </header>

          <div class="community-detail-title-row">
            <h1>{{ post.title }}</h1>

            <span
              v-if="post.rating != null"
              class="community-cleanliness-badge community-cleanliness-badge--detail"
              :class="ratingClass"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="m12 2.8 2.8 5.7 6.3.9-4.6 4.4 1.1 6.2-5.6-3-5.6 3 1.1-6.2-4.6-4.4 6.3-.9L12 2.8Z" fill="currentColor" />
              </svg>
              <span>청결도</span>
              <strong>{{ Number(post.rating).toFixed(1) }}</strong>
            </span>
          </div>

          <dl v-if="post.relatedPlace || post.restroomName" class="community-detail-location">
            <div v-if="post.relatedPlace">
              <dt>관련 장소</dt>
              <dd>{{ post.relatedPlace }}</dd>
            </div>
            <div v-if="post.restroomName">
              <dt>관련 화장실</dt>
              <dd>{{ post.restroomName }}</dd>
            </div>
          </dl>

          <p class="community-detail-content">{{ post.content }}</p>

          <ImageCarousel
            v-if="images.length"
            :images="images"
            :alt="post.title"
            variant="detail"
          />

          <footer class="community-detail-actions">
            <PostVoteControl
              :post-id="post.id"
              :score="post.recommendationCount || 0"
              :downvotes="post.dislikeCount || 0"
            />

            <button class="community-action-button" type="button" @click="sharePost">
              <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <circle cx="18" cy="5" r="2.2" stroke="currentColor" stroke-width="1.8" />
                <circle cx="6" cy="12" r="2.2" stroke="currentColor" stroke-width="1.8" />
                <circle cx="18" cy="19" r="2.2" stroke="currentColor" stroke-width="1.8" />
                <path d="m8 11 8-5M8 13l8 5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
              </svg>
              공유
            </button>

            <div class="community-detail-manage">
              <button type="button" @click="editModalOpen = true">수정</button>
              <button class="danger" type="button" @click="deleteModalOpen = true">삭제</button>
              <button class="primary" type="button" @click="openAiForPost">AI 관련 정보</button>
            </div>
          </footer>
        </article>

        <section id="comments" class="community-comments-panel">
          <header>
            <div>
              <span>댓글</span>
              <strong>{{ post.commentCount || comments.length }}</strong>
            </div>
            <p>다른 이용자의 추가 정보와 경험을 확인하세요.</p>
          </header>

          <div v-if="comments.length" class="community-comments-list">
            <article v-for="comment in comments" :key="comment.id" class="community-comment-item">
              <div>
                <strong>{{ comment.nickname || '익명 사용자' }}</strong>
                <time v-if="comment.createdAtLabel">{{ comment.createdAtLabel }}</time>
              </div>
              <p>{{ comment.content }}</p>
            </article>
          </div>

          <div v-else class="community-comments-empty">
            <strong>아직 등록된 댓글이 없습니다.</strong>
            <p>댓글 API가 연결되면 이 영역에 댓글이 표시됩니다.</p>
          </div>
        </section>
      </template>
    </div>

    <PasswordModal
      :open="deleteModalOpen"
      title="게시글 삭제"
      :busy="deleteBusy"
      :error="deleteError"
      @close="deleteModalOpen = false"
      @confirm="confirmDelete"
    />

    <PasswordModal
      :open="editModalOpen"
      title="게시글 수정"
      :busy="editBusy"
      :error="editError"
      @close="editModalOpen = false"
      @confirm="confirmEdit"
    />

    <p v-if="notice" class="community-feed-toast" role="status">{{ notice }}</p>
  </main>
</template>
