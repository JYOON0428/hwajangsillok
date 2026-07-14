<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  images: {
    type: Array,
    default: () => [],
  },
  alt: {
    type: String,
    default: '게시글 첨부 이미지',
  },
  variant: {
    type: String,
    default: 'feed',
  },
})

const currentIndex = ref(0)
const validImages = computed(() => props.images.filter(Boolean))
const currentImage = computed(() => validImages.value[currentIndex.value] || '')
const hasMultiple = computed(() => validImages.value.length > 1)

watch(
  validImages,
  () => {
    currentIndex.value = 0
  },
  { deep: true },
)

function previous() {
  if (!validImages.value.length) return
  currentIndex.value = (currentIndex.value - 1 + validImages.value.length) % validImages.value.length
}

function next() {
  if (!validImages.value.length) return
  currentIndex.value = (currentIndex.value + 1) % validImages.value.length
}

function goTo(index) {
  currentIndex.value = index
}

function handleKeydown(event) {
  if (event.key === 'ArrowLeft') previous()
  if (event.key === 'ArrowRight') next()
}
</script>

<template>
  <div
    v-if="validImages.length"
    class="post-image-carousel"
    :class="`post-image-carousel--${variant}`"
    tabindex="0"
    role="region"
    aria-label="게시글 첨부 이미지"
    @keydown="handleKeydown"
  >
    <div class="post-image-carousel__stage">
      <img
        :src="currentImage"
        :alt="`${alt} ${currentIndex + 1}`"
        loading="lazy"
      />

      <button
        v-if="hasMultiple"
        class="post-image-carousel__arrow previous"
        type="button"
        aria-label="이전 이미지"
        @click.stop="previous"
      >
        ‹
      </button>
      <button
        v-if="hasMultiple"
        class="post-image-carousel__arrow next"
        type="button"
        aria-label="다음 이미지"
        @click.stop="next"
      >
        ›
      </button>

      <span v-if="hasMultiple" class="post-image-carousel__counter">
        {{ currentIndex + 1 }} / {{ validImages.length }}
      </span>
    </div>

    <div v-if="hasMultiple" class="post-image-carousel__dots" aria-label="이미지 선택">
      <button
        v-for="(_, index) in validImages"
        :key="index"
        type="button"
        :class="{ active: currentIndex === index }"
        :aria-label="`${index + 1}번째 이미지 보기`"
        :aria-current="currentIndex === index ? 'true' : undefined"
        @click.stop="goTo(index)"
      />
    </div>
  </div>
</template>
