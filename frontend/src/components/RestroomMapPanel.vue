<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  restrooms: { type: Array, default: () => [] },
  selectedId: { type: Number, default: null },
  anchorLocation: { type: Object, default: null },
  selectedOnly: { type: Boolean, default: false },
  showResearchButton: { type: Boolean, default: true },
  resultCount: { type: Number, default: 0 },
})

const emit = defineEmits(['select', 'search-current-map', 'open-detail'])

const kakaoMapAppKey = import.meta.env.VITE_KAKAO_MAP_APP_KEY || ''
const panelRef = ref(null)
const mapContainer = ref(null)
const mapReady = ref(false)
const legendOpen = ref(true)
const isFullscreen = ref(false)
const mapError = ref('')
let map = null
let overlays = []
let sdkPromise = null

const selected = computed(() => props.restrooms.find((item) => item.id === props.selectedId) || null)
const visibleRestrooms = computed(() => {
  if (props.selectedOnly && selected.value) return [selected.value]
  return props.restrooms
})
const canUseKakaoMap = computed(() => Boolean(kakaoMapAppKey) && !mapError.value)

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

function centerLatLng() {
  const source = props.anchorLocation || selected.value || props.restrooms[0]
  return {
    latitude: Number(source?.latitude || 37.5665),
    longitude: Number(source?.longitude || 126.9780),
  }
}

