<script setup>
import { nextTick, watch } from 'vue'

const props = defineProps({
  restrooms: { type: Array, default: () => [] },
  selectedId: { type: Number, default: null },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
})

const emit = defineEmits(['select'])
const cardElements = new Map()

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

function filteredTags(tags = []) {
  const operationLabels = ['현재 개방', '현재 운영 종료', '운영 종료']
  return tags.filter((tag) => !operationLabels.includes(tag))
}

function visibleTags(restroom) {
  return filteredTags(restroom.tags).slice(0, 3)
}

function hiddenTagCount(restroom) {
  return Math.max(0, filteredTags(restroom.tags).length - 3)
}

function setCardRef(element, id) {
  if (element) cardElements.set(id, element)
  else cardElements.delete(id)
}

watch(
  () => props.selectedId,
  async (id) => {
    if (!id) return
    await nextTick()
    cardElements.get(id)?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
  },
)
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
      :ref="(element) => setCardRef(element, restroom.id)"
      class="restroom-list-card"
      :class="{ selected: selectedId === restroom.id }"
      type="button"
      @click="emit('select', restroom.id)"
    >
      <div class="restroom-list-card__top">
        <strong>{{ restroom.name }}</strong>
        <span class="distance-badge">{{ restroom.distanceMeters }}m</span>
      </div>

      <div class="restroom-card-metrics">
        <template v-if="restroom.rating != null">
          <strong :class="ratingClass(restroom.rating)">★ {{ restroom.rating }}</strong>
          <span>리뷰 {{ restroom.reviewCount }}개</span>
        </template>
        <span v-else class="rating-none">리뷰 없음</span>

        <span
          class="operation-status-badge"
          :class="operationStatus(restroom).className"
        >
          <i aria-hidden="true" />
          {{ operationStatus(restroom).label }}
        </span>
      </div>

      <p class="restroom-address">{{ restroom.address }}</p>

      <div v-if="visibleTags(restroom).length" class="restroom-card-tags">
        <span v-for="tag in visibleTags(restroom)" :key="tag">{{ tag }}</span>
        <span v-if="hiddenTagCount(restroom)" class="restroom-card-tags__more">
          +{{ hiddenTagCount(restroom) }}
        </span>
      </div>
    </button>
  </div>
</template>
