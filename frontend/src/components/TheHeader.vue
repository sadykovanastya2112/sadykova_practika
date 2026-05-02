<script setup>
import Menubar from 'primevue/menubar'
import UserPopupMenu from './landing/menus/UserPopupMenu.vue'
import { Button } from 'primevue'
import { ref, watch, computed } from 'vue'
import { authState, login } from '@/services/auth.js'
import { apiGetUserRoles, apiGetUserIdentity } from '@/services/api.js'
import AppAvatar from '@/components/AppAvatar.vue'

const navItems = computed(() => [
  {
    label: 'Главная',
    route: '/',
  },
  {
    label: 'Каталог',
    route: '/catalog',
  },
  {
    label: 'Мои записи',
    route: '/client/appointments',
    visible: authState.role === 'client',
  },
  {
    label: 'Сессии',
    route: '/specialist/sessions',
    visible: authState.role === 'specialist',
  },
  {
    label: 'Расписание',
    route: '/specialist/schedule',
    visible: authState.role === 'specialist',
  },
  {
    label: 'Панель управления',
    route: '/admin/control-panel',
    visible: authState.role === 'admin',
  },
])

const menuComponent = ref(null)

const userData = ref({
  name: '',
  photo: '',
  roles: [],
})

watch(
  () => authState.role,
  async (newRole) => {
    if (!!newRole) {
      const identity = await apiGetUserIdentity()
      userData.value.name = identity.displayName
      userData.value.photo = identity.photo

      const userRoles = await apiGetUserRoles()
      userData.value.roles = userRoles
    } else {
      userData.value.name = 'Войти'
      userData.value.photo = ''
      userData.value.roles = []
    }
  },
  { immediate: true },
)
</script>

<template>
  <header class="sticky top-0 z-50 flex flex-col bg-white border-b border-gray-200">
    <Menubar
      :model="navItems"
      breakpoint="48rem"
      class="border-none! bg-transparent! max-w-5xl mx-auto w-full"
    >
      <template #start>
        <div class="flex items-center gap-2">
          <i class="pi pi-user text-primary" />
          <h3 class="font-bold">Безопасный Контакт</h3>
        </div>
      </template>

      <template #item="{ item, props }">
        <router-link :to="item.route" v-bind="props.action">
          <span>{{ item.label }}</span>
        </router-link>
      </template>

      <template #end>
        <div class="flex items-center gap-3">
          <Button
            text
            severity="secondary"
            @click="(event) => (authState.role ? menuComponent.toggle(event) : login())"
          >
            <div class="flex items-center gap-2">
              <p class="m-0">
                {{ userData.name }}
              </p>

              <AppAvatar :image="userData.photo" class="size-12" />
            </div>
          </Button>
          <UserPopupMenu ref="menuComponent" :user="userData" />
        </div>
      </template>
    </Menubar>
  </header>
</template>
