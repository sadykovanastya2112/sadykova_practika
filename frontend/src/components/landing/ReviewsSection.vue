<script setup>
import { reviewsData } from '@/data/landing.mock'
import { Card, Rating } from 'primevue'
</script>

<template>
  <section class="flex flex-col gap-8">
    <h2>Отзывы</h2>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <Card v-for="(review, index) in reviewsData" :key="index">
        <template #content>
          <div class="flex flex-col gap-6 h-full">
            <div class="text-emerald-500">
              <i class="pi pi-pinterest text-9xl opacity-20"></i>
            </div>
            <p class="italic">"{{ review.quote }}"</p>
            <div
              class="flex items-center justify-between border-t border-zinc-200 dark:border-zinc-800 pt-4"
            >
              <small>{{ review.author }}</small>
              <Rating :modelValue="Number(review.stars)" readonly :cancel="false" />
            </div>
          </div>
        </template>
      </Card>
    </div>
  </section>
</template>
