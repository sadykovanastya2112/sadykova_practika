<script setup>
import TheFooter from '@/components/TheFooter.vue'
import TheHeader from '@/components/TheHeader.vue'
import { RouterView } from 'vue-router'
</script>

<template>
  <header>
    <TheHeader />
  </header>
  <RouterView />
  <footer>
    <TheFooter />
  </footer>
</template>
