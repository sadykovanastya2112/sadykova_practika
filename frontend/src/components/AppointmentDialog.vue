<script setup>
import { ref, onMounted } from 'vue'
import { Dialog, Button, Select, Message } from 'primevue'
import { apiGetAvailableSlots, apiCreateAppointment, apiCreatePayment } from '@/services/api.js'

const props = defineProps({
  visible: Boolean,
  specialist: Object,
})

const emit = defineEmits(['update:visible'])

const slots = ref([])
const selectedSlot = ref(null)
const isLoading = ref(false)
const isSubmitting = ref(false)
const error = ref('')

async function loadSlots() {
  isLoading.value = true
  try {
    slots.value = await apiGetAvailableSlots(props.specialist.id)
  } catch (e) {
    console.error(e)
    error.value = 'Не удалось загрузить доступное время'
  } finally {
    isLoading.value = false
  }
}

async function handleBooking() {
  if (!selectedSlot.value) return

  isSubmitting.value = true
  try {
    // 1. Создаем бронь
    const appointment = await apiCreateAppointment(selectedSlot.value.id, props.specialist.id)

    // 2. Создаем платеж
    const payment = await apiCreatePayment(appointment.appointment_id)

    // 3. Редирект на ЮKassa
    if (payment.confirmation_url) {
      // Сохраняем payment_id в localStorage, чтобы проверить статус на callback-странице
      localStorage.setItem('last_payment_id', payment.payment_id)
      window.location.href = payment.confirmation_url
    }
  } catch (e) {
    console.error(e)
    error.value = 'Ошибка при создании записи. Возможно, слот уже занят.'
    isSubmitting.value = false
  }
}

// Форматирование даты: "12 мая"
function formatDate(dateStr) {
  return new Date(dateStr + 'Z').toLocaleDateString([], { day: 'numeric', month: 'long' })
}

// Форматирование времени: "14:00"
function formatTime(dateStr) {
  return new Date(dateStr + 'Z').toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

onMounted(loadSlots)
</script>

<template>
  <Dialog
    :visible="visible"
    @update:visible="emit('update:visible', $event)"
    header="Запись на сессию"
    modal
    :draggable="false"
    dismissableMask
    class="w-11/12 max-w-md"
  >
    <div class="flex flex-col gap-6 py-4">
      <div v-if="isLoading" class="text-center py-4">
        <i class="pi pi-spin pi-spinner text-2xl"></i>
      </div>

      <div v-else-if="slots.length > 0" class="flex flex-col gap-4">
        <div class="flex flex-col gap-2">
          <label class="font-semibold text-sm">Выберите удобное время</label>
          <Select
            v-model="selectedSlot"
            :options="slots"
            placeholder="Выберите слот"
            class="w-full"
          >
            <template #option="slotProps">
              <div class="flex flex-col w-full border-b border-zinc-100 pb-1">
                <div class="flex justify-between items-center mb-1">
                  <span class="font-bold text-zinc-800">
                    {{ formatDate(slotProps.option.start_at) }}
                  </span>
                  <span class="text-primary font-semibold"> {{ slotProps.option.price }} ₽ </span>
                </div>
                <div class="text-sm text-zinc-500">
                  <i class="pi pi-clock mr-1 text-[10px]"></i>
                  {{ formatTime(slotProps.option.start_at) }} —
                  {{ formatTime(slotProps.option.end_at) }}
                </div>
              </div>
            </template>

            <template #value="slotProps">
              <div v-if="slotProps.value" class="flex justify-between items-center w-full pr-4">
                <span>
                  {{ formatDate(slotProps.value.start_at) }},
                  {{ formatTime(slotProps.value.start_at) }}
                </span>
                <span class="font-bold">{{ slotProps.value.price }} ₽</span>
              </div>
              <span v-else>{{ slotProps.placeholder }}</span>
            </template>
          </Select>
        </div>

        <Message v-if="error" severity="error" variant="simple">{{ error }}</Message>
      </div>

      <div v-else class="text-center text-zinc-500 py-2">
        <p>У специалиста нет свободных слотов на ближайшее время.</p>
      </div>
    </div>

    <template #footer>
      <div class="flex justify-end gap-2">
        <Button label="Отмена" severity="secondary" text @click="emit('update:visible', false)" />
        <Button
          label="Перейти к оплате"
          icon="pi pi-credit-card"
          :loading="isSubmitting"
          :disabled="!selectedSlot"
          @click="handleBooking"
        />
      </div>
    </template>
  </Dialog>
</template>

<style scoped>
/* Убираем лишние отступы у Select, чтобы кастомный шаблон выглядел чище */
:deep(.p-select-option) {
  padding: 0.75rem 1rem !important;
}
</style>
