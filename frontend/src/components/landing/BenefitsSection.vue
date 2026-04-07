<script setup>
import { ref, computed } from 'vue'
import { benefitsData } from '@/data/landing.mock'
import { Tab, Tabs, TabList, SelectButton } from 'primevue'

const role = ref('client')
const benefits = computed(() => benefitsData[role.value])
const options = [
  { label: 'Для клиентов', value: 'client' },
  { label: 'Для психологов', value: 'specialist' },
]
</script>

<template>
  <section class="flex flex-col gap-10 bg-zinc-900 text-white p-8 md:p-16 rounded-[3rem]">
    <div class="flex flex-col md:flex-row justify-between gap-8">
      <h2 class="text-4xl font-bold max-w-md">Почему выбирают нас</h2>
      <SelectButton v-model="role" :options="options" option-label="label" option-value="value" />
    </div>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-8">
      <div v-for="(benefit, index) in benefits" :key="index" class="flex gap-6 group">
        <div
          class="shrink-0 w-14 h-14 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center group-hover:bg-teal-500 group-hover:text-black transition-all duration-300"
        >
          <i :class="benefit.icon" class="text-2xl"></i>
        </div>
        <div class="flex flex-col gap-2">
          <h3 class="text-xl font-bold">{{ benefit.title }}</h3>
          <p class="text-zinc-400 leading-relaxed">{{ benefit.desc }}</p>
        </div>
      </div>
    </div>
  </section>
</template>
