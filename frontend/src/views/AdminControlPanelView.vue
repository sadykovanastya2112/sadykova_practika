<script setup>
import { ref, onMounted } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import { useToast } from 'primevue/usetoast'
import { apiGetPendingSpecialists, apiModerateSpecialist } from '@/services/api.js'

const toast = useToast()
const specialists = ref([])
const totalRecords = ref(0)
const loading = ref(false)
const expandedRows = ref([]) // Для раскрытия строк с деталями
const rejectionReasons = ref({}) // Храним текст отказа для каждого ID отдельно

const loadData = async (event = { page: 0, rows: 10 }) => {
  loading.value = true
  try {
    const data = await apiGetPendingSpecialists(event.page + 1, event.rows)
    specialists.value = data.items
    totalRecords.value = data.total
  } catch (err) {
    console.error(err)
    toast.add({ severity: 'error', summary: 'Ошибка', detail: 'Не удалось загрузить данные' })
  } finally {
    loading.value = false
  }
}

const handleAction = async (id, action) => {
  const reason = rejectionReasons.value[id]
  if (action === 'reject' && !reason) {
    toast.add({ severity: 'warn', summary: 'Внимание', detail: 'Укажите причину отказа' })
    return
  }

  try {
    await apiModerateSpecialist(id, action, reason)
    toast.add({
      severity: 'success',
      summary: 'Готово',
      detail: `Специалист ${action === 'approve' ? 'одобрен' : 'отклонен'}`,
    })
    // Удаляем из списка локально, чтобы не делать лишний запрос
    specialists.value = specialists.value.filter((s) => s.id !== id)
    totalRecords.value--
  } catch (err) {
    console.error(err)
    toast.add({ severity: 'error', summary: 'Ошибка', detail: 'Действие не выполнено' })
  }
}

onMounted(() => loadData())
</script>

<template>
  <div class="card p-4">
    <h2 class="mb-4">Верификация специалистов</h2>

    <DataTable
      v-model:expandedRows="expandedRows"
      :value="specialists"
      lazy
      paginator
      :rows="10"
      :totalRecords="totalRecords"
      :loading="loading"
      @page="loadData($event)"
      dataKey="id"
      class="p-datatable-sm"
    >
      <!-- Колонка для развертывания -->
      <Column expander style="width: 3rem" />

      <Column field="full_name" header="Имя специалиста">
        <template #body="{ data }">
          <div class="flex items-center gap-2">
            <img
              :src="data.photo_url || '/default-avatar.png'"
              class="size-8 rounded-full object-cover"
            />
            <span>{{ data.full_name }}</span>
          </div>
        </template>
      </Column>

      <Column field="specialization" header="Специализация" />

      <Column field="created_at" header="Дата заявки">
        <template #body="{ data }">
          {{ new Date(data.created_at).toLocaleDateString() }}
        </template>
      </Column>

      <!-- Содержимое при раскрытии строки -->
      <template #expansion="{ data }">
        <div class="p-3 border-round bg-gray-50 flex flex-col gap-3">
          <div><strong>Образование:</strong> {{ data.education }}</div>
          <div><strong>Опыт:</strong> {{ data.experience_years }} лет</div>
          <div><strong>О себе:</strong> {{ data.bio }}</div>
          <hr />
          <div class="flex items-center gap-3">
            <div class="grow">
              <InputText
                v-model="rejectionReasons[data.id]"
                placeholder="Причина отказа (обязательно для отклонения)"
                class="w-full"
              />
            </div>
            <Button
              label="Одобрить"
              icon="pi pi-check"
              severity="success"
              @click="handleAction(data.id, 'approve')"
            />
            <Button
              label="Отклонить"
              icon="pi pi-times"
              severity="danger"
              @click="handleAction(data.id, 'reject')"
            />
          </div>
        </div>
      </template>
    </DataTable>
  </div>
</template>

<style scoped>
/* У PrimeVue DataTable свои стили, здесь можно добавить отступы */
.p-datatable-sm {
  font-size: 0.9rem;
}
</style>
