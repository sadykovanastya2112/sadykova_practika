<script setup>
import { ref, onMounted } from 'vue'
import { Card, Tag, Button, ProgressSpinner, Message } from 'primevue'
import { apiGetAppointments, apiGetMeetingLink } from '@/services/api.js'

const appointments = ref([])
const isLoading = ref(false)
const error = ref(null)

async function fetchAppointments() {
  isLoading.value = true
  try {
    appointments.value = await apiGetAppointments()
  } catch (e) {
    console.error('Ошибка загрузки записей:', e)
    error.value = 'Не удалось загрузить список записей'
  } finally {
    isLoading.value = false
  }
}

function continuePayment() {
  try {
    const payment_id = localStorage.getItem('last_payment_id')
    if (payment_id) {
      const confirmation_url = `https://yoomoney.ru/checkout/payments/v2/contract?orderId=${payment_id}`
      window.location.href = confirmation_url
    }
  } catch (e) {
    console.error(e)
    alert('Ссылка на встречу пока недоступна. Убедитесь, что сессия оплачена.')
  }
}

async function joinMeeting(id) {
  try {
    const { meeting_link } = await apiGetMeetingLink(id)
    window.open(meeting_link, '_blank')
  } catch (e) {
    console.error(e)
    alert('Ссылка на встречу пока недоступна. Убедитесь, что сессия оплачена.')
  }
}

function getStatusSeverity(label) {
  const l = label.toLowerCase()
  if (l.includes('оплачено') || l.includes('подтвержд')) return 'success'
  if (l.includes('ожидает') || l.includes('оплат')) return 'warn'
  if (l.includes('отмен')) return 'danger'
  return 'info'
}

function formatDate(dateStr) {
  return new Date(dateStr + 'Z').toLocaleString([], {
    day: 'numeric',
    month: 'long',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(fetchAppointments)
</script>

<template>
  <div class="container mx-auto p-4 max-w-6xl">
    <h1 class="text-3xl font-bold mb-8 text-zinc-800">Мои записи</h1>

    <div v-if="isLoading" class="flex justify-center py-20">
      <ProgressSpinner />
    </div>

    <Message v-else-if="error" severity="error" class="mb-4">{{ error }}</Message>

    <div
      v-else-if="appointments.length > 0"
      class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
    >
      <Card
        v-for="app in appointments"
        :key="app.appointment_id"
        class="shadow-sm border border-zinc-100 overflow-hidden"
      >
        <template #title>
          <div class="flex justify-between items-start gap-4">
            <span class="text-lg leading-tight">
              {{ app.specialist_first_name }} {{ app.specialist_last_name }}
            </span>
            <Tag :value="app.status_label" :severity="getStatusSeverity(app.status_label)" />
          </div>
        </template>

        <template #content>
          <div class="flex flex-col gap-3 text-zinc-600">
            <div class="flex items-center gap-2">
              <i class="pi pi-calendar text-primary"></i>
              <span>{{ formatDate(app.start_at) }}</span>
            </div>
            <div class="flex items-center gap-2">
              <i class="pi pi-wallet"></i>
              <span>{{ app.price }} ₽</span>
            </div>
          </div>
        </template>

        <template #footer>
          <div class="flex flex-col gap-2">
            <Button
              v-if="app.status_label.toLowerCase().includes('оплачено')"
              label="Войти в кабинет"
              icon="pi pi-video"
              class="w-full"
              @click="joinMeeting(app.appointment_id)"
            />

            <Button
              v-else-if="app.status_label.toLowerCase().includes('ожидает')"
              label="Оплатить сессию"
              icon="pi pi-credit-card"
              severity="warn"
              class="w-full"
              @click="continuePayment"
            />
          </div>
        </template>
      </Card>
    </div>

    <div
      v-else
      class="text-center py-20 bg-zinc-50 rounded-3xl border-2 border-dashed border-zinc-200"
    >
      <i class="pi pi-calendar-minus text-5xl text-zinc-300 mb-4"></i>
      <h2 class="text-xl font-semibold text-zinc-500">У вас пока нет записей</h2>
      <p class="text-zinc-400 mt-2 mb-6">Выберите специалиста в каталоге, чтобы начать работу.</p>
      <Button label="Перейти в каталог" icon="pi pi-search" @click="$router.push('/catalog')" />
    </div>
  </div>
</template>
