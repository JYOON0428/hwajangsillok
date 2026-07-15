<script setup>
import { useRouter } from 'vue-router'
import CommunityTabs from './CommunityTabs.vue'

const router = useRouter()

function openCategory(category) {
  router.push({
    name: 'community',
    query: category === '전체' ? {} : { category },
  })
}
</script>

<template>
  <section class="content-section category-section">
    <div class="category-section-header">
      <h2>카테고리</h2>

      <RouterLink
        class="category-write-button"
        :to="{ name: 'post-create' }"
      >
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path
            d="m14.5 5.5 4 4M4 20l3.8-.8L19.2 7.8a1.4 1.4 0 0 0 0-2l-1-1a1.4 1.4 0 0 0-2 0L4.8 16.2 4 20Z"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
        <span>리뷰 쓰기</span>
      </RouterLink>
    </div>

    <CommunityTabs
      model-value="전체"
      @update:model-value="openCategory"
    />
  </section>
</template>
