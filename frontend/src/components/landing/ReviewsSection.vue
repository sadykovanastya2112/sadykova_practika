<script setup>
import { reviewsData } from '@/data/landing.mock'
import { Card, Rating } from 'primevue'
</script>

<template>
  <section class="flex flex-col gap-8">
    <h2 class="text-4xl font-bold dark:text-white">Отзывы</h2>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <Card
        v-for="(review, index) in reviewsData"
        :key="index"
        class="bg-zinc-50 dark:bg-zinc-900/20 border-none"
      >
        <template #content>
          <div class="flex flex-col gap-6 h-full">
            <div class="text-teal-500"><i class="pi pi-quote-right text-3xl opacity-20"></i></div>
            <p class="italic text-lg dark:text-zinc-300 grow">"{{ review.quote }}"</p>
            <div
              class="flex items-center justify-between border-t border-zinc-200 dark:border-zinc-800 pt-4"
            >
              <span class="font-bold dark:text-white">{{ review.author }}</span>
              <Rating :modelValue="Number(review.stars)" readonly :cancel="false" />
            </div>
          </div>
        </template>
      </Card>
    </div>
  </section>
</template>
