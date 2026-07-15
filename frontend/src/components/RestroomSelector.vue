<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { searchRestrooms } from '../services/locationApi'

const props = defineProps({
  modelValue: { type: Object, default: null },
  error: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue'])

const keyword = ref('')
const results = ref([])
const loading = ref(false)
const opened = ref(!props.modelValue)
const searchInput = ref(null)
let debounceTimer = null

const hasQuery = computed(() => keyword.value.trim().length > 0)

async function runSearch() {
  const query = keyword.value.trim()
  if (!query) {
    results.value = []
    return
  }
  loading.value = true
  try {
    results.value = (await searchRestrooms({ keyword: query, radius: 2000, sort: 'distance' })).slice(0, 8)
  } finally {
    loading.value = false
  }
}

function onInput() {
  window.clearTimeout(debounceTimer)
  debounceTimer = window.setTimeout(runSearch, 250)
}
function selectRestroom(restroom) {
  emit('update:modelValue', restroom)
  keyword.value = ''
  results.value = []
  opened.value = false
}
async function changeSelection() {
  opened.value = true
  await nextTick()
  searchInput.value?.focus()
}
function clearSelection() {
  emit('update:modelValue', null)
  opened.value = true
}

watch(() => props.modelValue, (value) => {
  if (value) opened.value = false
})
</script>

<template>
  <section class="restroom-selector" :class="{ 'has-field-error': error }" data-field="restroom">
    <div class="form-label-row">
      <label>관련 화장실 <span class="required-mark">필수</span></label>
    </div>

    <div v-if="modelValue && !opened" class="selected-restroom-card">
      <div class="selected-restroom-icon" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none"><path d="M12 21s7-5.1 7-12a7 7 0 1 0-14 0c0 6.9 7 12 7 12Z" stroke="currentColor" stroke-width="1.8"/><circle cx="12" cy="9" r="2.4" stroke="currentColor" stroke-width="1.8"/></svg>
      </div>
      <div>
        <span>선택된 화장실</span>
        <strong>{{ modelValue.name }}</strong>
        <p>{{ modelValue.address }}</p>
      </div>
      <button type="button" @click="changeSelection">변경</button>
    </div>

    <div v-else class="restroom-search-box">
      <div class="restroom-search-row">
        <div class="restroom-search-input">
          <svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="11" cy="11" r="7" stroke="currentColor" stroke-width="2"/><path d="m16.5 16.5 4 4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          <input
            ref="searchInput"
            v-model="keyword"
            type="search"
            placeholder="화장실명, 역명, 주소로 검색"
            @input="onInput"
            @keydown.enter.prevent="runSearch"
          />
        </div>
        <button type="button" class="restroom-search-button" @click="runSearch">검색</button>
        <button v-if="modelValue" type="button" class="restroom-cancel-change" @click="opened = false">취소</button>
      </div>

      <p v-if="loading" class="restroom-search-state">검색 중입니다.</p>
      <p v-else-if="hasQuery && !results.length" class="restroom-search-state">검색 결과가 없습니다.</p>
      <div v-else-if="results.length" class="restroom-search-results">
        <button
          v-for="restroom in results"
          :key="restroom.id"
          type="button"
          @click="selectRestroom(restroom)"
        >
          <span><strong>{{ restroom.name }}</strong><small>{{ restroom.address }}</small></span>
          <em>{{ restroom.distanceMeters }}m</em>
        </button>
      </div>
    </div>
    <p v-if="error" class="field-error">{{ error }}</p>
  </section>
</template>
