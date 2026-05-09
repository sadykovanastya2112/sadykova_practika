<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { ProgressSpinner, Button, Card } from 'primevue'
import { apiCheckPaymentStatus } from '@/services/api.js'

const router = useRouter()
const status = ref('processing') // 'processing', 'success', 'error'
let pollInterval = null

async function pollStatus(paymentId) {
  try {
    const data = await apiCheckPaymentStatus(paymentId)

    if (data.status === 'succeeded') {
      status.value = 'success'
      clearInterval(pollInterval)
      localStorage.removeItem('last_payment_id') // Очищаем после успеха
    } else if (data.status === 'canceled') {
      status.value = 'error'
      clearInterval(pollInterval)
    }
    // Если status 'pending', продолжаем ждать следующего тика интервала
  } catch (e) {
    console.error('Ошибка при проверке статуса:', e)
  }
}

onMounted(() => {
  const paymentId = localStorage.getItem('last_payment_id')

  if (!paymentId) {
    // Если зашли на страницу просто так — отправляем в каталог
    router.push('/catalog')
    return
  }

  // Начинаем опрос каждые 3 секунды
  pollInterval = setInterval(() => pollStatus(paymentId), 3000)

  // На всякий случай останавливаем опрос через 5 минут (таймаут)
  setTimeout(() => {
    if (pollInterval) {
      clearInterval(pollInterval)
      if (status.value === 'processing') status.value = 'error'
    }
  }, 300000)
})

onBeforeUnmount(() => {
  if (pollInterval) clearInterval(pollInterval)
})
</script>

<template>
  <div class="flex items-center justify-center min-h-[60vh]">
    <Card class="w-full max-w-md text-center shadow-xl">
      <template #content>
        <div v-if="status === 'processing'" class="py-10">
          <ProgressSpinner class="mb-4" />
          <h2 class="text-2xl font-bold">Подтверждаем оплату...</h2>
          <p class="text-zinc-500">Это займет всего несколько секунд</p>
        </div>

        <div v-else-if="status === 'success'" class="py-10">
          <i class="pi pi-check-circle text-green-500 text-7xl mb-4"></i>
          <h2 class="text-2xl font-bold text-zinc-800">Оплата прошла успешно!</h2>
          <p class="mb-8">Запись подтверждена, ждем вас на сессии.</p>
          <Button
            label="К моим записям"
            icon="pi pi-calendar"
            @click="router.push('/client/appointments')"
            class="w-full"
          />
        </div>

        <div v-else class="py-10">
          <i class="pi pi-times-circle text-red-500 text-7xl mb-4"></i>
          <h2 class="text-2xl font-bold text-zinc-800">Ошибка оплаты</h2>
          <p class="mb-8">Не удалось подтвердить платеж или он был отменен.</p>
          <Button
            label="Вернуться в каталог"
            severity="secondary"
            @click="router.push('/catalog')"
            class="w-full"
          />
        </div>
      </template>
    </Card>
  </div>
</template>
