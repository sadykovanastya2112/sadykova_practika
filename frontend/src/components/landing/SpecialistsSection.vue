<script setup>
import { apiGetSpecialists } from '@/services/specialists.api'
import { Card, Carousel, Badge, Chip } from 'primevue'
import { onMounted, ref } from 'vue'

const responsiveOptions = [
  { breakpoint: '1024px', numVisible: 2, numScroll: 1 },
  { breakpoint: '768px', numVisible: 1, numScroll: 1 },
]
const specialists = ref([])

onMounted(async () => {
  specialists.value = await apiGetSpecialists()
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
        <div class="p-2 h-full">
          <Card class="h-full">
            <template #content>
              <div class="flex flex-col gap-5 items-center text-center">
                <img :src="slotProps.data.avatarUrl" class="size-28 md:size-32 rounded-full" />
                <div class="flex-col md:flex-row content-between">
                  <Chip label="Документы проверены" icon="pi pi-file-check" />
                  <Chip label="Опыт 10+ лет" icon="pi pi-verified" />
                </div>
                <div>
                  <h3>
                    {{ slotProps.data.displayName }}
                  </h3>
                  <small>
                    {{ slotProps.data.specialization }}
                  </small>
                </div>
                <div
                  class="w-full pt-4 border-t border-zinc-100 dark:border-zinc-800 flex justify-between items-center"
                >
                  <span class="text-zinc-500 text-sm">от {{ slotProps.data.minPrice }} ₽</span>
                  <Badge
                    :severity="slotProps.data.isOnline ? 'success' : 'secondary'"
                    :value="slotProps.data.isOnline ? 'В сети' : 'Офлайн'"
                  />
                </div>
              </div>
            </template>
          </Card>
        </div>
      </template>
    </Carousel>
  </section>
</template>
