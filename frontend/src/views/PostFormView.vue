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
const categories = ['관광지', '문화시설', '축제·공연', '쇼핑']
const MAX_IMAGES = 5

const form = reactive({
  nickname: '',
  password: '',
  category: '',
  title: '',
  content: '',
  rating: 0,
})
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
const totalImageCount = computed(
  () => existingImageUrls.value.length + selectedImageFiles.value.length,
)
const canAddImages = computed(() => totalImageCount.value < MAX_IMAGES)
const hasUnsavedChanges = computed(() => currentSnapshot() !== pristineSnapshot.value && !submitted.value)

function currentSnapshot() {
  return JSON.stringify({
    ...form,
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

  if (!form.nickname.trim()) add('nickname', '닉네임을 입력해 주세요.')
  else if (form.nickname.trim().length < 2) add('nickname', '닉네임은 2자 이상 입력해 주세요.')

  if (!form.password.trim()) add('password', '수정·삭제용 비밀번호를 입력해 주세요.')
  else if (form.password.length < 4) add('password', '비밀번호는 4자 이상 입력해 주세요.')

  if (!form.category) add('category', '카테고리를 선택해 주세요.')
  if (!selectedRestroom.value) add('restroom', '리뷰를 연결할 화장실을 선택해 주세요.')
  if (!form.rating) add('rating', '청결도 별점을 선택해 주세요.')

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
  try {
    const post = await getPost(props.id)
    Object.assign(form, {
      nickname: post.nickname || '',
      password: '',
      category: post.category || '',
      title: post.title || '',
      content: post.content || '',
      rating: Number(post.rating || 0),
    })
    existingImageUrls.value = Array.isArray(post.imageUrls) && post.imageUrls.length
      ? post.imageUrls.filter(Boolean)
      : post.imageUrl
        ? [post.imageUrl]
        : []
    if (post.restroomId) {
      try { selectedRestroom.value = await getRestroom(post.restroomId) } catch { /* 이름 fallback 사용 */ }
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
      nickname: form.nickname.trim(),
      password: form.password,
      category: form.category,
      postType: '화장실 리뷰',
      title: form.title.trim(),
      content: form.content.trim(),
      rating: Number(form.rating),
      restroomId: selectedRestroom.value.id,
      restroomName: selectedRestroom.value.name,
      relatedPlace: form.category,
      imageUrls: existingImageUrls.value,
      imageUrl: existingImageUrls.value[0] || '',
    }
    const saved = isEdit.value
      ? await updatePost(props.id, payload, selectedImageFiles.value)
      : await createPost(payload, selectedImageFiles.value)
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

onMounted(async () => {
  if (isEdit.value) await loadForEdit()
  else await loadPreselectedRestroom()
  if (route.query.category && categories.includes(String(route.query.category))) {
    form.category = String(route.query.category)
  }
  await nextTick()
  setPristine()
})
onBeforeUnmount(revokePreviews)
</script>

<template>
  <main class="post-editor-page">
    <div class="post-editor-shell">
      <header class="post-editor-header">
        <button type="button" class="editor-back-button" aria-label="뒤로 가기" @click="cancel">←</button>
        <div>
          <span>화장실록 커뮤니티</span>
          <h1>{{ isEdit ? '게시글 수정' : '새 글 작성' }}</h1>
        </div>
      </header>

      <p v-if="loadError" class="editor-load-error">{{ loadError }}</p>

      <form v-else class="post-editor-form" novalidate @submit.prevent="submit">
        <section class="editor-section credentials-section">
          <div class="editor-section-heading">
            <div><span>01</span><h2>작성자 정보</h2></div>
            <p>회원가입 없이 사용하며, 비밀번호는 수정·삭제할 때만 사용합니다.</p>
          </div>
          <div class="credential-grid">
            <label :class="{ 'has-field-error': fieldErrors.nickname }" data-field="nickname">
              <span>닉네임 <em>필수</em></span>
              <input v-model="form.nickname" maxlength="20" placeholder="표시할 닉네임을 입력하세요" autocomplete="nickname" />
              <small>2~20자</small>
              <b v-if="fieldErrors.nickname" class="field-error">{{ fieldErrors.nickname }}</b>
            </label>
            <label :class="{ 'has-field-error': fieldErrors.password }" data-field="password">
              <span>수정용 비밀번호 <em>필수</em></span>
              <input v-model="form.password" type="password" maxlength="30" placeholder="4자 이상 입력하세요" autocomplete="new-password" />
              <small>수정·삭제 시 다시 입력합니다.</small>
              <b v-if="fieldErrors.password" class="field-error">{{ fieldErrors.password }}</b>
            </label>
          </div>
        </section>

        <section class="editor-section">
          <div class="editor-section-heading">
            <div><span>02</span><h2>리뷰 대상</h2></div>
            <p>관광 카테고리와 실제 이용한 화장실을 연결합니다.</p>
          </div>

          <div class="category-field" :class="{ 'has-field-error': fieldErrors.category }" data-field="category">
            <div class="form-label-row"><label>카테고리 <span class="required-mark">필수</span></label></div>
            <div class="editor-category-tabs">
              <button
                v-for="category in categories"
                :key="category"
                type="button"
                :class="{ active: form.category === category }"
                @click="form.category = category"
              >{{ category }}</button>
            </div>
            <p v-if="fieldErrors.category" class="field-error">{{ fieldErrors.category }}</p>
          </div>

          <RestroomSelector v-model="selectedRestroom" :error="fieldErrors.restroom" />

          <div class="rating-field" :class="{ 'has-field-error': fieldErrors.rating }" data-field="rating">
            <div class="form-label-row">
              <label>청결도 <span class="required-mark">필수</span></label>
              <span>평균값은 지도 핀 색상에 반영됩니다.</span>
            </div>
            <CleanlinessRating v-model="form.rating" />
            <p v-if="fieldErrors.rating" class="field-error">{{ fieldErrors.rating }}</p>
          </div>
        </section>

        <section class="editor-section">
          <div class="editor-section-heading">
            <div><span>03</span><h2>후기 작성</h2></div>
            <p>실제 이용 경험을 구체적으로 작성해 주세요.</p>
          </div>

          <label class="editor-text-field" :class="{ 'has-field-error': fieldErrors.title }" data-field="title">
            <div class="form-label-row"><span>제목 <span class="required-mark">필수</span></span><small>{{ titleCount }}/100</small></div>
            <input v-model="form.title" maxlength="100" placeholder="제목을 입력해 주세요" />
            <b v-if="fieldErrors.title" class="field-error">{{ fieldErrors.title }}</b>
          </label>

          <label class="editor-text-field" :class="{ 'has-field-error': fieldErrors.content }" data-field="content">
            <div class="form-label-row"><span>내용 <span class="required-mark">필수</span></span><small>{{ contentCount }}/3000</small></div>
            <textarea
              v-model="form.content"
              maxlength="3000"
              rows="12"
              placeholder="청결 상태, 혼잡도, 휴지·비누 비치 여부, 접근성처럼 다른 이용자에게 도움이 되는 내용을 적어 주세요."
            />
            <b v-if="fieldErrors.content" class="field-error">{{ fieldErrors.content }}</b>
          </label>
        </section>

        <section class="editor-section">
          <div class="editor-section-heading">
            <div><span>04</span><h2>사진 첨부</h2></div>
            <p>선택 항목 · JPG, PNG, WEBP · 장당 최대 5MB · 최대 5장</p>
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
              <svg viewBox="0 0 24 24" fill="none"><path d="M4 7h4l1.3-2h5.4L16 7h4v12H4V7Z" stroke="currentColor" stroke-width="1.8"/><circle cx="12" cy="13" r="3" stroke="currentColor" stroke-width="1.8"/></svg>
              <strong>사진 선택</strong>
              <span>{{ totalImageCount }}/5 · 여러 장을 한 번에 선택할 수 있습니다.</span>
            </button>

            <div v-if="totalImageCount" class="image-preview-grid">
              <article
                v-for="(url, index) in existingImageUrls"
                :key="`existing-${url}-${index}`"
                class="image-preview-tile"
              >
                <img :src="url" :alt="`기존 첨부 이미지 ${index + 1}`" />
                <span>기존 이미지</span>
                <button type="button" aria-label="기존 이미지 삭제" @click="removeExistingImage(index)">×</button>
              </article>

              <article
                v-for="(preview, index) in selectedImagePreviews"
                :key="`selected-${preview}`"
                class="image-preview-tile"
              >
                <img :src="preview" :alt="`새 첨부 이미지 ${index + 1}`" />
                <span>{{ selectedImageFiles[index]?.name }}</span>
                <button type="button" aria-label="선택 이미지 삭제" @click="removeSelectedImage(index)">×</button>
              </article>
            </div>
          </div>
        </section>

        <footer class="post-editor-actions">
          <button type="button" class="editor-cancel-button" @click="cancel">취소</button>
          <button type="submit" class="editor-submit-button" :disabled="busy">
            {{ busy ? '등록 중…' : isEdit ? '수정 완료' : '화장실록에 등록' }}
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
