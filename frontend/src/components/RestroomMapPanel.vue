<script setup>
import { computed } from 'vue'

const props = defineProps({
  restrooms: { type: Array, default: () => [] },
  selectedId: { type: Number, default: null },
})

const emit = defineEmits(['select', 'search-current-map', 'open-detail'])

const selected = computed(() => props.restrooms.find((item) => item.id === props.selectedId) || null)

function ratingClass(rating) {
  if (rating == null) return 'none'
  if (rating >= 4) return 'high'
  if (rating >= 3) return 'mid'
  return 'low'
}

function operationStatus(restroom) {
  if (restroom.openNow === true) return '현재 개방'
  if (restroom.openNow === false) return '현재 운영 종료'
  return '운영 여부 확인 필요'
}
</script>

<template>
  <section class="restroom-map-panel" aria-label="화장실 지도 목업">
    <div class="map-pattern" />
    <div class="map-river" />
    <div class="map-green green-one" />
    <div class="map-green green-two" />

    <button class="map-research-button" type="button" @click="emit('search-current-map')">
      현재 지도에서 다시 검색
    </button>

    <button
      v-for="restroom in restrooms"
      :key="restroom.id"
      class="restroom-map-pin"
      :class="[
        ratingClass(restroom.rating),
        { selected: restroom.id === selectedId },
      ]"
      :style="{
        left: `${restroom.mapPosition?.x ?? 50}%`,
        top: `${restroom.mapPosition?.y ?? 50}%`,
      }"
      type="button"
      :aria-label="`${restroom.name} 선택`"
      @click="emit('select', restroom.id)"
    >
      <span>★</span>
      <i v-if="restroom.recentStatus">!</i>
      <b v-if="restroom.id === selectedId">{{ restroom.name }}</b>
    </button>

    <span class="map-current-location" title="현재 위치" />

    <div class="map-color-legend">
      <span><i class="high" />4.0 이상</span>
      <span><i class="mid" />3.0~3.9</span>
      <span><i class="low" />3.0 미만</span>
      <span><i class="none" />리뷰 없음</span>
      <span><em>!</em>최근 상태 제보</span>
    </div>

    <article v-if="selected" class="mobile-map-summary">
      <div>
        <strong>{{ selected.name }}</strong>
        <p>
          {{ selected.rating == null ? '리뷰 없음' : `★ ${selected.rating}` }} ·
          {{ selected.distanceMeters }}m ·
          {{ operationStatus(selected) }}
        </p>
      </div>
      <button type="button" @click="emit('open-detail')">리뷰 보기</button>
    </article>
  </section>
</template>
