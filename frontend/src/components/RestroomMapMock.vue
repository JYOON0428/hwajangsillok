<script setup>
defineProps({
  restrooms: { type: Array, default: () => [] },
})

function ratingClass(rating) {
  if (rating == null) return 'none'
  if (rating >= 4) return 'high'
  if (rating >= 3) return 'mid'
  return 'low'
}
</script>

<template>
  <div class="map-mock" aria-label="주변 화장실 지도 목업">
    <div class="map-grid" />
    <div class="map-water" />
    <div class="map-park park-one" />
    <div class="map-park park-two" />
    <button
      v-for="(restroom, index) in restrooms.slice(0, 4)"
      :key="restroom.id"
      class="map-pin"
      :class="ratingClass(restroom.rating)"
      :style="{
        left: `${22 + ((index * 19) % 56)}%`,
        top: `${22 + ((index * 23) % 55)}%`,
      }"
      :title="`${restroom.name} ${restroom.rating ?? '리뷰 없음'}`"
      type="button"
    >
      <span>★</span>
    </button>
    <span class="current-location" title="현재 위치" />
    <div class="map-legend">
      <span><i class="high" />4.0 이상</span>
      <span><i class="mid" />3.0~3.9</span>
      <span><i class="low" />3.0 미만</span>
      <span><i class="none" />리뷰 없음</span>
    </div>
  </div>
</template>
