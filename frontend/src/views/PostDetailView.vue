<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { deletePost, getPost } from '../services/postApi'
import ImageCarousel from '../components/ImageCarousel.vue'
import PasswordModal from '../components/PasswordModal.vue'
import PostVoteControl from '../components/PostVoteControl.vue'

const props = defineProps({ id: { type: String, required: true } })
const router = useRouter()
const post = ref(null)
const loading = ref(true)
const error = ref('')
const deleteModalOpen = ref(false)
const deleteBusy = ref(false)
const deleteError = ref('')
const notice = ref('')
let noticeTimer = null

const images = computed(() => {
  if (!post.value) return []
  if (Array.isArray(post.value.imageUrls) && post.value.imageUrls.length) {
    return post.value.imageUrls.filter(Boolean)
  }
  return post.value.imageUrl ? [post.value.imageUrl] : []
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
  return new Intl.DateTimeFormat('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(post.value.createdAt))
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    post.value = await getPost(props.id)
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
  <main class="reddit-detail-page">
    <div class="page-container reddit-detail-shell">
      <button class="reddit-detail-back" type="button" @click="router.back()">
        <span aria-hidden="true">←</span>
        목록으로
      </button>

      <p v-if="loading" class="state-message">게시글을 불러오는 중입니다.</p>
      <p v-else-if="error" class="state-message error">{{ error }}</p>

      <template v-else-if="post">
        <article class="reddit-detail-card">
          <PostVoteControl
            class="reddit-detail-card__votes"
            :post-id="post.id"
            :score="post.recommendationCount || 0"
          />

          <div class="reddit-detail-card__body">
            <header class="reddit-detail-meta">
              <div>
                <span class="reddit-feed-card__category">{{ post.category }}</span>
                <span class="reddit-feed-card__type">{{ post.postType }}</span>
              </div>
              <p>{{ post.nickname || '익명 사용자' }} · {{ createdAtLabel }}</p>
            </header>

            <div class="reddit-detail-title-row">
              <h1>{{ post.title }}</h1>

              <span
                v-if="post.rating != null"
                class="reddit-cleanliness-score reddit-cleanliness-score--detail"
                :class="ratingClass"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="m12 2.8 2.8 5.7 6.3.9-4.6 4.4 1.1 6.2-5.6-3-5.6 3 1.1-6.2-4.6-4.4 6.3-.9L12 2.8Z" fill="currentColor" />
                </svg>
                <span>청결도</span>
                <strong>{{ Number(post.rating).toFixed(1) }}</strong>
              </span>
            </div>

            <p class="reddit-detail-content">{{ post.content }}</p>

            <ImageCarousel
              v-if="images.length"
              :images="images"
              :alt="post.title"
              variant="detail"
            />

            <dl v-if="post.relatedPlace || post.restroomName" class="reddit-detail-location-box">
              <div v-if="post.relatedPlace">
                <dt>관련 장소</dt>
                <dd>{{ post.relatedPlace }}</dd>
              </div>
              <div v-if="post.restroomName">
                <dt>관련 화장실</dt>
                <dd>{{ post.restroomName }}</dd>
              </div>
            </dl>

            <footer class="reddit-detail-actions">
              <div class="reddit-detail-actions__community">
                <span class="reddit-action-button static">
                  <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <path d="M5 5h14v11H9l-4 3V5Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" />
                  </svg>
                  댓글 {{ post.commentCount || 0 }}
                </span>
                <button class="reddit-action-button" type="button" @click="sharePost">
                  <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <circle cx="18" cy="5" r="2.2" stroke="currentColor" stroke-width="1.8" />
                    <circle cx="6" cy="12" r="2.2" stroke="currentColor" stroke-width="1.8" />
                    <circle cx="18" cy="19" r="2.2" stroke="currentColor" stroke-width="1.8" />
                    <path d="m8 11 8-5M8 13l8 5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
                  </svg>
                  공유
                </button>
              </div>

              <div class="reddit-detail-actions__manage">
                <RouterLink class="reddit-manage-button" :to="{ name: 'post-edit', params: { id: post.id } }">
                  수정
                </RouterLink>
                <button class="reddit-manage-button danger" type="button" @click="deleteModalOpen = true">
                  삭제
                </button>
                <button class="reddit-manage-button primary" type="button" @click="openAiForPost">
                  AI 관련 정보
                </button>
              </div>
            </footer>
          </div>
        </article>

        <section class="reddit-comments-panel">
          <header>
            <h2>댓글 {{ post.commentCount || 0 }}개</h2>
          </header>
          <div class="reddit-comments-placeholder">
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M5 5h14v11H9l-4 3V5Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" />
            </svg>
            <strong>댓글 영역</strong>
            <p>댓글 API가 연결되면 이 위치에 최신 댓글부터 표시됩니다.</p>
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

    <p v-if="notice" class="community-feed-toast" role="status">{{ notice }}</p>
  </main>
</template>
