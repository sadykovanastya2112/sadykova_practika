<script setup>
import { ref, computed } from 'vue'
import { stepsData } from '@/data/landing.mock'
import { Tabs, Tab, TabList, Card, SelectButton, Badge } from 'primevue'
const role = ref('client')
const steps = computed(() => stepsData[role.value])
const options = [
  { label: 'Для клиентов', value: 'client' },
  { label: 'Для психологов', value: 'specialist' },
]
</script>

<template>
  <section class="flex flex-col gap-10">
    <div class="flex flex-col md:flex-row md:items-end justify-between gap-6">
      <h2>Как это работает</h2>
      <SelectButton v-model="role" :options="options" option-label="label" option-value="value" />
    </div>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <Card v-for="step in steps" :key="step.id">
        <template #content>
          <div class="flex flex-col gap-4">
            <div class="flex items-center justify-between">
              <Badge size="xlarge">
                <i :class="step.icon" />
              </Badge>
              <span class="text-3xl font-black opacity-10">{{ step.id }}</span>
            </div>
            <h3 class="text-left">{{ step.title }}</h3>
            <p>{{ step.desc }}</p>
          </div>
        </template>
      </Card>
    </div>
  </section>
</template>
