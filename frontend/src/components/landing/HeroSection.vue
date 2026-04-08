<script setup>
import { Button } from 'primevue'
</script>

<template>
  <section class="flex flex-col gap-6 md:gap-10">
    <div class="w-full max-w-xl mx-auto px-6 text-emerald-500">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 120">
        <path
          d="M10 60C30 30 70 90 100 60C130 30 170 90 200 60C230 30 270 90 300 60C330 30 370 90 390 60"
          stroke="currentColor"
          stroke-width="6"
          fill="none"
          stroke-linecap="round"
        />
      </svg>
    </div>
    <div class="w-full flex flex-col gap-6 md:gap-8">
      <h1>
        Онлайн-консультации с
        <span class="text-emerald-500">профессионалами</span>
      </h1>
      <h4>
        Получите поддержку, когда она вам нужна, не выходя из дома. Безопасно. Анонимно. Мы поможем
        распутать клубок мыслей и найти путь к спокойствию.
      </h4>
      <div class="w-full flex max-md:flex-col justify-center gap-4 mt-6">
        <Button label="Найти психолога" />
        <Button label="Стать специалистом" outlined />
      </div>
    </div>
  </section>
</template>
