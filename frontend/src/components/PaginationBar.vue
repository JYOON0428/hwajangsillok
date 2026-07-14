<script setup>
import { computed } from 'vue'

const props = defineProps({
  page: { type: Number, default: 1 },
  size: { type: Number, default: 9 },
  total: { type: Number, default: 0 },
})

const emit = defineEmits(['change'])
const pageCount = computed(() => Math.max(1, Math.ceil(props.total / props.size)))
</script>

<template>
  <nav class="pagination" aria-label="페이지 이동">
    <button type="button" :disabled="page <= 1" @click="emit('change', page - 1)">이전</button>
    <button
      v-for="number in pageCount"
      :key="number"
      type="button"
      :class="{ active: number === page }"
      @click="emit('change', number)"
    >
      {{ number }}
    </button>
    <button type="button" :disabled="page >= pageCount" @click="emit('change', page + 1)">다음</button>
  </nav>
</template>
