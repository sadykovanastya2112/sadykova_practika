<script setup>
import { ref } from 'vue'
import { Button, Card, useToast } from 'primevue'
import SpecialistDialog from './SpecialistDialog.vue'
import { apiGetSpecialistProfile } from '@/services/specialists.api'
import AppAvatar from './AppAvatar.vue'

const props = defineProps({
  specialist: { type: Object, required: true },
})

const toast = useToast()
const fullProfile = ref(null)
const isDialogVisible = ref(false)
const isFetching = ref(false)

async function handleOpenProfile() {
  isFetching.value = true
  try {
    const data = await apiGetSpecialistProfile(props.specialist.id)
    fullProfile.value = data
    isDialogVisible.value = true
  } catch (e) {
    console.error(`Failed to fetch profile for id ${props.specialist.id}`, e)
    toast.add({
      severity: 'error',
      summary: 'Ошибка',
      detail: 'Не удалось загрузить профиль',
      life: 5000,
    })
  } finally {
    isFetching.value = false
  }
}
</script>

<template>
  <div class="p-2 h-full">
    <Card class="h-full">
      <template #content>
        <div class="flex flex-col gap-5 items-center text-center">
          <AppAvatar :src="specialist.photo_url" class="size-28 md:size-32" />
          <div>
            <h3 class="text-xl font-semibold">
              {{ specialist.first_name }} {{ specialist.last_name }}
            </h3>
            <small>{{ specialist.specialization }}</small>
          </div>
          <Button
            label="Посмотреть профиль"
            :loading="isFetching"
            @click="handleOpenProfile"
            fluid
          />
        </div>
      </template>
    </Card>
    <SpecialistDialog
      v-if="fullProfile"
      v-model:visible="isDialogVisible"
      :specialist="fullProfile"
    />
  </div>
</template>
