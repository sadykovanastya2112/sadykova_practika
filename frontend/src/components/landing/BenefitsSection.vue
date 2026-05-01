<script setup>
import { ref, computed } from 'vue'
import { benefitsData } from '@/data/landing.mock'
import { SelectButton, Badge } from 'primevue'

const role = ref('client')
const benefits = computed(() => benefitsData[role.value])
const options = [
  { label: 'Для клиентов', value: 'client' },
  { label: 'Для психологов', value: 'specialist' },
]
</script>

<template>
  <section class="flex flex-col gap-8">
    <div class="flex flex-col md:flex-row justify-between items-center gap-8">
      <h2>Почему выбирают нас</h2>
      <SelectButton
        v-model="role"
        :options="options"
        option-label="label"
        option-value="value"
        :allow-empty="false"
      />
    </div>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-8 p-8 bg-white rounded-4xl shadow-sm">
      <div v-for="(benefit, index) in benefits" :key="index" class="flex gap-6 group">
        <Badge size="xlarge">
          <i :class="benefit.icon"></i>
        </Badge>
        <div class="flex flex-col gap-2">
          <h3 class="text-left">{{ benefit.title }}</h3>
          <p>{{ benefit.desc }}</p>
        </div>
      </div>
    </div>
  </section>
</template>
