<script setup>
import TheFooter from '@/components/TheFooter.vue'
import TheHeader from '@/components/TheHeader.vue'
import { RouterView } from 'vue-router'
import { ScrollTop, Toast } from 'primevue'
</script>

<template>
  <div class="min-h-screen min-w-xs flex flex-col">
    <TheHeader />
    <main
      class="flex-1 w-full max-w-md md:max-w-5xl mx-auto flex flex-col px-4 md:px-8 py-6 md:py-12 gap-y-24 md:gap-y-32 overflow-hidden"
    >
      <router-view />
    </main>
    <footer>
      <TheFooter />
    </footer>
  </div>
  <Toast />
  <ScrollTop />
</template>
