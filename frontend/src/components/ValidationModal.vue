<script setup>
defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: '입력 내용을 확인해 주세요' },
  messages: { type: Array, default: () => [] },
})

const emit = defineEmits(['close'])
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="validation-modal-backdrop" role="presentation" @click.self="emit('close')">
      <section class="validation-modal" role="alertdialog" aria-modal="true" aria-labelledby="validation-title">
        <div class="validation-modal-icon" aria-hidden="true">!</div>
        <h2 id="validation-title">{{ title }}</h2>
        <p>아래 항목을 입력한 뒤 다시 등록해 주세요.</p>
        <ul>
          <li v-for="message in messages" :key="message">{{ message }}</li>
        </ul>
        <button type="button" class="primary-button" autofocus @click="emit('close')">확인</button>
      </section>
    </div>
  </Teleport>
</template>
