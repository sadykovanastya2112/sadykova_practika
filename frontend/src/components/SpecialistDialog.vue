<script setup>
import { Dialog, Button } from 'primevue'
import AppAvatar from './AppAvatar.vue'
import { pluralize } from '@/utils/pluralize'
import AppointmentDialog from './AppointmentDialog.vue'
import { ref } from 'vue'

defineProps({
  visible: Boolean,
  specialist: Object,
})

const emit = defineEmits(['update:visible'])

const isAppointmentVisible = ref(false)

function openBooking() {
  emit('update:visible', false) // Закрываем профиль
  isAppointmentVisible.value = true // Открываем запись
}
</script>

<template>
  <Dialog
    :visible="visible"
    @update:visible="emit('update:visible', $event)"
    header="Просмотр профиля специалиста"
    class="overflow-hidden w-11/12 max-w-2xl"
    :draggable="false"
    modal
    dismissableMask
  >
    <div class="flex flex-col gap-12 text-left">
      <section class="flex items-center gap-4 mt-6">
        <AppAvatar :src="specialist.photo_url" class="size-28 md:size-32" />
        <div>
          <h3>{{ specialist.first_name }} {{ specialist.last_name }}</h3>
          <p>{{ specialist.specialization }}</p>
          <small>
            Стаж:
            {{ specialist.experience_years }}
            {{ pluralize(specialist.experience_years) }}
          </small>
        </div>
      </section>

      <section class="space-y-6 mb-6">
        <div>
          <h4 class="w-full font-semibold text-left">Образование</h4>
          <p>{{ specialist.education }}</p>
        </div>
        <div>
          <h4 class="w-full font-semibold text-left">О специалисте</h4>
          <p>
            {{ specialist.bio }}
          </p>
        </div>
      </section>
    </div>
    <template #footer>
      <footer class="flex justify-between gap-8 items-center">
        <div>
          <small>Цена сессии</small>
          <p>{{ specialist.base_price }} ₽</p>
        </div>
        <Button label="Записаться" icon="pi pi-calendar-plus" class="px-8" @click="openBooking" />
      </footer>
    </template>
  </Dialog>
  <AppointmentDialog
    v-if="isAppointmentVisible"
    v-model:visible="isAppointmentVisible"
    :specialist="specialist"
  />
</template>
