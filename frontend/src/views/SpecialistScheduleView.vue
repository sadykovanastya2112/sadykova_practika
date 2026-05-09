<script setup>
import { ref, onMounted } from 'vue'
import DatePicker from 'primevue/datepicker'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import InputNumber from 'primevue/inputnumber'
import { useToast } from 'primevue/usetoast'
import { apiGetSlots, apiCreateSlots, apiDeleteSlot } from '@/services/api'

const toast = useToast()
const slots = ref([])
const loading = ref(false)

// Состояние для создания новых слотов
const selectedDates = ref([]) // Массив дат из календаря
const startTime = ref(null) // Время начала (Date object)
const endTime = ref(null) // Время конца (Date object)
const slotPrice = ref(null) // Индивидуальная цена (опционально)

const fetchSlots = async () => {
  loading.value = true
  try {
    const data = await apiGetSlots()
    slots.value = Array.isArray(data) ? data : []
  } finally {
    loading.value = false
  }
}

const createBulkSlots = async () => {
  if (!selectedDates.value.length || !startTime.value || !endTime.value) {
    toast.add({ severity: 'warn', summary: 'Ошибка', detail: 'Заполните даты и время' })
    return
  }

  // Формируем массив слотов для отправки
  const newSlots = selectedDates.value.map((date) => {
    const start = new Date(date)
    start.setHours(startTime.value.getHours(), startTime.value.getMinutes())

    const end = new Date(date)
    end.setHours(endTime.value.getHours(), endTime.value.getMinutes())

    return {
      start_at: start.toISOString(),
      end_at: end.toISOString(),
      price: slotPrice.value,
    }
  })

  try {
    await apiCreateSlots(newSlots)
    toast.add({ severity: 'success', summary: 'Успех', detail: 'Слоты созданы' })
    selectedDates.value = [] // Очистить выбор
    fetchSlots() // Обновить список
  } catch (err) {
    toast.add({
      severity: 'error',
      summary: 'Ошибка',
      detail: err.response?.data?.error || 'Конфликт времени',
    })
  }
}

const deleteSlot = async (id) => {
  try {
    await apiDeleteSlot(id)
    slots.value = slots.value.filter((s) => s.id !== id)
    toast.add({ severity: 'info', summary: 'Удалено', detail: 'Слот удален' })
  } catch (err) {
    console.error(err)
    toast.add({
      severity: 'error',
      summary: 'Ошибка',
      detail: 'Нельзя удалить забронированный слот',
    })
  }
}

onMounted(fetchSlots)
</script>

<template>
  <div class="grid p-4 gap-4">
    <!-- Левая колонка: Создание -->
    <div class="col-12 md:col-4 flex flex-col gap-4 p-4 border rounded-lg bg-gray-50">
      <h3 class="font-bold m-0">Создать слоты</h3>

      <div class="flex flex-col gap-1">
        <label>Выберите дни</label>
        <DatePicker
          v-model="selectedDates"
          selectionMode="multiple"
          :minDate="new Date()"
          inline
          class="w-full"
        />
      </div>

      <div class="flex gap-2">
        <div class="flex flex-col gap-1 w-full">
          <label>Начало</label>
          <DatePicker v-model="startTime" timeOnly hourFormat="24" />
        </div>
        <div class="flex flex-col gap-1 w-full">
          <label>Конец</label>
          <DatePicker v-model="endTime" timeOnly hourFormat="24" />
        </div>
      </div>

      <div class="flex flex-col gap-1">
        <label>Цена (оставьте пустым для базовой)</label>
        <InputNumber v-model="slotPrice" mode="currency" currency="RUB" locale="ru-RU" />
      </div>

      <Button label="Создать серию слотов" icon="pi pi-plus" @click="createBulkSlots" />
    </div>

    <!-- Правая колонка: Список -->
    <div class="col-12 md:col-8">
      <DataTable
        :value="slots"
        :loading="loading"
        paginator
        :rows="10"
        sortField="start_at"
        :sortOrder="1"
      >
        <Column header="Дата">
          <template #body="{ data }">
            {{ new Date(data.start_at + 'Z').toLocaleDateString() }}
          </template>
        </Column>
        <Column header="Время">
          <template #body="{ data }">
            {{
              new Date(data.start_at + 'Z').toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
              })
            }}
            -
            {{
              new Date(data.end_at + 'Z').toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
              })
            }}
          </template>
        </Column>
        <Column field="price" header="Цена" />
        <Column style="width: 3rem">
          <template #body="{ data }">
            <Button icon="pi pi-trash" severity="danger" text @click="deleteSlot(data.id)" />
          </template>
        </Column>
      </DataTable>
    </div>
  </div>
</template>
