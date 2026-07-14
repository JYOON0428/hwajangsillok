<script setup>
import AppHeader from './components/AppHeader.vue'
import ChatbotFloating from './components/ChatbotFloating.vue'
</script>

<template>
  <div class="app-shell">
    <AppHeader />
    <RouterView />
    <ChatbotFloating />
  </div>
</template>
