<script setup>
import { computed } from 'vue'

const props = defineProps({
  page: { type: Number, default: 1 },
  size: { type: Number, default: 10 },
  total: { type: Number, default: 0 },
})

const emit = defineEmits(['change'])
const pageCount = computed(() => Math.max(1, Math.ceil(props.total / props.size)))

const desktopItems = computed(() => {
  const count = pageCount.value
  const current = Math.min(Math.max(1, props.page), count)

  if (count <= 7) return Array.from({ length: count }, (_, index) => index + 1)
  if (current <= 4) return [1, 2, 3, 4, 5, 'end-ellipsis', count]
  if (current >= count - 3) return [1, 'start-ellipsis', count - 4, count - 3, count - 2, count - 1, count]
  return [1, 'start-ellipsis', current - 1, current, current + 1, 'end-ellipsis', count]
})

function move(nextPage) {
  const normalized = Math.min(Math.max(1, nextPage), pageCount.value)
  if (normalized === props.page) return
  emit('change', normalized)
}
</script>

<template>
  <nav class="community-pagination" aria-label="게시글 페이지 이동">
    <button
      type="button"
      class="community-pagination__move"
      :disabled="page <= 1"
      @click="move(page - 1)"
    >
      이전
    </button>

    <div class="community-pagination__desktop">
      <template v-for="item in desktopItems" :key="item">
        <span v-if="typeof item === 'string'" class="community-pagination__ellipsis" aria-hidden="true">…</span>
        <button
          v-else
          type="button"
          :class="{ active: item === page }"
          :aria-current="item === page ? 'page' : undefined"
          @click="move(item)"
        >
          {{ item }}
        </button>
      </template>
    </div>

    <span class="community-pagination__mobile" aria-live="polite">
      {{ page }} / {{ pageCount }}
    </span>

    <button
      type="button"
      class="community-pagination__move"
      :disabled="page >= pageCount"
      @click="move(page + 1)"
    >
      다음
    </button>
  </nav>
</template>
