<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: '비밀번호 확인' },
  busy: { type: Boolean, default: false },
  error: { type: String, default: '' },
})

const emit = defineEmits(['close', 'confirm'])
const password = ref('')

watch(
  () => props.open,
  (open) => {
    if (open) password.value = ''
  },
)
</script>

<template>
  <div v-if="open" class="modal-backdrop" @click.self="emit('close')">
    <section class="password-modal" role="dialog" aria-modal="true">
      <h2>{{ title }}</h2>
      <p>게시글 작성 시 등록한 수정용 비밀번호를 입력하세요.</p>
      <input v-model="password" type="password" autocomplete="current-password" @keydown.enter="emit('confirm', password)" />
      <p v-if="error" class="form-error">{{ error }}</p>
      <div class="modal-actions">
        <button class="secondary-button" type="button" @click="emit('close')">취소</button>
        <button class="danger-button" type="button" :disabled="busy || !password" @click="emit('confirm', password)">
          {{ busy ? '처리 중' : '확인' }}
        </button>
      </div>
    </section>
  </div>
</template>
