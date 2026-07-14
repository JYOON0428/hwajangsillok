<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { sendChat } from '../services/chatApi'

const open = ref(false)
const input = ref('')
const loading = ref(false)
const error = ref('')
const messages = ref([
  {
    role: 'assistant',
    content: '원하는 조건을 말해보세요. 예: “경복궁 근처 기저귀 교환대가 있고 청결도 높은 곳”',
  },
])

function openFromEvent(event) {
  open.value = true
  input.value = event.detail || ''
  if (input.value) submit()
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
    <header>
      <div>
        <strong>화장실록 AI 찾기</strong>
        <small>공공데이터와 최근 리뷰를 함께 검색합니다.</small>
      </div>
      <button type="button" aria-label="챗봇 닫기" @click="open = false">×</button>
    </header>
    <div class="chat-history">
      <div v-for="(message, index) in messages" :key="index" class="chat-message" :class="message.role">
        <p>{{ message.content }}</p>
        <div v-if="message.locations?.length" class="chat-location-list">
          <article v-for="location in message.locations" :key="location.id">
            <strong>{{ location.name }}</strong>
            <span>{{ location.rating == null ? '리뷰 없음' : `★ ${location.rating}` }} · {{ location.distanceMeters }}m</span>
          </article>
        </div>
        <small v-for="warning in message.warnings" :key="warning">{{ warning }}</small>
      </div>
      <p v-if="loading" class="chat-loading">AI가 조건을 확인하고 있습니다.</p>
      <p v-if="error" class="form-error">{{ error }}</p>
    </div>
    <form class="chat-form" @submit.prevent="submit">
      <input v-model="input" placeholder="조건을 자연어로 입력하세요" />
      <button type="submit" :disabled="loading">전송</button>
    </form>
  </aside>
</template>
