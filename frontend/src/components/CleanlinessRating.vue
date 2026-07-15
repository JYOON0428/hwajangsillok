<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  modelValue: { type: Number, default: 0 },
  disabled: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])
const hoverValue = ref(0)

const displayValue = computed(() => hoverValue.value || props.modelValue || 0)
const label = computed(() => {
  if (!displayValue.value) return '별점을 선택해 주세요'
  if (displayValue.value < 3) return '청결 상태가 아쉬워요'
  if (displayValue.value < 4) return '보통이에요'
  return '깨끗해요'
})
const toneClass = computed(() => {
  if (!displayValue.value) return 'rating-empty'
  if (displayValue.value < 3) return 'rating-low'
  if (displayValue.value < 4) return 'rating-mid'
  return 'rating-high'
})

function valueFromPointer(event, star) {
  const rect = event.currentTarget.getBoundingClientRect()
  return event.clientX - rect.left < rect.width / 2 ? star - 0.5 : star
}
function setHover(event, star) {
  if (!props.disabled) hoverValue.value = valueFromPointer(event, star)
}
function select(event, star) {
  if (!props.disabled) emit('update:modelValue', valueFromPointer(event, star))
}
function fillWidth(star) {
  if (displayValue.value >= star) return '100%'
  if (displayValue.value === star - 0.5) return '50%'
  return '0%'
}
</script>

<template>
  <div class="cleanliness-rating" :class="toneClass" @mouseleave="hoverValue = 0">
    <div class="rating-stars" role="radiogroup" aria-label="청결도 별점">
      <button
        v-for="star in 5"
        :key="star"
        type="button"
        class="rating-star-button"
        :aria-label="`${star}점`"
        :aria-checked="modelValue === star"
        role="radio"
        :disabled="disabled"
        @mousemove="setHover($event, star)"
        @click="select($event, star)"
      >
        <span class="rating-star-empty">★</span>
        <span class="rating-star-fill" :style="{ width: fillWidth(star) }">★</span>
      </button>
      <strong>{{ displayValue ? displayValue.toFixed(1) : '미선택' }}</strong>
    </div>
    <span class="rating-label">{{ label }}</span>
  </div>
</template>
