<script setup>
import { computed, ref } from 'vue'
import { conditionOptions } from '../data/mockData'

const emit = defineEmits(['search-ai'])
const selected = ref([])

const buttonLabel = computed(() =>
  selected.value.length
    ? `${selected.value.length}개 조건으로 AI 찾기`
    : '조건을 선택하면 AI 찾기가 활성화됩니다',
)

function toggle(condition) {
  selected.value = selected.value.includes(condition)
    ? selected.value.filter((item) => item !== condition)
    : [...selected.value, condition]
}

function submit() {
  if (!selected.value.length) return
  emit('search-ai', [...selected.value])
}
</script>

<template>
  <div class="condition-area">
    <div class="condition-heading">
      <strong>세부 조건으로 더 정확하게 찾아보세요</strong>
      <span>선택한 조건을 바탕으로 AI가 맞는 화장실을 찾아드려요.</span>
    </div>

    <div class="condition-list">
      <button
        v-for="condition in conditionOptions"
        :key="condition"
        class="condition-chip"
        :class="{ selected: selected.includes(condition) }"
        type="button"
        :aria-pressed="selected.includes(condition)"
        @click="toggle(condition)"
      >
        <span class="condition-check" aria-hidden="true">{{ selected.includes(condition) ? '✓' : '+' }}</span>
        {{ condition }}
      </button>
    </div>

    <button
      class="condition-submit"
      :class="{ ready: selected.length }"
      :disabled="!selected.length"
      type="button"
      @click="submit"
    >
      <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
        <path d="m10 2 1.7 4.3L16 8l-4.3 1.7L10 14l-1.7-4.3L4 8l4.3-1.7L10 2Z" fill="currentColor" />
        <path d="m16 13 .8 2.2L19 16l-2.2.8L16 19l-.8-2.2L13 16l2.2-.8L16 13Z" fill="currentColor" opacity=".65" />
      </svg>
      {{ buttonLabel }}
    </button>
  </div>
</template>
