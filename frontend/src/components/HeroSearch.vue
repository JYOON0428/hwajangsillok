<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import ConditionChips from './ConditionChips.vue'

const router = useRouter()
const query = ref('')

function submitSearch() {
  const value = query.value.trim() || '경복궁 근처 화장실'
  router.push({ name: 'search', query: { q: value, radius: 500 } })
}

function emitAiSearch(conditions) {
  window.dispatchEvent(
    new CustomEvent('open-ai-chat', {
      detail: `${conditions.join(', ')} 조건에 맞는 가까운 화장실을 찾아줘.`,
    }),
  )
}
</script>

<template>
  <section class="hero-section">
    <div class="hero-decor hero-decor-one" aria-hidden="true" />
    <div class="hero-decor hero-decor-two" aria-hidden="true" />

    <div class="hero-content">
      <span class="hero-label">
        <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
          <path d="m10 2 1.7 4.3L16 8l-4.3 1.7L10 14l-1.7-4.3L4 8l4.3-1.7L10 2Z" fill="currentColor" />
          <path d="m16 13 .8 2.2L19 16l-2.2.8L16 19l-.8-2.2L13 16l2.2-.8L16 13Z" fill="currentColor" opacity=".6" />
        </svg>
        공공데이터에 이용 경험을 더하다
      </span>

      <h1>가까운 화장실을<br />더 빠르고 정확하게</h1>
      <p>장소를 검색하고, 청결도와 편의시설 정보를 한눈에 비교하세요.</p>

      <form class="main-search" @submit.prevent="submitSearch">
        <input
          v-model="query"
          type="search"
          placeholder="지역명, 역명, 관광지를 검색하세요"
          aria-label="화장실 검색"
        />
        <button type="submit" aria-label="화장실 검색 실행">
          <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <circle cx="11" cy="11" r="6.5" stroke="currentColor" stroke-width="2" />
            <path d="m16 16 4 4" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
          </svg>
        </button>
      </form>

      <p class="search-helper">
        예: 경복궁 근처 화장실 · 강남역 · 서울숲
      </p>

      <ConditionChips @search-ai="emitAiSearch" />
    </div>
  </section>
</template>
