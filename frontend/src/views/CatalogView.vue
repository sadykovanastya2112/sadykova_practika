<script setup>
import { ref, onMounted, watch } from 'vue'
import { Button, Select, InputText, InputNumber, DataView, Paginator, Menubar } from 'primevue'
import { apiGetSpecialists } from '@/services/specialists.api'
import SpecialistCard from '@/components/SpecialistCard.vue'

const specialists = ref([])
const totalRecords = ref(0)
const isLoading = ref(false)

const filters = ref({
  page: 1,
  per_page: 12, // Дефолтное кол-во
  specialization: '',
  min_price: null,
  max_price: null,
  min_experience: null,
  sort_by: 'id',
  sort_order: 'asc',
})

const sortOptions = [
  { label: 'По умолчанию', value: 'id' },
  { label: 'Цена (дешевле)', value: 'price_asc' },
  { label: 'Цена (дороже)', value: 'price_desc' },
  { label: 'Опыт (больше)', value: 'experience_desc' },
  { label: 'Имя (А-Я)', value: 'name_asc' },
]

const selectedSort = ref(sortOptions[0])
const rowsPerPageOptions = [12, 24, 48]

async function fetchSpecialists() {
  isLoading.value = true
  try {
    const params = { ...filters.value }
    if (selectedSort.value.value.includes('_')) {
      const [by, order] = selectedSort.value.value.split('_')
      params.sort_by = by
      params.sort_order = order
    }

    const data = await apiGetSpecialists(params)
    // Твой api.js теперь возвращает корректную структуру {items, total}
    specialists.value = data.items
    totalRecords.value = data.total
  } catch (e) {
    console.error('Ошибка при загрузке каталога:', e)
  } finally {
    isLoading.value = false
  }
}

function resetFilters() {
  filters.value = {
    ...filters.value,
    specialization: '',
    min_price: null,
    max_price: null,
    min_experience: null,
    page: 1,
  }
  fetchSpecialists()
}

// Следим за сортировкой и сменой страницы
watch([selectedSort, () => filters.value.page, () => filters.value.per_page], () => {
  fetchSpecialists()
})

function onPageChange(event) {
  filters.value.page = event.page + 1
  filters.value.per_page = event.rows // Обновляем кол-во записей
}

function handleFilter() {
  filters.value.page = 1
  fetchSpecialists()
}

onMounted(() => {
  fetchSpecialists()
})
</script>

<template>
  <div class="container mx-auto p-4">
    <h1 class="text-3xl font-bold mb-6 text-zinc-800">Каталог психологов</h1>

    <!-- Панель фильтров в Menubar -->
    <Menubar breakpoint="48rem" class="mb-8 border-none bg-white shadow-sm p-4 rounded-xl">
      <template #start>
        <div class="flex flex-wrap items-center gap-4">
          <!-- Специализация -->
          <div class="flex flex-col gap-1">
            <label class="text-[10px] font-bold uppercase text-zinc-400 ml-1">Специализация</label>
            <InputText
              v-model="filters.specialization"
              placeholder="Напр: КПТ"
              class="p-inputtext-sm w-40"
              @keyup.enter="handleFilter"
            />
          </div>

          <!-- Цена -->
          <div class="flex flex-col gap-1">
            <label class="text-[10px] font-bold uppercase text-zinc-400 ml-1">Цена (от — до)</label>
            <div class="flex items-center gap-1">
              <InputNumber
                v-model="filters.min_price"
                placeholder="от"
                class="p-inputtext-sm w-24"
              />
              <InputNumber
                v-model="filters.max_price"
                placeholder="до"
                class="p-inputtext-sm w-24"
              />
            </div>
          </div>

          <!-- Опыт -->
          <div class="flex flex-col gap-1">
            <label class="text-[10px] font-bold uppercase text-zinc-400 ml-1">Опыт (лет)</label>
            <InputNumber
              v-model="filters.min_experience"
              placeholder="0"
              class="p-inputtext-sm w-20"
            />
          </div>

          <!-- Сортировка -->
          <div class="flex flex-col gap-1">
            <label class="text-[10px] font-bold uppercase text-zinc-400 ml-1">Сортировка</label>
            <Select
              v-model="selectedSort"
              :options="sortOptions"
              optionLabel="label"
              class="p-inputtext-sm w-48"
            />
          </div>
        </div>
      </template>

      <template #end>
        <div class="flex gap-2">
          <Button icon="pi pi-filter-slash" severity="secondary" text @click="resetFilters" />
          <Button label="Найти" icon="pi pi-search" size="small" @click="handleFilter" />
        </div>
      </template>
    </Menubar>

    <!-- Список (DataView) -->
    <!-- Пропс dataViewLayout ("grid" по умолчанию) управляет отображением -->
    <DataView :value="specialists" layout="grid" :loading="isLoading" class="min-h-[400px]">
      <template #grid="slotProps">
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 w-full">
          <div v-for="(item, index) in slotProps.items" :key="index">
            <SpecialistCard :specialist="item" />
          </div>
        </div>
      </template>

      <template #empty>
        <div class="flex flex-col items-center justify-center py-20 text-zinc-400 gap-4">
          <i class="pi pi-search text-4xl"></i>
          <span>Специалисты не найдены. Попробуйте изменить фильтры.</span>
        </div>
      </template>
    </DataView>

    <!-- Пагинация с выбором кол-ва строк -->
    <div class="mt-10 card">
      <Paginator
        :rows="filters.per_page"
        :totalRecords="totalRecords"
        :rowsPerPageOptions="rowsPerPageOptions"
        :first="(filters.page - 1) * filters.per_page"
        @page="onPageChange"
        template="RowsPerPageDropdown FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport"
        currentPageReportTemplate="{first} - {last} из {totalRecords}"
      />
    </div>
  </div>
</template>

<style scoped>
/* Убираем стандартные бордеры Menubar для чистого вида */
:deep(.p-menubar) {
  border: 1px solid #f4f4f5;
}
</style>
