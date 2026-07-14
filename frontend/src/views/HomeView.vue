<script setup>
import HeroSearch from '../components/HeroSearch.vue'
import CommunitySection from '../components/CommunitySection.vue'
import NearbySection from '../components/NearbySection.vue'
</script>

<template>
  <main>
    <HeroSearch />
    <div class="page-container">
      <CommunitySection />
    </div>
    <NearbySection />
  </main>
</template>
