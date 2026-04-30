<script setup>
import { ref, computed } from 'vue'
import { stepsData } from '@/data/landing.mock'
import { Card, SelectButton, Badge } from 'primevue'
const role = ref('client')
const steps = computed(() => stepsData[role.value])
const options = [
  { label: 'Для клиентов', value: 'client' },
  { label: 'Для психологов', value: 'specialist' },
]
</script>

<template>
  <section class="flex flex-col gap-8">
    <div class="flex flex-col md:flex-row justify-between items-center gap-6">
      <h2>Как это работает</h2>
      <SelectButton
        v-model="role"
        :options="options"
        option-label="label"
        option-value="value"
        :allow-empty="false"
      />
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
            <h3 class="md:text-left">{{ step.title }}</h3>
            <p class="max-md:text-center">{{ step.desc }}</p>
          </div>
        </template>
      </Card>
    </div>
  </section>
</template>
