<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import CleanlinessRating from '../components/CleanlinessRating.vue'
import RestroomSelector from '../components/RestroomSelector.vue'
import ValidationModal from '../components/ValidationModal.vue'
import { createPost, getPost, updatePost } from '../services/postApi'
import { getRestroom } from '../services/locationApi'

const props = defineProps({ id: { type: String, default: '' } })
const route = useRoute()
const router = useRouter()
const isEdit = computed(() => Boolean(props.id))
const categoryOptions = [
  { value: '관광지', label: '관광지' },
  { value: '문화시설', label: '문화시설' },
  { value: '축제·공연', label: '축제·공연' },
  { value: '쇼핑', label: '쇼핑' },
  { value: '일반 게시판', label: '일반' },
  { value: '자유게시판', label: '자유게시판' },
]
const MAX_IMAGES = 5

const form = reactive({
  password: '',
  category: '',
  title: '',
  content: '',
  rating: 0,
})
const authorNickname = ref('')
const selectedRestroom = ref(null)
const selectedImageFiles = ref([])
const selectedImagePreviews = ref([])
const existingImageUrls = ref([])
const busy = ref(false)
const loadError = ref('')
const fieldErrors = reactive({})
const validationMessages = ref([])
const validationModalOpen = ref(false)
const submitted = ref(false)
const pristineSnapshot = ref('')
const fileInput = ref(null)

const titleCount = computed(() => form.title.length)
const contentCount = computed(() => form.content.length)
const isFreeBoard = computed(() => form.category === '자유게시판')
const editPasswordStorageKey = computed(() => (props.id ? `post-edit-password-${props.id}` : ''))
const totalImageCount = computed(
  () => existingImageUrls.value.length + selectedImageFiles.value.length,
)
const canAddImages = computed(() => totalImageCount.value < MAX_IMAGES)
const hasUnsavedChanges = computed(() => currentSnapshot() !== pristineSnapshot.value && !submitted.value)
const editorTitle = computed(() => {
  if (isEdit.value) return '리뷰 수정'
  if (selectedRestroom.value?.name) return `${selectedRestroom.value.name} 리뷰 쓰기`
  return '리뷰 쓰기'
})
const submitLabel = computed(() => {
  if (busy.value) return isEdit.value ? '수정 중…' : '등록 중…'
  return isEdit.value ? '수정 완료' : '리뷰 등록'
})

const nicknameAdjectives = [
  '상쾌한', '깨끗한', '푸른', '조용한', '밝은',
  '느긋한', '산뜻한', '반가운', '꼼꼼한', '다정한',
]
const nicknameNouns = [
  '여행자', '시민', '산책러', '탐험가', '방문객',
  '나들이객', '길잡이', '이용자', '동네친구', '관찰자',
]

