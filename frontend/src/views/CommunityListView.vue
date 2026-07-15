<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import CommunityTabs from '../components/CommunityTabs.vue'
import CommunityFeedCard from '../components/CommunityFeedCard.vue'
import PaginationBar from '../components/PaginationBar.vue'
import { listPosts } from '../services/postApi'

const route = useRoute()
const router = useRouter()

const allowedCategories = ['전체', '관광지', '문화시설', '축제·공연', '쇼핑', '일반 게시판', '자유게시판']
const allowedSorts = ['recent', 'popular', 'comments']
const pageSize = 10

const category = ref('전체')
const keywordInput = ref('')
const appliedKeyword = ref('')
const sort = ref('recent')
const page = ref(1)
const posts = ref([])
const total = ref(0)
const loading = ref(false)
const error = ref('')
const notice = ref('')
let requestSequence = 0
let noticeTimer = null

function getCategoryLabel(value) {
  return value === '일반 게시판' || value === '일반'
    ? '일반'
    : value
}

const pageTitle = computed(() =>
  category.value === '전체' ? '커뮤니티' : getCategoryLabel(category.value),
)

const heroTitle = computed(() =>
  category.value === '전체' ? '커뮤니티' : `${getCategoryLabel(category.value)} 커뮤니티`,
)

const pageDescription = computed(() => {
  if (category.value === '전체') return '장소별 이용 후기와 현장 정보를 한곳에서 확인하세요.'
  if (category.value === '자유게시판') return '화장실 이용과 관련된 자유로운 이야기를 나눠보세요.'
  if (category.value === '일반 게시판' || category.value === '일반') return '관광 카테고리에 속하지 않는 화장실 후기와 제보를 확인하세요.'
  return `${getCategoryLabel(category.value)} 주변의 화장실 후기와 이용 정보를 확인하세요.`
})

const writeRoute = computed(() => ({
  name: 'post-create',
  query: category.value === '전체' ? {} : { category: category.value },
}))

const resultSummary = computed(() => {
  if (appliedKeyword.value) return `“${appliedKeyword.value}” 검색 결과 ${total.value}개`
  return `전체 ${total.value}개`
})

function cleanQuery(query) {
  return Object.fromEntries(
    Object.entries(query).filter(([, value]) => value !== undefined && value !== '' && value !== null),
  )
}

function replaceQuery(patch) {
  router.push({
    name: 'community',
    query: cleanQuery({
      ...route.query,
      ...patch,
    }),
  })
}

function changeCategory(nextCategory) {
  replaceQuery({
    category: nextCategory === '전체' ? undefined : nextCategory,
    page: undefined,
  })
}

function changeSort(nextSort) {
  replaceQuery({
    sort: nextSort === 'recent' ? undefined : nextSort,
    page: undefined,
  })
}

function submitSearch() {
  replaceQuery({
    keyword: keywordInput.value.trim() || undefined,
    page: undefined,
  })
}

function clearSearch() {
  keywordInput.value = ''
  replaceQuery({ keyword: undefined, page: undefined })
}

