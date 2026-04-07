<script setup>
import { apiGetSpecialists } from '@/services/specialists.api'
import { Card, Carousel, Avatar, Badge } from 'primevue'
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
    <h2 class="text-4xl font-bold dark:text-white text-center md:text-left">Наши психологи</h2>
    <Carousel
      :value="specialists"
      :numVisible="3"
      :numScroll="1"
      :responsiveOptions="responsiveOptions"
    >
      <template #item="slotProps">
        <div class="p-2 h-full">
          <Card
            class="h-full border-none bg-white dark:bg-zinc-900/40 backdrop-blur-md border border-zinc-200 dark:border-zinc-800 shadow-xl"
          >
            <template #content>
              <div class="flex flex-col gap-5 items-center text-center">
                <Avatar
                  :image="slotProps.data.avatarUrl"
                  size="xlarge"
                  shape="circle"
                  class="ring-4 ring-teal-500/20"
                />
                <div>
                  <h3 class="text-xl font-bold dark:text-white">
                    {{ slotProps.data.displayName }}
                  </h3>
                  <p class="text-teal-500 font-medium text-sm">
                    {{ slotProps.data.specialization }}
                  </p>
                </div>
                <div
                  class="flex items-center gap-2 bg-zinc-100 dark:bg-zinc-800 px-3 py-1 rounded-full"
                >
                  <i class="pi pi-star-fill text-yellow-500 text-xs"></i>
                  <span class="text-sm font-bold">{{ slotProps.data.rating }}</span>
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
