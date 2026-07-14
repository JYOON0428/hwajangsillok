<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  postId: {
    type: [Number, String],
    required: true,
  },
  score: {
    type: Number,
    default: 0,
  },
  label: {
    type: String,
    default: '게시글 추천',
  },
})

const storageKey = computed(() => `hwajangsillok.vote.${props.postId}`)
const vote = ref(0)

function readVote() {
  const stored = Number(localStorage.getItem(storageKey.value) || 0)
  vote.value = [-1, 0, 1].includes(stored) ? stored : 0
}

watch(storageKey, readVote, { immediate: true })

const displayedScore = computed(() => Number(props.score || 0) + vote.value)

function toggleVote(direction) {
  vote.value = vote.value === direction ? 0 : direction
  localStorage.setItem(storageKey.value, String(vote.value))
}
</script>

<template>
  <div class="post-vote-control" :aria-label="label">
    <button
      type="button"
      class="post-vote-button up"
      :class="{ active: vote === 1 }"
      :aria-pressed="vote === 1"
      aria-label="추천"
      title="추천"
      @click.stop="toggleVote(1)"
    >
      <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="m12 5-6 7h4v7h4v-7h4l-6-7Z" stroke="currentColor" stroke-width="1.9" stroke-linejoin="round" />
      </svg>
    </button>

    <strong :class="{ positive: vote === 1, negative: vote === -1 }">
      {{ displayedScore }}
    </strong>

    <button
      type="button"
      class="post-vote-button down"
      :class="{ active: vote === -1 }"
      :aria-pressed="vote === -1"
      aria-label="비추천"
      title="비추천"
      @click.stop="toggleVote(-1)"
    >
      <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="m12 19 6-7h-4V5h-4v7H6l6 7Z" stroke="currentColor" stroke-width="1.9" stroke-linejoin="round" />
      </svg>
    </button>
  </div>
</template>
