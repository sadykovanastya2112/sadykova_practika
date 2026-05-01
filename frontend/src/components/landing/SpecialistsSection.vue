<script setup>
import { apiGetSpecialists } from '@/services/specialists.api'
import SpecialistCard from '../SpecialistCard.vue'
import { Carousel } from 'primevue'
import { onMounted, ref } from 'vue'

const responsiveOptions = [
  { breakpoint: '1024px', numVisible: 2, numScroll: 1 },
  { breakpoint: '768px', numVisible: 1, numScroll: 1 },
]
const specialists = ref([])

onMounted(async () => {
  const data = await apiGetSpecialists()
  specialists.value = data.items
})
</script>

<template>
  <section class="flex flex-col gap-8">
    <h2>Наши психологи</h2>
    <Carousel
      :value="specialists"
      :numVisible="3"
      :numScroll="1"
      :responsiveOptions="responsiveOptions"
    >
      <template #item="slotProps">
        <SpecialistCard :specialist="slotProps.data" />
      </template>
    </Carousel>
  </section>
</template>
