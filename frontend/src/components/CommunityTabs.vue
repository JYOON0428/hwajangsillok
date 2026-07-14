<script setup>
defineProps({
  modelValue: {
    type: String,
    default: '전체',
  },
  variant: {
    type: String,
    default: 'cards',
    validator: (value) => ['cards', 'pills'].includes(value),
  },
})

const emit = defineEmits(['update:modelValue'])

const categories = [
  { name: '전체', icon: 'grid' },
  { name: '관광지', icon: 'location' },
  { name: '문화시설', icon: 'museum' },
  { name: '축제·공연', icon: 'ticket' },
  { name: '쇼핑', icon: 'shopping' },
  { name: '자유게시판', icon: 'chat' },
]
</script>

<template>
  <div
    class="category-card-grid"
    :class="`category-card-grid--${variant}`"
    role="tablist"
    aria-label="게시글 카테고리"
  >
    <button
      v-for="category in categories"
      :key="category.name"
      type="button"
      role="tab"
      class="category-card"
      :class="[
        `category-card--${variant}`,
        { active: modelValue === category.name },
      ]"
      :aria-selected="modelValue === category.name"
      @click="emit('update:modelValue', category.name)"
    >
      <span class="category-card-icon">
        <svg
          v-if="category.icon === 'grid'"
          viewBox="0 0 24 24"
          fill="none"
          aria-hidden="true"
        >
          <rect x="4" y="4" width="6" height="6" rx="1.5" stroke="currentColor" stroke-width="1.8" />
          <rect x="14" y="4" width="6" height="6" rx="1.5" stroke="currentColor" stroke-width="1.8" />
          <rect x="4" y="14" width="6" height="6" rx="1.5" stroke="currentColor" stroke-width="1.8" />
          <rect x="14" y="14" width="6" height="6" rx="1.5" stroke="currentColor" stroke-width="1.8" />
        </svg>

        <svg
          v-else-if="category.icon === 'location'"
          viewBox="0 0 24 24"
          fill="none"
          aria-hidden="true"
        >
          <path
            d="M12 21s7-6.1 7-12a7 7 0 1 0-14 0c0 5.9 7 12 7 12Z"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linejoin="round"
          />
          <circle cx="12" cy="9" r="2.5" stroke="currentColor" stroke-width="1.8" />
        </svg>

        <svg
          v-else-if="category.icon === 'museum'"
          viewBox="0 0 24 24"
          fill="none"
          aria-hidden="true"
        >
          <path d="m4 9 8-5 8 5H4Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" />
          <path d="M6 10v7M10 10v7M14 10v7M18 10v7M4 20h16M5 17h14" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
        </svg>

        <svg
          v-else-if="category.icon === 'ticket'"
          viewBox="0 0 24 24"
          fill="none"
          aria-hidden="true"
        >
          <path
            d="M5 6h14a2 2 0 0 1 2 2v2a2.5 2.5 0 0 0 0 5v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1a2.5 2.5 0 0 0 0-5V8a2 2 0 0 1 2-2Z"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linejoin="round"
          />
          <path d="M12 8v2M12 14v2" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
        </svg>

        <svg
          v-else-if="category.icon === 'shopping'"
          viewBox="0 0 24 24"
          fill="none"
          aria-hidden="true"
        >
          <path d="M5 8h14l-1 12H6L5 8Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" />
          <path d="M9 9V7a3 3 0 0 1 6 0v2" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
        </svg>

        <svg
          v-else
          viewBox="0 0 24 24"
          fill="none"
          aria-hidden="true"
        >
          <path d="M5 5h14v11H9l-4 3V5Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" />
          <path d="M8 9h8M8 12h5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
        </svg>
      </span>

      <strong>{{ category.name }}</strong>
    </button>
  </div>
</template>