function changePage(nextPage) {
  replaceQuery({ page: nextPage > 1 ? nextPage : undefined })
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

async function sharePost(post) {
  const resolved = router.resolve({
    name: 'post-detail',
    params: { id: post.id },
  })
  const url = new URL(resolved.href, window.location.origin).href
  const shareData = {
    title: `${post.title} | 화장실록`,
    text: post.restroomName ? `${post.title}\n${post.restroomName}` : post.title,
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

async function loadPosts() {
  const sequence = ++requestSequence
  loading.value = true
  error.value = ''

  try {
    const result = await listPosts({
      category: category.value,
      keyword: appliedKeyword.value,
      sort: sort.value,
      page: page.value,
      size: pageSize,
    })

    if (sequence !== requestSequence) return

    posts.value = result.items
    total.value = result.total
  } catch (loadError) {
    if (sequence !== requestSequence) return
    error.value = loadError.message || '게시글을 불러오지 못했습니다.'
    posts.value = []
    total.value = 0
  } finally {
    if (sequence === requestSequence) loading.value = false
  }
}

watch(
  () => route.query,
  (query) => {
    const nextCategory = String(query.category || '전체')
    const nextSort = String(query.sort || 'recent')
    const nextKeyword = String(query.keyword || '')
    const nextPage = Math.max(1, Number(query.page || 1))

    category.value = allowedCategories.includes(nextCategory) ? nextCategory : '전체'
    sort.value = allowedSorts.includes(nextSort) ? nextSort : 'recent'
    appliedKeyword.value = nextKeyword
    keywordInput.value = nextKeyword
    page.value = Number.isFinite(nextPage) ? nextPage : 1

    loadPosts()
  },
  { immediate: true, deep: true },
)
</script>

<template>
  <main class="community-board-page">
    <section class="community-board-hero">
      <div class="page-container community-board-hero__inner">
        <div>
          <span>화장실록 커뮤니티</span>
          <h1>{{ heroTitle }}</h1>
          <p>{{ pageDescription }}</p>
        </div>
      </div>
    </section>

    <div class="page-container community-board-shell">
      <div class="community-board-layout">
        <aside class="community-board-sidebar" aria-label="커뮤니티 카테고리">
          <strong class="community-board-sidebar__title">게시판</strong>
          <CommunityTabs
            :model-value="category"
            variant="sidebar"
            @update:model-value="changeCategory"
          />
        </aside>

        <section class="community-board-main community-board-content">
          <section
            id="community-list-start"
            class="community-board-toolbar"
            aria-label="게시글 검색과 정렬"
          >
            <form class="community-board-search" @submit.prevent="submitSearch">
              <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <circle cx="11" cy="11" r="6.5" stroke="currentColor" stroke-width="1.8" />
                <path d="m16 16 4 4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
              </svg>

              <input
                v-model="keywordInput"
                type="search"
                placeholder="제목, 내용, 장소 또는 화장실명 검색"
                aria-label="커뮤니티 게시글 검색"
              />

              <button
                v-if="keywordInput"
                class="community-board-search__clear"
                type="button"
                aria-label="검색어 지우기"
                @click="clearSearch"
              >
                ×
              </button>

              <button class="community-board-search__submit" type="submit">
                검색
              </button>
            </form>

            <div class="community-board-toolbar__actions">
              <div class="community-board-sort" role="tablist" aria-label="게시글 정렬">
                <button
                  type="button"
                  role="tab"
                  :class="{ active: sort === 'recent' }"
                  :aria-selected="sort === 'recent'"
                  @click="changeSort('recent')"
                >
                  최신순
                </button>
                <button
                  type="button"
                  role="tab"
                  :class="{ active: sort === 'popular' }"
                  :aria-selected="sort === 'popular'"
                  @click="changeSort('popular')"
                >
                  인기순
                </button>
                <button
                  type="button"
                  role="tab"
                  :class="{ active: sort === 'comments' }"
                  :aria-selected="sort === 'comments'"
                  @click="changeSort('comments')"
                >
                  댓글순
                </button>
              </div>

              <RouterLink class="community-board-toolbar__write" :to="writeRoute">
                <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <path d="m14.5 5.5 4 4M4 20l3.8-.8L19.2 7.8a1.4 1.4 0 0 0 0-2l-1-1a1.4 1.4 0 0 0-2 0L4.8 16.2 4 20Z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
                글쓰기
              </RouterLink>
            </div>
          </section>

          <div class="community-board-summary">
            <strong>{{ resultSummary }}</strong>
            <span>한 페이지에 {{ pageSize }}개씩 표시</span>
          </div>

          <div
            v-if="loading"
            class="community-board-skeletons"
            aria-label="게시글을 불러오는 중"
          >
            <div
              v-for="number in 3"
              :key="number"
              class="community-board-skeleton"
            >
              <div class="skeleton-line short"></div>
              <div class="skeleton-line title"></div>
              <div class="skeleton-line"></div>
              <div class="skeleton-line medium"></div>
            </div>
          </div>

          <div v-else-if="error" class="community-board-empty error">
            <strong>게시글을 불러오지 못했습니다.</strong>
            <p>{{ error }}</p>
            <button type="button" @click="loadPosts">다시 시도</button>
          </div>

          <section
            v-else-if="posts.length"
            class="community-board-list"
            aria-label="게시글 목록"
          >
            <CommunityFeedCard
              v-for="post in posts"
              :key="post.id"
              :post="post"
              @share="sharePost"
            />
          </section>

          <div v-else class="community-board-empty">
            <span class="community-board-empty__icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none">
                <path d="M5 5h14v11H9l-4 3V5Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" />
              </svg>
            </span>
            <strong>조건에 맞는 게시글이 없습니다.</strong>
            <p>검색어를 바꾸거나 첫 글을 작성해보세요.</p>
            <RouterLink :to="writeRoute">글쓰기</RouterLink>
          </div>

          <PaginationBar
            v-if="!loading && !error && total > pageSize"
            :page="page"
            :size="pageSize"
            :total="total"
            @change="changePage"
          />
        </section>
      </div>
    </div>

    <p v-if="notice" class="community-feed-toast" role="status">{{ notice }}</p>
  </main>
</template>
