<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  createComment,
  deleteComment,
  deletePost,
  getPost,
  updateComment,
  verifyPostPassword,
} from '../services/postApi'
import ImageCarousel from '../components/ImageCarousel.vue'
import PasswordModal from '../components/PasswordModal.vue'
import PostVoteControl from '../components/PostVoteControl.vue'

const props = defineProps({ id: { type: String, required: true } })
const route = useRoute()
const router = useRouter()

const post = ref(null)
const loading = ref(true)
const error = ref('')
const notice = ref('')
const postManageOpen = ref(false)

const deleteModalOpen = ref(false)
const deleteBusy = ref(false)
const deleteError = ref('')
const editModalOpen = ref(false)
const editBusy = ref(false)
const editError = ref('')

const commentForm = ref({
  nickname: '',
  password: '',
  content: '',
})
const commentBusy = ref(false)
const commentError = ref('')
const editingCommentId = ref(null)
const editCommentForm = ref({
  content: '',
  password: '',
})
const editCommentBusy = ref(false)
const editCommentError = ref('')
const commentDeleteModalOpen = ref(false)
const commentDeleteBusy = ref(false)
const commentDeleteError = ref('')
const selectedComment = ref(null)
let noticeTimer = null

const nicknameAdjectives = [
  '상쾌한',
  '깨끗한',
  '푸른',
  '조용한',
  '빠른',
  '따뜻한',
  '밝은',
  '느긋한',
  '산뜻한',
  '반가운',
]

const nicknameNouns = [
  '여행자',
  '시민',
  '산책러',
  '탐험가',
  '방문객',
  '나들이객',
  '길잡이',
  '이용자',
  '동네친구',
  '관찰자',
]

function getOrCreateCommentNickname() {
  const storageKey = 'hwajangsillok-comment-nickname'

  try {
    const savedNickname = sessionStorage.getItem(storageKey)
    if (savedNickname) return savedNickname

    const adjective = nicknameAdjectives[Math.floor(Math.random() * nicknameAdjectives.length)]
    const noun = nicknameNouns[Math.floor(Math.random() * nicknameNouns.length)]
    const nickname = `${adjective} ${noun}`

    sessionStorage.setItem(storageKey, nickname)
    return nickname
  } catch {
    const adjective = nicknameAdjectives[Math.floor(Math.random() * nicknameAdjectives.length)]
    const noun = nicknameNouns[Math.floor(Math.random() * nicknameNouns.length)]
    return `${adjective} ${noun}`
  }
}

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

const commentCount = computed(() => {
  const count = Number(post.value?.commentCount || 0)
  return Math.max(count, comments.value.length)
})

const commentSubmitDisabled = computed(
  () =>
    commentBusy.value ||
    !commentForm.value.content.trim() ||
    commentForm.value.password.trim().length < 4,
)

const isFreeBoard = computed(() => post.value?.category === '자유게시판')

function getCategoryLabel(value) {
  return value === '일반 게시판' || value === '일반' ? '일반' : value
}

const categoryBadgeLabel = computed(() => getCategoryLabel(post.value?.category))
const typeBadgeLabel = computed(() => getCategoryLabel(post.value?.postType))

const showTypeBadge = computed(() => {
  const type = String(post.value?.postType || '').trim()
  if (!type) return false
  if (getCategoryLabel(type) === categoryBadgeLabel.value) return false
  if (type === '화장실 리뷰') return false
  return true
})

const showRating = computed(() => !isFreeBoard.value && post.value?.rating != null)

const hasRelatedContext = computed(
  () =>
    !isFreeBoard.value &&
    Boolean(post.value?.relatedPlace || post.value?.restroomName || showRating.value),
)

const restroomReviewsRoute = computed(() => {
  if (!post.value?.restroomId) return null

  return {
    name: 'restroom-reviews',
    params: { id: post.value.restroomId },
  }
})

const ratingClass = computed(() => {
  const rating = post.value?.rating
  if (rating == null) return 'rating-none'
  if (rating >= 4) return 'rating-high'
  if (rating >= 3) return 'rating-mid'
  return 'rating-low'
})

