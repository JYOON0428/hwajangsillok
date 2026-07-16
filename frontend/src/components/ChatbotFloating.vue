<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { sendChat } from '../services/chatApi'

const router = useRouter()

const open = ref(false)
const input = ref('')
const loading = ref(false)
const error = ref('')

const messages = ref([
  {
    role: 'assistant',
    content: '안녕하세요! 편하게 대화하거나, 찾는 장소와 필요한 시설을 알려주세요.',
    locations: [],
    warnings: [],
  },
])

function openFromEvent(event) {
  open.value = true
  input.value = String(event?.detail || '').trim()

  if (input.value) {
    submit()
  }
}

function getLocationId(location) {
  const id = Number(
    location?.toiletId ??
      location?.toilet_id ??
      location?.locationId ??
      location?.location_id ??
      location?.id,
  )

  return Number.isFinite(id) && id > 0 ? id : null
}

function getLocationKey(location, index) {
  return (
    getLocationId(location) ??
    `${location?.name || 'location'}-${location?.distanceMeters ?? index}`
  )
}

function getReviewPreview(location) {
  const snippets = location?.reviewSnippets

  if (Array.isArray(snippets) && snippets.length > 0) {
    return snippets[0]?.content || ''
  }

  return location?.latestReview || ''
}

function openLocation(location) {
  const locationId = getLocationId(location)

  if (!locationId) {
    error.value = '화장실 상세 정보를 확인할 수 없습니다.'
    return
  }

  error.value = ''
  open.value = false

  router.push({
    name: 'restroom-reviews',
    params: {
      id: String(locationId),
    },
  })
}

async function submit() {
  const message = input.value.trim()

  if (!message || loading.value) {
    return
  }

  /*
   * 현재 질문을 messages에 추가하기 전의 대화만 history로 전달합니다.
   *
   * 백엔드에는 현재 질문이 message 필드로 별도 전달되므로,
   * 현재 질문을 history에도 넣으면 같은 질문이 두 번 전달됩니다.
   */
  const history = messages.value.map(({ role, content }) => ({
    role,
    content,
  }))

  messages.value.push({
    role: 'user',
    content: message,
    locations: [],
    warnings: [],
  })

  input.value = ''
  loading.value = true
  error.value = ''

  try {
    const response = await sendChat({
      message,
      history,
      location_id: null,
    })

    messages.value.push({
      role: 'assistant',

      content:
        typeof response?.answer === 'string' && response.answer.trim()
          ? response.answer.trim()
          : '답변을 불러오지 못했어요. 잠시 후 다시 시도해 주세요.',

      locations: Array.isArray(response?.locations)
        ? response.locations
        : [],

      warnings: Array.isArray(response?.warnings)
        ? response.warnings
        : [],
    })
  } catch (err) {
    const errorMessage =
      err instanceof Error && err.message
        ? err.message
        : '챗봇 요청 중 오류가 발생했습니다.'

    error.value = errorMessage
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  window.addEventListener('open-ai-chat', openFromEvent)
})

onBeforeUnmount(() => {
  window.removeEventListener('open-ai-chat', openFromEvent)
})
</script>

<template>
  <!-- 우측 하단 챗봇 열기 버튼 -->
  <button
    class="chat-fab"
    type="button"
    aria-label="AI 챗봇 열기"
    @click="open = !open"
  >
    <svg
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
    >
      <path
        d="M6 18.5 3.5 21v-5A8 8 0 1 1 7 19.4"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      />

      <path
        d="M8 11h.01M12 11h.01M16 11h.01"
        stroke="currentColor"
        stroke-width="2.5"
        stroke-linecap="round"
      />
    </svg>
  </button>

  <aside
    v-if="open"
    class="chat-window"
    aria-label="화장실록 AI 챗봇"
  >
    <!-- master에서 반영된 새 헤더 디자인 -->
    <header class="chat-window__header">
      <div class="chat-window__brand">
        <span
          class="chat-window__brand-icon"
          aria-hidden="true"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
          >
            <path
              d="M6 18.5 3.5 21v-5A8 8 0 1 1 7 19.4"
              stroke="currentColor"
              stroke-width="1.9"
              stroke-linecap="round"
              stroke-linejoin="round"
            />

            <path
              d="M8 11h.01M12 11h.01M16 11h.01"
              stroke="currentColor"
              stroke-width="2.3"
              stroke-linecap="round"
            />
          </svg>
        </span>

        <div>
          <strong>화장실록 AI</strong>

          <small>
            가까운 화장실과 이용 후기를 찾아드려요.
          </small>
        </div>
      </div>

      <button
        class="chat-window__close"
        type="button"
        aria-label="챗봇 닫기"
        @click="open = false"
      >
        ×
      </button>
    </header>

    <!-- 채팅 메시지 영역 -->
    <div class="chat-history">
      <div
        v-for="(message, messageIndex) in messages"
        :key="messageIndex"
        class="chat-message"
        :class="message.role"
      >
        <p>{{ message.content }}</p>

        <!-- 백엔드가 반환한 화장실 검색 결과 -->
        <div
          v-if="message.locations?.length"
          class="chat-location-list"
        >
          <button
            v-for="(location, locationIndex) in message.locations"
            :key="getLocationKey(location, locationIndex)"
            class="chat-location-card"
            type="button"
            @click="openLocation(location)"
          >
            <span class="chat-location-card__copy">
              <!-- 화장실 이름 -->
              <strong>
                {{ location.name }}
              </strong>

              <!-- 평점, 거리, 개방 여부 -->
              <small>
                {{
                  location.rating == null
                    ? '리뷰 없음'
                    : `★ ${location.rating}`
                }}

                <template v-if="location.distanceMeters != null">
                  · {{ location.distanceMeters }}m
                </template>

                <template v-if="location.openNow === true">
                  · 현재 개방
                </template>
              </small>

              <!-- 최근 리뷰 미리보기 -->
              <em
                v-if="getReviewPreview(location)"
                class="chat-location-card__review"
              >
                {{ getReviewPreview(location) }}
              </em>
            </span>

            <!-- 상세 페이지 이동 화살표 -->
            <svg
              viewBox="0 0 20 20"
              fill="none"
              aria-hidden="true"
            >
              <path
                d="m8 5 5 5-5 5"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </button>
        </div>

        <!-- 백엔드 경고 메시지 -->
        <small
          v-for="warning in message.warnings || []"
          :key="warning"
          class="chat-message__warning"
        >
          {{ warning }}
        </small>
      </div>

      <p
        v-if="loading"
        class="chat-loading"
      >
        AI가 답변을 작성하고 있습니다.
      </p>

      <p
        v-if="error"
        class="form-error"
      >
        {{ error }}
      </p>
    </div>

    <!-- 메시지 입력창 -->
    <form
      class="chat-form"
      @submit.prevent="submit"
    >
      <input
        v-model="input"
        placeholder="메시지 또는 찾는 화장실 조건을 입력하세요."
        aria-label="챗봇 메시지"
        autocomplete="off"
      />

      <button
        type="submit"
        :disabled="loading || !input.trim()"
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          aria-hidden="true"
        >
          <path
            d="m4 12 16-7-5.5 14-3.2-5.7L4 12Z"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linejoin="round"
          />

          <path
            d="m11.3 13.3 4.2-4.1"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
          />
        </svg>

        <span>
          {{ loading ? '전송 중' : '전송' }}
        </span>
      </button>
    </form>
  </aside>
</template>