function getOrCreateAnonymousNickname() {
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

function normalizeCategory(value) {
  const category = String(value || '')
  if (category === '일반') return '일반 게시판'
  return categoryOptions.some((option) => option.value === category) ? category : ''
}

function currentSnapshot() {
  return JSON.stringify({
    ...form,
    nickname: authorNickname.value,
    restroomId: selectedRestroom.value?.id || null,
    imageNames: selectedImageFiles.value.map((file) => file.name),
    existingImageUrls: existingImageUrls.value,
  })
}

function setPristine() {
  pristineSnapshot.value = currentSnapshot()
}

function clearErrors() {
  Object.keys(fieldErrors).forEach((key) => delete fieldErrors[key])
}

function validate() {
  clearErrors()
  const messages = []
  const add = (field, message) => {
    fieldErrors[field] = message
    messages.push(message)
  }

  if (!isEdit.value) {
    if (!form.password.trim()) add('password', '수정·삭제용 비밀번호를 입력해 주세요.')
    else if (form.password.length < 4) add('password', '비밀번호는 4자 이상 입력해 주세요.')
  }

  if (!form.category) add('category', '카테고리를 선택해 주세요.')
  if (!isFreeBoard.value && !selectedRestroom.value) add('restroom', '리뷰를 연결할 화장실을 선택해 주세요.')
  if (!isFreeBoard.value && !form.rating) add('rating', '청결도 별점을 선택해 주세요.')
  if (isEdit.value && !form.password) add('password', '상세 화면에서 비밀번호 확인 후 수정해 주세요.')

  if (!form.title.trim()) add('title', '제목을 입력해 주세요.')
  else if (form.title.trim().length < 2) add('title', '제목은 2자 이상 입력해 주세요.')

  if (!form.content.trim()) add('content', '내용을 입력해 주세요.')
  else if (form.content.trim().length < 5) add('content', '내용은 5자 이상 입력해 주세요.')

  validationMessages.value = messages
  return messages.length === 0
}

async function closeValidationModal() {
  validationModalOpen.value = false
  await nextTick()
  const firstField = Object.keys(fieldErrors)[0]
  document.querySelector(`[data-field="${firstField}"]`)?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  document.querySelector(`[data-field="${firstField}"] input, [data-field="${firstField}"] textarea, [data-field="${firstField}"] button`)?.focus()
}

function handleImageChange(event) {
  const files = Array.from(event.target.files || [])
  if (!files.length) return

  if (totalImageCount.value + files.length > MAX_IMAGES) {
    validationMessages.value = [`사진은 최대 ${MAX_IMAGES}장까지 첨부할 수 있습니다.`]
    validationModalOpen.value = true
    event.target.value = ''
    return
  }

  const allowed = ['image/jpeg', 'image/png', 'image/webp']
  const invalidType = files.find((file) => !allowed.includes(file.type))
  if (invalidType) {
    validationMessages.value = ['JPG, PNG, WEBP 형식의 이미지만 첨부할 수 있습니다.']
    validationModalOpen.value = true
    event.target.value = ''
    return
  }

  const oversized = files.find((file) => file.size > 5 * 1024 * 1024)
  if (oversized) {
    validationMessages.value = ['사진 한 장의 용량은 5MB 이하로 선택해 주세요.']
    validationModalOpen.value = true
    event.target.value = ''
    return
  }

  selectedImageFiles.value.push(...files)
  selectedImagePreviews.value.push(...files.map((file) => URL.createObjectURL(file)))
  event.target.value = ''
}

function revokePreviews() {
  selectedImagePreviews.value.forEach((preview) => {
    if (preview?.startsWith('blob:')) URL.revokeObjectURL(preview)
  })
}

function removeSelectedImage(index) {
  const preview = selectedImagePreviews.value[index]
  if (preview?.startsWith('blob:')) URL.revokeObjectURL(preview)
  selectedImageFiles.value.splice(index, 1)
  selectedImagePreviews.value.splice(index, 1)
}

function removeExistingImage(index) {
  existingImageUrls.value.splice(index, 1)
}

function moveArrayItem(list, fromIndex, toIndex) {
  if (toIndex < 0 || toIndex >= list.length) return
  const [item] = list.splice(fromIndex, 1)
  list.splice(toIndex, 0, item)
}

function moveExistingImage(index, direction) {
  moveArrayItem(existingImageUrls.value, index, index + direction)
}

function moveSelectedImage(index, direction) {
  const nextIndex = index + direction
  if (nextIndex < 0 || nextIndex >= selectedImageFiles.value.length) return
  moveArrayItem(selectedImageFiles.value, index, nextIndex)
  moveArrayItem(selectedImagePreviews.value, index, nextIndex)
}

async function loadPreselectedRestroom() {
  const restroomId = route.query.restroomId
  const restroomName = String(route.query.restroomName || '')
  if (!restroomId && !restroomName) return

  try {
    if (restroomId) selectedRestroom.value = await getRestroom(restroomId)
  } catch {
    selectedRestroom.value = { id: Number(restroomId) || null, name: restroomName, address: '' }
  }

  if (!selectedRestroom.value && restroomName) {
    selectedRestroom.value = { id: Number(restroomId) || null, name: restroomName, address: '' }
  }

  if (selectedRestroom.value && !form.title) form.title = `${selectedRestroom.value.name} 이용 후기`
}

async function loadForEdit() {
  if (!isEdit.value) return
  const verifiedPassword = sessionStorage.getItem(editPasswordStorageKey.value)
  if (!verifiedPassword) {
    loadError.value = '게시글 상세 화면에서 비밀번호를 확인한 뒤 수정할 수 있습니다.'
    return
  }

  try {
    const post = await getPost(props.id)
    Object.assign(form, {
      password: verifiedPassword,
      category: normalizeCategory(post.category),
      title: post.title || '',
      content: post.content || '',
      rating: Number(post.rating || 0),
    })
    authorNickname.value = post.nickname || authorNickname.value
    existingImageUrls.value = Array.isArray(post.imageUrls) && post.imageUrls.length
      ? post.imageUrls.filter(Boolean)
      : post.imageUrl
        ? [post.imageUrl]
        : []

    if (post.restroomId) {
      try {
        selectedRestroom.value = await getRestroom(post.restroomId)
      } catch {
        // 이름 fallback 사용
      }
    }

    if (!selectedRestroom.value && post.restroomName) {
      selectedRestroom.value = { id: post.restroomId || null, name: post.restroomName, address: '' }
    }
  } catch (error) {
    loadError.value = error.message || '게시글을 불러오지 못했습니다.'
  }
}

async function submit() {
  if (!validate()) {
    validationModalOpen.value = true
    return
  }

  busy.value = true
  try {
    const payload = {
      nickname: authorNickname.value,
      password: form.password,
      category: form.category,
      postType: isFreeBoard.value ? '자유게시판' : '화장실 리뷰',
      title: form.title.trim(),
      content: form.content.trim(),
      rating: isFreeBoard.value ? '' : Number(form.rating),
      restroomId: isFreeBoard.value ? '' : selectedRestroom.value.id,
      restroomName: isFreeBoard.value ? '' : selectedRestroom.value.name,
      relatedPlace: form.category,
      imageUrls: existingImageUrls.value,
      imageUrl: existingImageUrls.value[0] || '',
    }

    const saved = isEdit.value
      ? await updatePost(props.id, payload, selectedImageFiles.value)
      : await createPost(payload, selectedImageFiles.value)

    if (isEdit.value) sessionStorage.removeItem(editPasswordStorageKey.value)
    submitted.value = true
    router.push({ name: 'post-detail', params: { id: saved.id } })
  } catch (error) {
    validationMessages.value = [error.message || '게시글 저장 중 오류가 발생했습니다.']
    validationModalOpen.value = true
  } finally {
    busy.value = false
  }
}

function cancel() {
  if (hasUnsavedChanges.value && !window.confirm('작성 중인 내용이 사라집니다. 나가시겠습니까?')) return
  submitted.value = true
  router.back()
}

onBeforeRouteLeave(() => {
  if (!hasUnsavedChanges.value) return true
  return window.confirm('작성 중인 내용이 사라집니다. 페이지를 나가시겠습니까?')
})

watch(selectedRestroom, (value) => {
  if (value && !form.title.trim()) form.title = `${value.name} 이용 후기`
})

watch(() => form.category, (value) => {
  if (value === '자유게시판') {
    selectedRestroom.value = null
    form.rating = 0
  }
})

onMounted(async () => {
  authorNickname.value = getOrCreateAnonymousNickname()

  if (isEdit.value) await loadForEdit()
  else await loadPreselectedRestroom()

  const routeCategory = normalizeCategory(route.query.category)
  if (routeCategory) form.category = routeCategory

  await nextTick()
  setPristine()
})

onBeforeUnmount(revokePreviews)
</script>

<template>
  <main class="post-editor-page">
    <div class="post-editor-shell">
      <header class="post-editor-header">
        <button type="button" class="editor-back-button" aria-label="뒤로 가기" @click="cancel">
          <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path
              d="m14.5 5-7 7 7 7"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </button>

        <div>
          <span v-if="isEdit">작성한 리뷰를 수정합니다</span>
          <h1>{{ editorTitle }}</h1>
        </div>
      </header>

      <p v-if="loadError" class="editor-load-error">{{ loadError }}</p>

      <form v-else class="post-editor-form" novalidate @submit.prevent="submit">
        <section class="editor-section editor-section--author">
          <div class="editor-section-heading">
            <div>
              <h2>작성자 정보</h2>
              <p>익명 닉네임과 수정·삭제에 사용할 비밀번호를 확인합니다.</p>
            </div>
          </div>

          <div class="editor-author-grid">
            <div class="editor-author-card editor-author-identity" aria-label="자동 생성 작성자 닉네임">
              <div class="editor-author-card__label">작성자</div>
              <div class="editor-author-card__content">
                <span class="editor-author-avatar" aria-hidden="true">{{ authorNickname.slice(0, 1) }}</span>
                <div class="editor-author-copy">
                  <strong>{{ authorNickname }}</strong>
                  <small>자동 생성 닉네임</small>
                </div>
              </div>
            </div>

            <label
              v-if="!isEdit"
              class="editor-author-card editor-password-field"
              :class="{ 'has-field-error': fieldErrors.password }"
              data-field="password"
            >
              <span class="editor-author-card__label">
                수정·삭제 비밀번호
                <em class="required-mark">필수</em>
              </span>
              <input
                v-model="form.password"
                type="password"
                maxlength="30"
                placeholder="4자 이상 입력하세요"
                autocomplete="new-password"
              />
              <b v-if="fieldErrors.password" class="field-error">{{ fieldErrors.password }}</b>
            </label>

            <div v-else class="editor-author-card editor-password-verified">
              <span class="editor-author-card__label">수정 비밀번호</span>
              <div class="editor-password-verified__content">
                <strong>확인 완료</strong>
                <small>상세 화면에서 확인한 비밀번호가 적용됩니다.</small>
              </div>
            </div>
          </div>
        </section>

        <section class="editor-section">
          <div class="editor-section-heading">
            <div>
              <h2>리뷰 설정</h2>
            </div>
          </div>

          <div class="category-field" :class="{ 'has-field-error': fieldErrors.category }" data-field="category">
            <div class="form-label-row">
              <label>카테고리 <span class="required-mark">필수</span></label>
            </div>

            <div class="editor-category-tabs">
              <button
                v-for="category in categoryOptions"
                :key="category.value"
                type="button"
                :class="{ active: form.category === category.value }"
                :aria-pressed="form.category === category.value"
                @click="form.category = category.value"
              >
                {{ category.label }}
              </button>
            </div>
            <p v-if="fieldErrors.category" class="field-error">{{ fieldErrors.category }}</p>
          </div>

          <RestroomSelector
            v-if="!isFreeBoard"
            v-model="selectedRestroom"
            :error="fieldErrors.restroom"
          />

          <div
            v-if="!isFreeBoard"
            class="rating-field"
            :class="{ 'has-field-error': fieldErrors.rating }"
            data-field="rating"
          >
            <div class="form-label-row">
              <label>청결도 <span class="required-mark">필수</span></label>
            </div>
            <CleanlinessRating v-model="form.rating" />
            <p v-if="fieldErrors.rating" class="field-error">{{ fieldErrors.rating }}</p>
          </div>
        </section>

        <section class="editor-section">
          <div class="editor-section-heading">
            <div>
              <h2>리뷰 작성</h2>
              <p>청결 상태와 이용 경험을 구체적으로 남겨 주세요.</p>
            </div>
          </div>

          <label class="editor-text-field" :class="{ 'has-field-error': fieldErrors.title }" data-field="title">
            <div class="form-label-row">
              <span>제목 <span class="required-mark">필수</span></span>
              <small>{{ titleCount }}/100</small>
            </div>
            <input v-model="form.title" maxlength="100" placeholder="제목을 입력해 주세요" />
            <b v-if="fieldErrors.title" class="field-error">{{ fieldErrors.title }}</b>
          </label>

          <label class="editor-text-field" :class="{ 'has-field-error': fieldErrors.content }" data-field="content">
            <div class="form-label-row">
              <span>내용 <span class="required-mark">필수</span></span>
              <small>{{ contentCount }}/3000</small>
            </div>
            <textarea
              v-model="form.content"
              maxlength="3000"
              rows="8"
              placeholder="청결 상태, 혼잡도, 휴지·비누 비치 여부, 접근성처럼 다른 이용자에게 도움이 되는 내용을 적어 주세요."
            />
            <b v-if="fieldErrors.content" class="field-error">{{ fieldErrors.content }}</b>
          </label>
        </section>

        <section class="editor-section editor-section--photos">
          <div class="editor-section-heading">
            <div>
              <h2>사진 첨부 <span class="optional-mark">선택</span></h2>
              <p>JPG, PNG, WEBP · 장당 최대 5MB · 최대 5장</p>
            </div>
          </div>

          <div class="image-upload-zone image-upload-zone--multiple">
            <input
              ref="fileInput"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              multiple
              @change="handleImageChange"
            />

            <button v-if="canAddImages" type="button" @click="fileInput?.click()">
              <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path d="M4 7h4l1.3-2h5.4L16 7h4v12H4V7Z" stroke="currentColor" stroke-width="1.8" />
                <circle cx="12" cy="13" r="3" stroke="currentColor" stroke-width="1.8" />
              </svg>
              <strong>사진 추가</strong>
              <span>{{ totalImageCount }}/5 · 여러 장을 한 번에 선택할 수 있습니다.</span>
            </button>

            <div v-if="totalImageCount" class="image-upload-summary">
              <strong>{{ totalImageCount }}장 선택됨</strong>
              <span>첫 번째 사진이 대표 이미지로 사용됩니다.</span>
            </div>

            <div v-if="totalImageCount" class="image-preview-grid">
              <article
                v-for="(url, index) in existingImageUrls"
                :key="`existing-${url}-${index}`"
                class="image-preview-tile"
              >
                <img :src="url" :alt="`기존 첨부 이미지 ${index + 1}`" />
                <em v-if="index === 0" class="image-cover-badge">대표 사진</em>
                <span>기존 이미지</span>
                <div class="image-preview-actions">
                  <button
                    type="button"
                    aria-label="이미지를 앞으로 이동"
                    :disabled="index === 0"
                    @click="moveExistingImage(index, -1)"
                  >←</button>
                  <button
                    type="button"
                    aria-label="이미지를 뒤로 이동"
                    :disabled="index === existingImageUrls.length - 1"
                    @click="moveExistingImage(index, 1)"
                  >→</button>
                  <button type="button" class="danger" aria-label="기존 이미지 삭제" @click="removeExistingImage(index)">삭제</button>
                </div>
              </article>

              <article
                v-for="(preview, index) in selectedImagePreviews"
                :key="`selected-${preview}`"
                class="image-preview-tile"
              >
                <img :src="preview" :alt="`새 첨부 이미지 ${index + 1}`" />
                <em
                  v-if="!existingImageUrls.length && index === 0"
                  class="image-cover-badge"
                >대표 사진</em>
                <span>{{ selectedImageFiles[index]?.name }}</span>
                <div class="image-preview-actions">
                  <button
                    type="button"
                    aria-label="이미지를 앞으로 이동"
                    :disabled="index === 0"
                    @click="moveSelectedImage(index, -1)"
                  >←</button>
                  <button
                    type="button"
                    aria-label="이미지를 뒤로 이동"
                    :disabled="index === selectedImageFiles.length - 1"
                    @click="moveSelectedImage(index, 1)"
                  >→</button>
                  <button type="button" class="danger" aria-label="선택 이미지 삭제" @click="removeSelectedImage(index)">삭제</button>
                </div>
              </article>
            </div>
          </div>
        </section>

        <footer class="post-editor-actions">
          <button type="button" class="editor-cancel-button" @click="cancel">취소</button>
          <button type="submit" class="editor-submit-button" :disabled="busy">
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path
                d="m14.5 5.5 4 4M4 20l3.8-.8L19.2 7.8a1.4 1.4 0 0 0 0-2l-1-1a1.4 1.4 0 0 0-2 0L4.8 16.2 4 20Z"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
            <span>{{ submitLabel }}</span>
          </button>
        </footer>
      </form>
    </div>

    <ValidationModal
      :open="validationModalOpen"
      :messages="validationMessages"
      @close="closeValidationModal"
    />
  </main>
</template>
