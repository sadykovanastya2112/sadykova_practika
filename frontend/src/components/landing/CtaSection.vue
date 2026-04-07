<script setup>
import { Button } from 'primevue'
</script>
<template>
  <section
    class="bg-linear-to-br from-teal-600 to-emerald-700 rounded-[3rem] p-12 text-center text-white flex flex-col gap-8 shadow-2xl overflow-hidden relative"
  >
    <div
      class="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full -mr-32 -mt-32 blur-3xl"
    ></div>
    <h2 class="text-4xl md:text-5xl font-extrabold">Готовы начать?</h2>
    <p class="text-xl opacity-90 max-w-xl mx-auto">
      Сделайте первый шаг к своему ментальному благополучию прямо сейчас.
    </p>
    <div class="flex flex-wrap justify-center gap-4">
      <Button label="Найти психолога" severity="contrast" class="px-10 py-4" />
      <Button label="Стать специалистом" outlined class="px-10 py-4 text-white border-white" />
    </div>
  </section>
</template>
