<script setup>
import TieredMenu from 'primevue/tieredmenu'
import { ref, computed } from 'vue'
import { authState, logout } from '@/services/auth.js'
import { apiAssignRole } from '@/services/api.js'

const props = defineProps({
  user: {
    type: Object,
    required: true,
  },
})

const menu = ref(null)

// Делаем меню реактивным, чтобы роли подтянулись, когда загрузятся
const items = computed(() => [
  {
    label: 'Настройки',
    icon: 'pi pi-cog',
  },
  {
    label: 'Стать специалистом',
    icon: 'pi pi-user-plus',
    // Показываем, если текущая роль - клиент И в списке ролей нет специалиста
    visible: authState.role === 'client' && !props.user.roles.includes('specialist'),
    command: async () => {
      await apiAssignRole('specialist')
    },
  },
  {
    label: 'Сменить роль',
    icon: 'pi pi-users',
    // Показываем подменю выбора ролей, только если их больше одной
    visible: props.user.roles.length > 1,
    items: props.user.roles.map((roleName) => ({
      label: roleName,
      icon: roleName === authState.role ? 'pi pi-check' : '', // Помечаем текущую
      command: () => {
        authState.setRole(roleName) // Меняем роль в нашем реактивном объекте
      },
    })),
  },
  { separator: true },
  {
    label: 'Выйти',
    icon: 'pi pi-sign-out',
    command: logout,
  },
])

const toggle = (event) => {
  menu.value.toggle(event)
}

// Позволяем родителю вызывать этот метод
defineExpose({ toggle })
</script>

<template>
  <TieredMenu ref="menu" id="overlay_tmenu" :model="items" popup />
</template>
