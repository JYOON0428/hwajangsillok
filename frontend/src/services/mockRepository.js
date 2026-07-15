import { initialPosts, restrooms, restroomReviews } from '../data/mockData'

const POST_KEY = 'hwajangsillok.posts.community-v2'

function clone(value) {
  return typeof structuredClone === 'function'
    ? structuredClone(value)
    : JSON.parse(JSON.stringify(value))
}

function wait(ms = 120) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function readPosts() {
  const stored = localStorage.getItem(POST_KEY)
  if (!stored) {
    localStorage.setItem(POST_KEY, JSON.stringify(initialPosts))
    return clone(initialPosts)
  }
  return JSON.parse(stored)
}

function savePosts(posts) {
  localStorage.setItem(POST_KEY, JSON.stringify(posts))
}

export async function listMockPosts({
  category = '전체',
  keyword = '',
  sort = 'recent',
  page = 1,
  size = 10,
} = {}) {
  await wait()
  let items = readPosts()

  if (category !== '전체') {
    items = items.filter((post) => post.category === category)
  }

  if (keyword.trim()) {
    const query = keyword.trim().toLowerCase()
    items = items.filter((post) => {
      const searchTarget = [
        post.title,
        post.content,
        post.relatedPlace,
        post.restroomName,
        post.nickname,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()

      return searchTarget.includes(query)
    })
  }

  const sorters = {
    recent: (a, b) => new Date(b.createdAt) - new Date(a.createdAt),
    popular: (a, b) =>
      (b.recommendationCount || 0) - (a.recommendationCount || 0)
      || (b.commentCount || 0) - (a.commentCount || 0)
      || new Date(b.createdAt) - new Date(a.createdAt),
    comments: (a, b) =>
      (b.commentCount || 0) - (a.commentCount || 0)
      || (b.recommendationCount || 0) - (a.recommendationCount || 0)
      || new Date(b.createdAt) - new Date(a.createdAt),
  }

  items = items.slice().sort(sorters[sort] || sorters.recent)

  const start = (page - 1) * size
  return {
    items: items.slice(start, start + size),
    total: items.length,
    page,
    size,
  }
}

export async function getMockPost(id) {
  await wait()
  const post = readPosts().find((item) => item.id === Number(id))
  if (!post) throw new Error('게시글을 찾을 수 없습니다.')
  return post
}

export async function createMockPost(payload) {
  await wait()
  const posts = readPosts()
  const id = posts.length ? Math.max(...posts.map((post) => post.id)) + 1 : 1
  const post = {
    id,
    recommendationCount: 0,
    dislikeCount: 0,
    commentCount: 0,
    commentPreview: [],
    comments: [],
    createdAt: new Date().toISOString(),
    imageUrl: '',
    imageUrls: [],
    rating: payload.rating ?? null,
    ...payload,
  }
  if (post.imageUrl && (!Array.isArray(post.imageUrls) || !post.imageUrls.length)) post.imageUrls = [post.imageUrl]
  posts.push(post)
  savePosts(posts)
  return post
}

export async function updateMockPost(id, payload) {
  await wait()
  const posts = readPosts()
  const index = posts.findIndex((item) => item.id === Number(id))
  if (index < 0) throw new Error('게시글을 찾을 수 없습니다.')
  if (posts[index].password !== payload.password) throw new Error('비밀번호가 일치하지 않습니다.')
  const nextPayload = { ...payload }
  if (nextPayload.imageUrl && (!Array.isArray(nextPayload.imageUrls) || !nextPayload.imageUrls.length)) nextPayload.imageUrls = [nextPayload.imageUrl]
  posts[index] = { ...posts[index], ...nextPayload, updatedAt: new Date().toISOString() }
  savePosts(posts)
  return posts[index]
}

export async function deleteMockPost(id, password) {
  await wait()
  const posts = readPosts()
  const post = posts.find((item) => item.id === Number(id))
  if (!post) throw new Error('게시글을 찾을 수 없습니다.')
  if (post.password !== password) throw new Error('비밀번호가 일치하지 않습니다.')
  savePosts(posts.filter((item) => item.id !== Number(id)))
  return { success: true }
}


function syncCommentSummary(post) {
  const comments = Array.isArray(post.comments) ? post.comments : []
  post.commentCount = comments.length
  post.commentPreview = comments.slice(0, 2).map((comment) => {
    const { password, ...preview } = comment
    return preview
  })
}

function findPostIndex(posts, postId) {
  const index = posts.findIndex((item) => item.id === Number(postId))
  if (index < 0) throw new Error('게시글을 찾을 수 없습니다.')
  return index
}

function findComment(post, commentId) {
  const comments = Array.isArray(post.comments) ? post.comments : []
  const index = comments.findIndex((item) => item.id === Number(commentId))
  if (index < 0) throw new Error('댓글을 찾을 수 없습니다.')
  return { comments, index, comment: comments[index] }
}

export async function createMockComment(postId, payload) {
  await wait()
  const nickname = String(payload.nickname || '').trim()
  const password = String(payload.password || '')
  const content = String(payload.content || '').trim()

  if (!nickname) throw new Error('닉네임을 입력해 주세요.')
  if (password.length < 4) throw new Error('비밀번호를 4자 이상 입력해 주세요.')
  if (!content) throw new Error('댓글 내용을 입력해 주세요.')

  const posts = readPosts()
  const postIndex = findPostIndex(posts, postId)
  const allCommentIds = posts.flatMap((post) =>
    Array.isArray(post.comments) ? post.comments.map((comment) => Number(comment.id) || 0) : [],
  )
  const id = allCommentIds.length ? Math.max(...allCommentIds) + 1 : 1
  const comment = {
    id,
    nickname,
    password,
    content,
    createdAt: new Date().toISOString(),
  }

  const comments = Array.isArray(posts[postIndex].comments)
    ? posts[postIndex].comments
    : []
  posts[postIndex].comments = [comment, ...comments]
  syncCommentSummary(posts[postIndex])
  savePosts(posts)

  const { password: _, ...publicComment } = comment
  return clone(publicComment)
}

export async function updateMockComment(postId, commentId, payload) {
  await wait()
  const content = String(payload.content || '').trim()
  const password = String(payload.password || '')
  if (!content) throw new Error('댓글 내용을 입력해 주세요.')

  const posts = readPosts()
  const postIndex = findPostIndex(posts, postId)
  const { comments, index, comment } = findComment(posts[postIndex], commentId)
  const storedPassword = comment.password || '1234'
  if (storedPassword !== password) throw new Error('비밀번호가 일치하지 않습니다.')

  comments[index] = {
    ...comment,
    content,
    updatedAt: new Date().toISOString(),
  }
  posts[postIndex].comments = comments
  syncCommentSummary(posts[postIndex])
  savePosts(posts)

  const { password: _, ...publicComment } = comments[index]
  return clone(publicComment)
}

export async function deleteMockComment(postId, commentId, password) {
  await wait()
  const posts = readPosts()
  const postIndex = findPostIndex(posts, postId)
  const { comments, index, comment } = findComment(posts[postIndex], commentId)
  const storedPassword = comment.password || '1234'
  if (storedPassword !== password) throw new Error('비밀번호가 일치하지 않습니다.')

  comments.splice(index, 1)
  posts[postIndex].comments = comments
  syncCommentSummary(posts[postIndex])
  savePosts(posts)
  return { success: true }
}

export async function searchMockRestrooms({
  keyword = '',
  radius = 1000,
  sort = 'distance',
  openNow = false,
  diaperTable = false,
  accessible = false,
  emergencyBell = false,
  recentReview = false,
} = {}) {
  await wait()
  const query = keyword.trim().toLowerCase()
  let items = restrooms.filter((item) => {
    const haystack = `${item.name} ${item.address}`.toLowerCase()
    const matchesKeyword = !query || haystack.includes(query) || query.includes('화장실')
    const matchesRadius = item.distanceMeters <= Number(radius || 1000)
    const matchesOpen = !openNow || item.openNow
    const matchesDiaper = !diaperTable || item.facilities.diaperTable
    const matchesAccessible = !accessible || item.facilities.accessible
    const matchesBell = !emergencyBell || item.facilities.emergencyBell
    const matchesRecent = !recentReview || Boolean(item.latestReviewAt)
    return matchesKeyword && matchesRadius && matchesOpen && matchesDiaper && matchesAccessible && matchesBell && matchesRecent
  })

  const sorters = {
    distance: (a, b) => a.distanceMeters - b.distanceMeters,
    cleanliness: (a, b) => (b.rating ?? -1) - (a.rating ?? -1),
    reviews: (a, b) => b.reviewCount - a.reviewCount,
  }
  items = items.slice().sort(sorters[sort] || sorters.distance)
  return clone(items)
}

export async function getMockRestroom(restroomId) {
  await wait()
  const restroom = restrooms.find((item) => item.id === Number(restroomId))
  if (!restroom) throw new Error('화장실 정보를 찾을 수 없습니다.')
  return clone(restroom)
}

export async function getMockRestroomReviews(restroomId, { sort = 'recent' } = {}) {
  await wait()
  const items = clone(restroomReviews[Number(restroomId)] || [])
  const sorters = {
    recent: (a, b) => new Date(b.createdAt) - new Date(a.createdAt),
    cleanlinessHigh: (a, b) => b.cleanliness - a.cleanliness,
    cleanlinessLow: (a, b) => a.cleanliness - b.cleanliness,
    comments: (a, b) => b.commentCount - a.commentCount,
  }
  return items.sort(sorters[sort] || sorters.recent)
}

export async function mockChat({ message }) {
  await wait(350)
  return {
    answer: '조건과 최근 리뷰를 기준으로 화장실을 찾았습니다.',
    locations: restrooms.slice(0, 2),
    related_posts: [],
    warnings: ['최근 리뷰와 현장 상황은 실제 이용 시점과 다를 수 있습니다.'],
    echo: message,
  }
}