function formatRelativeTime(value, fallback = '') {
  if (!value) return fallback
  const createdAt = new Date(value)
  if (Number.isNaN(createdAt.getTime())) return fallback

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
}

const createdAtLabel = computed(() =>
  formatRelativeTime(post.value?.createdAt, post.value?.createdAtLabel || ''),
)

function commentTimeLabel(comment) {
  const base = formatRelativeTime(comment.createdAt, comment.createdAtLabel || '')
  return comment.updatedAt ? `${base} · 수정됨` : base
}

function commentInitial(comment) {
  const nickname = String(comment?.nickname || '익명').trim()
  return nickname.charAt(0) || '익'
}

async function refreshPost() {
  post.value = await getPost(props.id)
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    await refreshPost()
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

function validateCommentForm() {
  if (commentForm.value.password.trim().length < 4) {
    return '비밀번호를 4자 이상 입력해 주세요.'
  }
  if (!commentForm.value.content.trim()) return '댓글 내용을 입력해 주세요.'
  return ''
}

async function submitComment() {
  commentError.value = validateCommentForm()
  if (commentError.value) return

  commentBusy.value = true
  try {
    await createComment(props.id, {
      nickname: commentForm.value.nickname.trim(),
      password: commentForm.value.password,
      content: commentForm.value.content.trim(),
    })
    commentForm.value = {
      nickname: commentForm.value.nickname,
      password: '',
      content: '',
    }
    await refreshPost()
    await nextTick()
    document.querySelector('.community-comments-list')?.lastElementChild?.scrollIntoView({
      behavior: 'smooth',
      block: 'nearest',
    })
    showNotice('댓글을 등록했습니다.')
  } catch (err) {
    commentError.value = err.message || '댓글을 등록하지 못했습니다.'
  } finally {
    commentBusy.value = false
  }
}

function startCommentEdit(comment) {
  editingCommentId.value = comment.id
  editCommentForm.value = {
    content: comment.content || '',
    password: '',
  }
  editCommentError.value = ''
}

function cancelCommentEdit() {
  editingCommentId.value = null
  editCommentForm.value = { content: '', password: '' }
  editCommentError.value = ''
}

async function submitCommentEdit(commentId) {
  if (!editCommentForm.value.content.trim()) {
    editCommentError.value = '댓글 내용을 입력해 주세요.'
    return
  }
  if (editCommentForm.value.password.trim().length < 4) {
    editCommentError.value = '댓글 작성 시 사용한 비밀번호를 입력해 주세요.'
    return
  }

  editCommentBusy.value = true
  editCommentError.value = ''
  try {
    await updateComment(props.id, commentId, {
      content: editCommentForm.value.content.trim(),
      password: editCommentForm.value.password,
    })
    cancelCommentEdit()
    await refreshPost()
    showNotice('댓글을 수정했습니다.')
  } catch (err) {
    editCommentError.value = err.message || '댓글을 수정하지 못했습니다.'
  } finally {
    editCommentBusy.value = false
  }
}

function openCommentDelete(comment) {
  selectedComment.value = comment
  commentDeleteError.value = ''
  commentDeleteModalOpen.value = true
}

async function confirmCommentDelete(password) {
  if (!selectedComment.value) return
  commentDeleteBusy.value = true
  commentDeleteError.value = ''
  try {
    await deleteComment(props.id, selectedComment.value.id, password)
    commentDeleteModalOpen.value = false
    selectedComment.value = null
    await refreshPost()
    showNotice('댓글을 삭제했습니다.')
  } catch (err) {
    commentDeleteError.value = err.message || '댓글을 삭제하지 못했습니다.'
  } finally {
    commentDeleteBusy.value = false
  }
}

function goToPostList() {
  const currentCategory = post.value?.category
  const category = currentCategory === '일반'
    ? '일반 게시판'
    : currentCategory

  router.push({
    name: 'community',
    query: category && category !== '전체'
      ? { category }
      : {},
  })
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
  const prompt = isFreeBoard.value
    ? `${post.value.title} 게시글의 내용을 요약해줘.`
    : `${post.value.title} 관련 화장실과 최근 리뷰를 요약해줘.`

  window.dispatchEvent(
    new CustomEvent('open-ai-chat', {
      detail: prompt,
    }),
  )
}

onMounted(() => {
  commentForm.value.nickname = getOrCreateCommentNickname()
  load()
})
</script>

<template>
  <main class="community-detail-page" @click="postManageOpen = false">
    <div class="page-container community-detail-shell">
      <button
        class="community-detail-back"
        type="button"
        aria-label="게시글 목록으로 돌아가기"
        @click="goToPostList"
      >
        <span class="community-detail-back__icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none">
            <path
              d="m15 18-6-6 6-6"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </span>
        <span>게시글 목록</span>
      </button>

      <p v-if="loading" class="state-message">게시글을 불러오는 중입니다.</p>
      <p v-else-if="error" class="state-message error">{{ error }}</p>

      <template v-else-if="post">
        <article class="community-detail-card">
          <header class="community-detail-meta">
            <div class="community-detail-meta__primary">
              <div class="community-post-card__badges">
                <span class="category">{{ categoryBadgeLabel }}</span>
                <span v-if="showTypeBadge" class="type">{{ typeBadgeLabel }}</span>
              </div>
              <span class="community-detail-meta__author">
                {{ post.nickname || '익명 사용자' }} · {{ createdAtLabel }}
              </span>
            </div>

            <div class="community-detail-top-actions" @click.stop>
              <button class="community-detail-ai" type="button" @click="openAiForPost">
                <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <path
                    d="M12 3.5 13.4 8l4.6 1.5-4.6 1.5L12 15.5 10.6 11 6 9.5 10.6 8 12 3.5Z"
                    stroke="currentColor"
                    stroke-width="1.7"
                    stroke-linejoin="round"
                  />
                  <path
                    d="m18.5 15 .8 2.2 2.2.8-2.2.8-.8 2.2-.8-2.2-2.2-.8 2.2-.8.8-2.2Z"
                    fill="currentColor"
                  />
                </svg>
                AI에게 물어보기
              </button>

              <div class="community-detail-more" :class="{ open: postManageOpen }">
                <button
                  class="community-detail-more__toggle"
                  type="button"
                  aria-label="게시글 관리 메뉴"
                  :aria-expanded="postManageOpen"
                  @click="postManageOpen = !postManageOpen"
                >
                  <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                    <circle cx="5" cy="12" r="1.8" />
                    <circle cx="12" cy="12" r="1.8" />
                    <circle cx="19" cy="12" r="1.8" />
                  </svg>
                </button>

                <div v-if="postManageOpen" class="community-detail-more__menu">
                  <button
                    type="button"
                    @click="postManageOpen = false; editModalOpen = true"
                  >
                    수정
                  </button>
                  <button
                    class="danger"
                    type="button"
                    @click="postManageOpen = false; deleteModalOpen = true"
                  >
                    삭제
                  </button>
                </div>
              </div>
            </div>
          </header>

          <h1 class="community-detail-title">{{ post.title }}</h1>

          <p class="community-detail-content">{{ post.content }}</p>

          <ImageCarousel
            v-if="images.length"
            :images="images"
            :alt="post.title"
            variant="detail"
          />

          <section
            v-if="hasRelatedContext"
            class="community-detail-context"
            aria-label="게시글 관련 화장실 정보"
          >
            <RouterLink
              v-if="post.restroomName && restroomReviewsRoute"
              class="community-detail-context__place"
              :to="restroomReviewsRoute"
              :aria-label="`${post.restroomName} 후기 목록 보기`"
            >
              <span class="community-detail-context__icon restroom" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none">
                  <path
                    d="M7 5h10v14H7V5Z"
                    stroke="currentColor"
                    stroke-width="1.8"
                    stroke-linejoin="round"
                  />
                  <path
                    d="M10 9h4M10 12h4M10 15h2"
                    stroke="currentColor"
                    stroke-width="1.8"
                    stroke-linecap="round"
                  />
                </svg>
              </span>
              <span class="community-detail-context__copy">
                <strong>{{ post.restroomName }}</strong>
                <small v-if="post.relatedPlace">{{ post.relatedPlace }} 주변</small>
              </span>
            </RouterLink>

            <div v-else-if="post.restroomName" class="community-detail-context__place">
              <span class="community-detail-context__icon restroom" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none">
                  <path
                    d="M7 5h10v14H7V5Z"
                    stroke="currentColor"
                    stroke-width="1.8"
                    stroke-linejoin="round"
                  />
                  <path
                    d="M10 9h4M10 12h4M10 15h2"
                    stroke="currentColor"
                    stroke-width="1.8"
                    stroke-linecap="round"
                  />
                </svg>
              </span>
              <span class="community-detail-context__copy">
                <strong>{{ post.restroomName }}</strong>
                <small v-if="post.relatedPlace">{{ post.relatedPlace }} 주변</small>
              </span>
            </div>

            <div v-else-if="post.relatedPlace" class="community-detail-context__place">
              <span class="community-detail-context__icon" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none">
                  <path
                    d="M12 21s7-6.1 7-12a7 7 0 1 0-14 0c0 5.9 7 12 7 12Z"
                    stroke="currentColor"
                    stroke-width="1.8"
                    stroke-linejoin="round"
                  />
                  <circle cx="12" cy="9" r="2.4" stroke="currentColor" stroke-width="1.8" />
                </svg>
              </span>
              <span class="community-detail-context__copy">
                <strong>{{ post.relatedPlace }}</strong>
              </span>
            </div>

            <span
              v-if="showRating"
              class="community-detail-rating"
              :class="ratingClass"
              :aria-label="`청결도 ${Number(post.rating).toFixed(1)}점`"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path
                  d="m12 2.8 2.8 5.7 6.3.9-4.6 4.4 1.1 6.2-5.6-3-5.6 3 1.1-6.2-4.6-4.4 6.3-.9L12 2.8Z"
                  fill="currentColor"
                />
              </svg>
              <span>청결도</span>
              <strong>{{ Number(post.rating).toFixed(1) }}</strong>
            </span>
          </section>

          <footer class="community-detail-actions">
            <div class="community-detail-actions__primary">
              <PostVoteControl
                :post-id="post.id"
                :score="post.recommendationCount || 0"
                :downvotes="post.dislikeCount || 0"
              />

              <span
                class="community-action-button community-action-button--static"
                aria-label="댓글 수"
              >
                <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <path
                    d="M5 5h14v11H9l-4 3V5Z"
                    stroke="currentColor"
                    stroke-width="1.8"
                    stroke-linejoin="round"
                  />
                </svg>
                댓글 {{ commentCount }}
              </span>

              <button class="community-action-button" type="button" @click="sharePost">
                <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <circle cx="18" cy="5" r="2.2" stroke="currentColor" stroke-width="1.8" />
                  <circle cx="6" cy="12" r="2.2" stroke="currentColor" stroke-width="1.8" />
                  <circle cx="18" cy="19" r="2.2" stroke="currentColor" stroke-width="1.8" />
                  <path
                    d="m8 11 8-5M8 13l8 5"
                    stroke="currentColor"
                    stroke-width="1.8"
                    stroke-linecap="round"
                  />
                </svg>
                공유
              </button>
            </div>

          </footer>
        </article>

        <section id="comments" class="community-comments-panel">
          <header class="community-comments-heading">
            <div>
              <h2>댓글 <span>{{ commentCount }}</span></h2>
              <p>이용 경험이나 추가 정보를 남겨보세요.</p>
            </div>
          </header>

          <form class="community-comment-form" @submit.prevent="submitComment">
            <div class="community-comment-form__topline">
              <div class="community-comment-form__identity">
                <span class="community-comment-form__avatar" aria-hidden="true">
                  <span>{{ commentForm.nickname.charAt(0) || '익' }}</span>
                </span>
                <div>
                  <strong>{{ commentForm.nickname }}</strong>
                  <small>자동 생성 닉네임</small>
                </div>
              </div>

              <label class="community-comment-form__password">
                <span class="sr-only">비밀번호</span>
                <input
                  v-model="commentForm.password"
                  type="password"
                  minlength="4"
                  maxlength="30"
                  autocomplete="new-password"
                  placeholder="비밀번호 4자 이상 입력"
                />
              </label>
            </div>

            <label class="community-comment-form__content">
              <span class="sr-only">댓글 내용</span>
              <textarea
                v-model="commentForm.content"
                maxlength="500"
                rows="4"
                placeholder="댓글을 입력하세요. 다른 이용자에게 도움이 되는 정보를 남겨주세요."
              />
            </label>

            <div class="community-comment-form__footer">
              <p
                v-if="commentError"
                class="community-comment-form__error"
                role="alert"
              >
                {{ commentError }}
              </p>
              <span v-else>{{ commentForm.content.length }}/500</span>
              <button type="submit" :disabled="commentSubmitDisabled">
                {{ commentBusy ? '등록 중...' : '댓글 등록' }}
              </button>
            </div>
          </form>

          <div v-if="comments.length" class="community-comments-list">
            <article v-for="comment in comments" :key="comment.id" class="community-comment-item">
              <span class="community-comment-item__avatar" aria-hidden="true">
                <span>{{ commentInitial(comment) }}</span>
              </span>

              <div class="community-comment-item__body">
                <div class="community-comment-item__header">
                  <div>
                    <strong>{{ comment.nickname || '익명 사용자' }}</strong>
                    <time>{{ commentTimeLabel(comment) }}</time>
                  </div>

                  <details class="community-comment-item__more">
                    <summary aria-label="댓글 관리 메뉴">
                      <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                        <circle cx="5" cy="12" r="1.7" />
                        <circle cx="12" cy="12" r="1.7" />
                        <circle cx="19" cy="12" r="1.7" />
                      </svg>
                    </summary>
                    <div>
                      <button type="button" @click="startCommentEdit(comment)">수정</button>
                      <button class="danger" type="button" @click="openCommentDelete(comment)">
                        삭제
                      </button>
                    </div>
                  </details>
                </div>

                <form
                  v-if="editingCommentId === comment.id"
                  class="community-comment-edit-form"
                  @submit.prevent="submitCommentEdit(comment.id)"
                >
                  <textarea
                    v-model="editCommentForm.content"
                    maxlength="500"
                    rows="3"
                    aria-label="수정할 댓글 내용"
                  />
                  <div class="community-comment-edit-form__footer">
                    <input
                      v-model="editCommentForm.password"
                      type="password"
                      minlength="4"
                      maxlength="30"
                      autocomplete="current-password"
                      placeholder="댓글 비밀번호"
                      aria-label="댓글 비밀번호"
                    />
                    <span v-if="editCommentError" role="alert">{{ editCommentError }}</span>
                    <button type="button" @click="cancelCommentEdit">취소</button>
                    <button class="primary" type="submit" :disabled="editCommentBusy">
                      {{ editCommentBusy ? '저장 중...' : '저장' }}
                    </button>
                  </div>
                </form>

                <p v-else>{{ comment.content }}</p>
              </div>
            </article>
          </div>

          <div v-else class="community-comments-empty">
            <strong>아직 등록된 댓글이 없습니다.</strong>
            <p>첫 댓글로 이용 경험이나 추가 정보를 남겨보세요.</p>
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

    <PasswordModal
      :open="commentDeleteModalOpen"
      title="댓글 삭제"
      :busy="commentDeleteBusy"
      :error="commentDeleteError"
      @close="commentDeleteModalOpen = false"
      @confirm="confirmCommentDelete"
    />

    <p v-if="notice" class="community-feed-toast" role="status">{{ notice }}</p>
  </main>
</template>
