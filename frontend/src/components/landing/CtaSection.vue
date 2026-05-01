<script setup>
import { Button } from 'primevue'
</script>
<template>
  <section
    class="bg-emerald-500 rounded-4xl p-8 flex flex-col gap-8 shadow-2xl overflow-hidden relative"
  >
    <h2 class="text-white">Готовы начать?</h2>
    <p class="text-zinc-50">Сделайте первый шаг к своему ментальному благополучию прямо сейчас.</p>
    <div class="flex flex-wrap justify-center gap-4">
      <Button label="Найти психолога" severity="contrast" class="px-10 py-4" />
      <Button label="Стать специалистом" outlined class="px-10 py-4 text-white border-white" />
    </div>
  </section>
</template>
