<script setup>
import { Button } from 'primevue'
import { login } from '@/services/auth'
</script>
<template>
  <section
    class="bg-emerald-500 rounded-4xl p-8 flex flex-col gap-8 shadow-2xl overflow-hidden relative"
  >
    <h2 class="text-white">Готовы начать?</h2>
    <p class="text-zinc-50">Сделайте первый шаг к своему ментальному благополучию прямо сейчас.</p>
    <div class="flex flex-wrap justify-center gap-4">
      <Button asChild v-slot="slotProps" severity="contrast">
        <RouterLink to="/catalog" :class="slotProps.class">Найти психолога</RouterLink>
      </Button>
      <Button label="Стать участником" @click="login" severity="secondary" />
    </div>
  </section>
</template>
