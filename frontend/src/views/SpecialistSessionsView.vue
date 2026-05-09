<script setup>
import { ref, onMounted } from 'vue'
import { Card, Tag, Button, ProgressSpinner, Message } from 'primevue'
import { apiGetSpecialistAppointments, apiGetMeetingLink } from '@/services/api.js'
import AppAvatar from '@/components/AppAvatar.vue'

const appointments = ref([])
const isLoading = ref(false)
const error = ref(null)

async function fetchAppointments() {
  isLoading.value = true
  try {
    appointments.value = await apiGetSpecialistAppointments()
  } catch (e) {
    console.error('Ошибка загрузки записей:', e)
    error.value = 'Не удалось загрузить список сессий'
  } finally {
    isLoading.value = false
  }
}

async function joinMeeting(id) {
  try {
    const { meeting_link } = await apiGetMeetingLink(id)
    window.open(meeting_link, '_blank')
  } catch (e) {
    console.error(e)
    alert('Кабинет пока недоступен. Проверьте статус оплаты сессии.')
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
  return new Date(dateStr).toLocaleString('ru-RU', {
    day: 'numeric',
    month: 'long',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function calculateDuration(start, end) {
  if (!start || !end) return '—'
  const diffMs = new Date(end) - new Date(start)
  const minutes = Math.round(diffMs / 60000)
  return `${minutes} мин.`
}

onMounted(fetchAppointments)
</script>

<template>
  <div class="container mx-auto p-4 max-w-6xl">
    <h1 class="text-3xl font-bold mb-8 text-zinc-800">Сессии с клиентами</h1>

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
        class="shadow-sm border border-zinc-100"
      >
        <template #title>
          <div class="flex items-center gap-4 mb-2">
            <AppAvatar :src="app.client_avatar" class="size-12" />
            <div class="flex flex-col flex-1 overflow-hidden">
              <span class="text-lg font-bold truncate">{{ app.client_name }}</span>
              <Tag
                :value="app.status_label"
                :severity="getStatusSeverity(app.status_label)"
                class="w-fit text-[10px] px-2 py-0"
              />
            </div>
          </div>
        </template>

        <template #content>
          <div class="flex flex-col gap-3 text-zinc-600 mt-2">
            <div class="flex items-center gap-2">
              <i class="pi pi-calendar text-primary"></i>
              <span class="text-sm">{{ formatDate(app.start_at) }}</span>
            </div>
            <div class="flex items-center gap-2">
              <i class="pi pi-clock"></i>
              <span>Длительность: {{ calculateDuration(app.start_at, app.end_at) }}</span>
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
              label="Начать сессию"
              icon="pi pi-video"
              class="w-full"
              @click="joinMeeting(app.appointment_id)"
            />
            <Button v-else label="Ожидание оплаты" icon="pi pi-lock" disabled text class="w-full" />
          </div>
        </template>
      </Card>
    </div>

    <div
      v-else
      class="text-center py-20 bg-zinc-50 rounded-3xl border-2 border-dashed border-zinc-200"
    >
      <i class="pi pi-users text-5xl text-zinc-300 mb-4"></i>
      <h2 class="text-xl font-semibold text-zinc-500">У вас пока нет активных записей</h2>
      <p class="text-zinc-400 mt-2">
        Когда клиенты запишутся на ваши свободные слоты, они появятся здесь.
      </p>
    </div>
  </div>
</template>
