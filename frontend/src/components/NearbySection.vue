<script setup>
import { onMounted, ref, watch } from 'vue'
import { searchRestrooms } from '../services/locationApi'
import RestroomMapPanel from './RestroomMapPanel.vue'
import NearbyRestroomCard from './NearbyRestroomCard.vue'

const FIXED_NEARBY_LOCATION = {
  label: '역삼역 멀티캠퍼스',
  keyword: '역삼역 멀티캠퍼스',
  latitude: 37.5012743,
  longitude: 127.039585,
}

const radius = ref(500)
const restrooms = ref([])
const loading = ref(false)
const initialized = ref(false)
const error = ref('')
const selectedRestroomId = ref(null)

const radiusOptions = [200, 500, 1000]
let requestSequence = 0

async function load() {
  const currentRequest = ++requestSequence
  loading.value = true
  error.value = ''

  try {
    const nextRestrooms = await searchRestrooms({
      keyword: FIXED_NEARBY_LOCATION.keyword,
      radius: radius.value,
    })

    // 사용자가 반경 버튼을 연속으로 눌렀을 때 가장 마지막 요청만 반영한다.
    if (currentRequest !== requestSequence) return

    // 기존 배열을 먼저 비우지 않고 새 결과가 준비된 뒤 한 번에 교체한다.
    restrooms.value = nextRestrooms
    initialized.value = true
  } catch (err) {
    if (currentRequest !== requestSequence) return
    error.value = err?.message || '주변 화장실을 불러오지 못했습니다.'
    initialized.value = true
  } finally {
    if (currentRequest === requestSequence) {
      loading.value = false
    }
  }
}

function changeRadius(option) {
  if (radius.value === option) return
  radius.value = option
  selectedRestroomId.value = null
}

function selectRestroom(restroomId) {
  selectedRestroomId.value = Number(restroomId)
}

watch(radius, load)
onMounted(load)
</script>

<template>
  <section class="nearby-section">
    <div class="content-section">
      <div class="section-heading radius-heading">
        <div>
          <h2>{{ radius === 1000 ? '1km' : `${radius}m` }} 내 주변 화장실</h2>
          <p>가까운 화장실의 청결도와 최근 후기를 확인하세요.</p>
        </div>

        <div class="nearby-heading-actions">
          <RouterLink
            v-if="restrooms.length"
            class="nearby-map-link"
            :to="{ name: 'search', query: { q: FIXED_NEARBY_LOCATION.keyword, radius, source: 'nearby' } }"
          >
            지도에서 {{ restrooms.length }}곳 보기
            <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
              <path
                d="m7 4 6 6-6 6"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </RouterLink>

          <div class="radius-buttons" aria-label="검색 반경">
            <button
              v-for="option in radiusOptions"
              :key="option"
              type="button"
              :class="{ active: radius === option }"
              :aria-pressed="radius === option"
              @click="changeRadius(option)"
            >
              {{ option === 1000 ? '1km' : `${option}m` }}
            </button>
          </div>
        </div>
      </div>

      <!-- 최초 진입 때만 로딩 문구를 표시한다. 반경 변경 때는 기존 지도와 목록을 유지한다. -->
      <p v-if="!initialized && loading" class="state-message">
        주변 화장실을 찾는 중입니다.
      </p>

      <template v-else>
        <p v-if="error" class="nearby-inline-error" role="alert">
          {{ error }} 기존 결과를 계속 표시합니다.
        </p>

        <div
          class="nearby-layout"
          :aria-busy="loading"
          aria-live="polite"
        >
          <RestroomMapPanel
            class="nearby-kakao-map"
            :restrooms="restrooms"
            :selected-id="selectedRestroomId"
            :anchor-location="FIXED_NEARBY_LOCATION"
            :show-research-button="false"
            :result-count="restrooms.length"
            @select="selectRestroom"
          />

          <div class="nearby-list nearby-home-list">
            <NearbyRestroomCard
              v-for="restroom in restrooms.slice(0, 3)"
              :key="restroom.id"
              :restroom="restroom"
              :radius="radius"
              :origin-keyword="FIXED_NEARBY_LOCATION.keyword"
              :selected="selectedRestroomId === Number(restroom.id)"
              @select="selectRestroom"
            />

            <p v-if="!restrooms.length && !error" class="state-message">
              현재 반경에 표시할 화장실이 없습니다.
            </p>
          </div>
        </div>
      </template>
    </div>
  </section>
</template>
