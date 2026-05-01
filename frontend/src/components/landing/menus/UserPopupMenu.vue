<script setup>
import TieredMenu from 'primevue/tieredmenu'
import { ref } from 'vue'

const menu = ref(null)

const items = ref([
  { label: 'Настройки' },
  {
    label: 'Сменить роль',
    items: [
      {
        label: 'Обновить',
        icon: 'pi pi-refresh',
        command: () => {
          // Действие при клике
        },
      },
      {
        label: 'Удалить',
        icon: 'pi pi-times',
        command: () => {
          // Действие при клике
        },
      },
    ],
  },
  { label: 'Выйти' },
])

const toggle = (event) => {
  menu.value.toggle(event)
}

defineExpose({ toggle })
</script>

<template>
  <TieredMenu ref="menu" id="overlay_tmenu" :model="items" popup />
</template>
