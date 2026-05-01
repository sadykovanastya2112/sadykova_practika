<script setup>
import Menubar from 'primevue/menubar'
import UserPopupMenu from './landing/menus/UserPopupMenu.vue'
import { Button, Avatar } from 'primevue'
import { ref, onMounted, watch } from 'vue'
import { useLogto } from '@logto/vue'
import axios from 'axios' // Предполагаем использование axios

const { isAuthenticated, getAccessToken, signIn } = useLogto()

const items = [
  { label: 'Главная', route: '/' },
  { label: 'Каталог', route: '/catalog' },
  { label: 'Личный кабинет', route: '/dashboard' },
]

const menuComponent = ref(null)
const userData = ref({
  name: '',
  photo: '',
  role: null, // 'client' | 'specialist'
})

const handleAuth = (event) => {
  if (isAuthenticated.value) {
    menuComponent.value.toggle(event)
  } else {
    signIn(`${window.location.origin}/callback`)
  }
}

const goToLogin = () => {
  window.location.href = `${import.meta.env.VITE_API_URL}/auth/login`
}

const loadUserProfile = async () => {
  if (!isAuthenticated.value) return

  try {
    const token = await getAccessToken()
    const headers = { Authorization: `Bearer ${token}` }

    // Логика определения кто перед нами.
    // Можно попробовать запросить профиль специалиста, если 403 — значит клиент.
    try {
      const specRes = await axios.get('/specialist/me', { headers })
      userData.value = {
        name: specRes.data.me.first_name,
        photo: specRes.data.me.photo_url,
        role: 'specialist',
      }
    } catch (err) {
      if (err.response?.status === 403) {
        // Если не специалист, пробуем получить данные клиента
        // (Добавь эндпоинт /clients/me если он есть, или используй общую логику)
        const clientRes = await axios.get('/clients/me', { headers })
        userData.value = {
          name: clientRes.data.first_name || 'Клиент',
          photo: clientRes.data.photo_url,
          role: 'client',
        }
      }
    }
  } catch (error) {
    console.error('Ошибка загрузки профиля:', error)
  }
}

onMounted(loadUserProfile)
// Следим за изменением статуса авторизации
watch(isAuthenticated, (newVal) => {
  if (newVal) loadUserProfile()
  else userData.value = { name: '', photo: '', role: null }
})
</script>

<template>
  <header class="sticky top-0 z-50 flex flex-col bg-white border-b border-gray-200">
    <Menubar
      :model="items"
      breakpoint="48rem"
      class="border-none bg-transparent max-w-[64rem] mx-auto w-full"
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
          <Button text severity="secondary" @click="goToLogin">
            <div class="flex items-center gap-2">
              <!-- Отображение имени -->
              <p class="m-0">
                {{ isAuthenticated ? userData.name || 'Загрузка...' : 'Войти' }}
              </p>

              <!-- Аватар -->
              <Avatar
                :image="isAuthenticated ? userData.photo : null"
                shape="circle"
                icon="pi pi-user"
              />
            </div>
          </Button>
          <UserPopupMenu ref="menuComponent" />
        </div>
      </template>
    </Menubar>
  </header>
</template>