function loadKakaoMapSdk() {
  if (!kakaoMapAppKey) {
    return Promise.reject(new Error('Kakao Maps JavaScript 키가 설정되지 않았습니다.'))
  }
  if (window.kakao?.maps) return Promise.resolve(window.kakao)
  if (sdkPromise) return sdkPromise

  sdkPromise = new Promise((resolve, reject) => {
    const existing = document.getElementById('kakao-map-sdk')
    if (existing) {
      existing.addEventListener('load', () => window.kakao.maps.load(() => resolve(window.kakao)), { once: true })
      existing.addEventListener('error', () => reject(new Error('Kakao Maps SDK를 불러오지 못했습니다.')), { once: true })
      return
    }

    const script = document.createElement('script')
    script.id = 'kakao-map-sdk'
    script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${encodeURIComponent(kakaoMapAppKey)}&autoload=false`
    script.async = true
    script.onload = () => window.kakao.maps.load(() => resolve(window.kakao))
    script.onerror = () => reject(new Error('Kakao Maps SDK를 불러오지 못했습니다.'))
    document.head.appendChild(script)
  })

  return sdkPromise
}

async function initMap() {
  if (!mapContainer.value || map) return

  try {
    const kakao = await loadKakaoMapSdk()
    const center = centerLatLng()
    map = new kakao.maps.Map(mapContainer.value, {
      center: new kakao.maps.LatLng(center.latitude, center.longitude),
      level: 4,
    })
    mapReady.value = true
    renderMarkers()
  } catch (error) {
    mapError.value = error.message || '지도를 불러오지 못했습니다.'
  }
}

function clearMarkers() {
  overlays.forEach((overlay) => overlay.setMap(null))
  overlays = []
}

function createMarkerElement(restroom) {
  const marker = document.createElement('button')
  marker.type = 'button'
  marker.className = [
    'kakao-restroom-marker',
    ratingClass(restroom.rating),
    restroom.id === props.selectedId ? 'selected' : '',
  ].filter(Boolean).join(' ')
  marker.setAttribute('aria-label', `${restroom.name} 선택`)
  marker.innerHTML = `
    <span>${restroom.rating == null ? '·' : Number(restroom.rating).toFixed(1)}</span>
    <b>${restroom.name}</b>
  `
  marker.addEventListener('click', (event) => {
    event.stopPropagation()
    emit('select', restroom.id)
  })
  return marker
}

function createAnchorElement() {
  const marker = document.createElement('div')
  marker.className = 'kakao-search-anchor-marker'
  marker.innerHTML = `
    <span></span>
    <b>${props.anchorLocation?.label || '검색 위치'}</b>
  `
  return marker
}

function renderMarkers({ preserveCenter = false } = {}) {
  if (!map || !window.kakao?.maps) return

  clearMarkers()
  const bounds = new window.kakao.maps.LatLngBounds()
  let hasBounds = false
  let pointCount = 0

  if (props.anchorLocation) {
    const anchorLatitude = Number(props.anchorLocation.latitude)
    const anchorLongitude = Number(props.anchorLocation.longitude)
    if (Number.isFinite(anchorLatitude) && Number.isFinite(anchorLongitude)) {
      const anchorPosition = new window.kakao.maps.LatLng(anchorLatitude, anchorLongitude)
      const anchorOverlay = new window.kakao.maps.CustomOverlay({
        position: anchorPosition,
        content: createAnchorElement(),
        xAnchor: 0.5,
        yAnchor: 0.5,
        zIndex: 20,
      })
      anchorOverlay.setMap(map)
      overlays.push(anchorOverlay)
      bounds.extend(anchorPosition)
      hasBounds = true
      pointCount += 1
    }
  }

  visibleRestrooms.value.forEach((restroom) => {
    const latitude = Number(restroom.latitude)
    const longitude = Number(restroom.longitude)
    if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) return

    const position = new window.kakao.maps.LatLng(latitude, longitude)
    const overlay = new window.kakao.maps.CustomOverlay({
      position,
      content: createMarkerElement(restroom),
      xAnchor: 0.5,
      yAnchor: 1,
      zIndex: restroom.id === props.selectedId ? 10 : 3,
    })
    overlay.setMap(map)
    overlays.push(overlay)
    bounds.extend(position)
    hasBounds = true
    pointCount += 1
  })

  if (!preserveCenter && hasBounds) {
    if (pointCount === 1) {
      const center = centerLatLng()
      map.setCenter(new window.kakao.maps.LatLng(center.latitude, center.longitude))
      map.setLevel(4)
    } else {
      map.setBounds(bounds)
    }
  }
}


async function toggleFullscreen() {
  try {
    if (!document.fullscreenElement) {
      await panelRef.value?.requestFullscreen?.()
    } else {
      await document.exitFullscreen?.()
    }
  } catch {
    // 브라우저가 전체화면을 지원하지 않아도 지도 이용에는 영향이 없다.
  }
}

function syncFullscreenState() {
  isFullscreen.value = document.fullscreenElement === panelRef.value
  if (map && window.kakao?.maps) {
    requestAnimationFrame(() => {
      map.relayout()
      renderMarkers({ preserveCenter: true })
    })
  }
}

function panToSelected() {
  if (!map || !selected.value || !window.kakao?.maps) return
  const latitude = Number(selected.value.latitude)
  const longitude = Number(selected.value.longitude)
  if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) return
  map.panTo(new window.kakao.maps.LatLng(latitude, longitude))
}

onMounted(async () => {
  document.addEventListener('fullscreenchange', syncFullscreenState)
  await nextTick()
  initMap()
})

watch(
  () => props.restrooms,
  () => renderMarkers(),
  { deep: true },
)

watch(
  () => [props.anchorLocation, props.selectedOnly],
  () => renderMarkers(),
  { deep: true },
)

watch(
  () => props.selectedId,
  () => {
    renderMarkers({ preserveCenter: true })
    panToSelected()
  },
)

onBeforeUnmount(() => {
  document.removeEventListener('fullscreenchange', syncFullscreenState)
  clearMarkers()
  map = null
})
</script>

<template>
  <section ref="panelRef" class="restroom-map-panel" aria-label="화장실 지도">
    <template v-if="canUseKakaoMap">
      <div ref="mapContainer" class="kakao-map-canvas" />
    </template>

    <template v-else>
      <div class="map-pattern" />
      <div class="map-river" />
      <div class="map-green green-one" />
      <div class="map-green green-two" />

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
      <p class="kakao-map-empty">{{ mapError || 'Kakao Maps JavaScript 키를 설정하면 실제 지도가 표시됩니다.' }}</p>
    </template>

    <button v-if="showResearchButton" class="map-research-button" type="button" @click="emit('search-current-map')">
      현재 지도에서 다시 검색
    </button>

    <div class="map-secondary-controls">
      <span class="map-result-count">{{ resultCount }}곳 표시</span>
      <button class="map-fullscreen-button" type="button" :aria-label="isFullscreen ? '전체화면 종료' : '지도 전체화면'" @click="toggleFullscreen">
        <svg v-if="!isFullscreen" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        <svg v-else viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M9 4v5H4M20 9h-5V4M15 20v-5h5M4 15h5v5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </button>
    </div>

    <button class="map-legend-toggle" type="button" :aria-expanded="legendOpen" @click="legendOpen = !legendOpen">
      범례
      <span aria-hidden="true">{{ legendOpen ? '−' : '+' }}</span>
    </button>

    <div v-if="legendOpen" class="map-color-legend map-color-legend--readable">
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
