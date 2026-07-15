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
  downvotes: {
    type: Number,
    default: 0,
  },
  label: {
    type: String,
    default: '게시글 추천과 비추천',
  },
})

const storageKey = computed(() => `hwajangsillok.vote.${props.postId}`)
const vote = ref(0)

function readVote() {
  const stored = Number(localStorage.getItem(storageKey.value) || 0)
  vote.value = [-1, 0, 1].includes(stored) ? stored : 0
}

watch(storageKey, readVote, { immediate: true })

const displayedUpvotes = computed(() => Number(props.score || 0) + (vote.value === 1 ? 1 : 0))
const displayedDownvotes = computed(() => Number(props.downvotes || 0) + (vote.value === -1 ? 1 : 0))

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
      @click.stop="toggleVote(1)"
    >
      <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M7.5 10.5 11 4.7c.8-1.3 2.8-.7 2.8.8v3.2h3.7a2 2 0 0 1 1.9 2.6l-1.7 6a2 2 0 0 1-1.9 1.4H7.5v-8.2Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" />
        <path d="M4 10.5h3.5v8.2H4z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" />
      </svg>
      <span>추천</span>
      <strong>{{ displayedUpvotes }}</strong>
    </button>

    <button
      type="button"
      class="post-vote-button down"
      :class="{ active: vote === -1 }"
      :aria-pressed="vote === -1"
      @click.stop="toggleVote(-1)"
    >
      <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M7.5 13.5 11 19.3c.8 1.3 2.8.7 2.8-.8v-3.2h3.7a2 2 0 0 0 1.9-2.6l-1.7-6a2 2 0 0 0-1.9-1.4H7.5v8.2Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" />
        <path d="M4 5.3h3.5v8.2H4z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" />
      </svg>
      <span>비추천</span>
      <strong>{{ displayedDownvotes }}</strong>
    </button>
  </div>
</template>
