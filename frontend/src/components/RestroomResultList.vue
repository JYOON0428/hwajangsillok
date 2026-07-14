<script setup>
defineProps({
  restrooms: { type: Array, default: () => [] },
  selectedId: { type: Number, default: null },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
})

const emit = defineEmits(['select'])

function ratingClass(rating) {
  if (rating == null) return 'rating-none'
  if (rating >= 4) return 'rating-high'
  if (rating >= 3) return 'rating-mid'
  return 'rating-low'
}

function operationStatus(restroom) {
  if (restroom.openNow === true) {
    return { label: '현재 개방', className: 'status-open' }
  }
  if (restroom.openNow === false) {
    return { label: '현재 운영 종료', className: 'status-closed' }
  }
  return { label: '운영 여부 확인 필요', className: 'status-unknown' }
}

function visibleTags(tags = []) {
  const operationLabels = ['현재 개방', '현재 운영 종료', '운영 종료']
  return tags.filter((tag) => !operationLabels.includes(tag)).slice(0, 3)
}
</script>

<template>
  <div class="restroom-result-list" aria-live="polite">
    <p v-if="loading" class="search-state">화장실을 검색하고 있습니다.</p>
    <p v-else-if="error" class="search-state error">{{ error }}</p>

    <div v-else-if="!restrooms.length" class="empty-search-state">
      <strong>조건에 맞는 화장실이 없습니다.</strong>
      <p>검색 반경을 넓히거나 필터를 줄여보세요.</p>
    </div>

    <button
      v-for="restroom in restrooms"
      v-else
      :key="restroom.id"
      class="restroom-list-card"
      :class="{ selected: selectedId === restroom.id }"
      type="button"
      @click="emit('select', restroom.id)"
    >
      <div class="restroom-list-card__top">
        <strong>{{ restroom.name }}</strong>
        <span class="distance-badge">{{ restroom.distanceMeters }}m</span>
      </div>

      <p class="restroom-address">{{ restroom.address }}</p>

      <div class="restroom-card-metrics">
        <span :class="ratingClass(restroom.rating)">
          {{ restroom.rating == null ? '리뷰 없음' : `★ ${restroom.rating}` }}
        </span>
        <span>리뷰 {{ restroom.reviewCount }}개</span>
        <span
          class="operation-status-badge"
          :class="operationStatus(restroom).className"
        >
          <i aria-hidden="true" />
          {{ operationStatus(restroom).label }}
        </span>
      </div>

      <div v-if="visibleTags(restroom.tags).length" class="restroom-card-tags">
        <span v-for="tag in visibleTags(restroom.tags)" :key="tag">{{ tag }}</span>
      </div>
    </button>
  </div>
</template>
