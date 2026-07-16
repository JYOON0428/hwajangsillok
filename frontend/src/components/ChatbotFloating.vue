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
    content: '찾는 장소와 필요한 시설을 알려주세요.',
  },
])

function openFromEvent(event) {
  open.value = true
  input.value = event.detail || ''
  if (input.value) submit()
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

function openLocation(location) {
  const locationId = getLocationId(location)

  if (!locationId) {
    error.value = '화장실 상세 정보를 확인할 수 없습니다.'
    return
  }

  open.value = false
  router.push({
    name: 'restroom-reviews',
    params: { id: String(locationId) },
  })
}

async function submit() {
  const message = input.value.trim()
  if (!message || loading.value) return

  messages.value.push({ role: 'user', content: message })
  input.value = ''
  loading.value = true
  error.value = ''

  try {
    const response = await sendChat({
      message,
      history: messages.value.map(({ role, content }) => ({ role, content })),
      location_id: null,
    })

    messages.value.push({
      role: 'assistant',
      content: response.answer,
      locations: response.locations || [],
      warnings: response.warnings || [],
    })
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

onMounted(() => window.addEventListener('open-ai-chat', openFromEvent))
onBeforeUnmount(() => window.removeEventListener('open-ai-chat', openFromEvent))
</script>

<template>
  <button class="chat-fab" type="button" aria-label="AI 챗봇 열기" @click="open = !open">
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M6 18.5 3.5 21v-5A8 8 0 1 1 7 19.4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
      <path d="M8 11h.01M12 11h.01M16 11h.01" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" />
    </svg>
  </button>

  <aside v-if="open" class="chat-window" aria-label="화장실록 AI 챗봇">
    <header class="chat-window__header">
      <div class="chat-window__brand">
        <span class="chat-window__brand-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none">
            <path d="M6 18.5 3.5 21v-5A8 8 0 1 1 7 19.4" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" />
            <path d="M8 11h.01M12 11h.01M16 11h.01" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" />
          </svg>
        </span>
        <div>
          <strong>화장실록 AI</strong>
          <small>가까운 화장실과 이용 후기를 찾아드려요.</small>
        </div>
      </div>

      <button class="chat-window__close" type="button" aria-label="챗봇 닫기" @click="open = false">×</button>
    </header>

    <div class="chat-history">
      <div
        v-for="(message, index) in messages"
        :key="index"
        class="chat-message"
        :class="message.role"
      >
        <p>{{ message.content }}</p>

        <div v-if="message.locations?.length" class="chat-location-list">
          <button
            v-for="location in message.locations"
            :key="location.toiletId ?? location.toilet_id ?? location.id"
            class="chat-location-card"
            type="button"
            @click="openLocation(location)"
          >
            <span class="chat-location-card__copy">
              <strong>{{ location.name }}</strong>
              <small>
                {{ location.rating == null ? '리뷰 없음' : `★ ${location.rating}` }}
                <template v-if="location.distanceMeters != null">
                  · {{ location.distanceMeters }}m
                </template>
                <template v-if="location.openNow === true"> · 현재 개방</template>
              </small>
            </span>

            <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
              <path d="m8 5 5 5-5 5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </button>
        </div>

        <small v-for="warning in message.warnings" :key="warning" class="chat-message__warning">
          {{ warning }}
        </small>
      </div>

      <p v-if="loading" class="chat-loading">AI가 조건을 확인하고 있습니다.</p>
      <p v-if="error" class="form-error">{{ error }}</p>
    </div>

    <form class="chat-form" @submit.prevent="submit">
      <input
        v-model="input"
        placeholder="찾는 장소와 필요한 시설을 알려주세요."
        aria-label="챗봇 메시지"
      />
      <button type="submit" :disabled="loading || !input.trim()">
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="m4 12 16-7-5.5 14-3.2-5.7L4 12Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" />
          <path d="m11.3 13.3 4.2-4.1" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
        </svg>
        <span>{{ loading ? '전송 중' : '전송' }}</span>
      </button>
    </form>
  </aside>
</template>
