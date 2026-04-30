<script setup>
import Menubar from 'primevue/menubar'
import UserPopupMenu from './landing/menus/UserPopupMenu.vue'
import { Button } from 'primevue'
import { ref } from 'vue'

const items = [
  { label: 'Главная', route: '/' },
  { label: 'Каталог', route: '/catalog' },
  { label: 'Личный кабинет', route: '/dashboard' },
]
const menuComponent = ref(null)

const openMenu = (event) => {
  menuComponent.value.toggle(event)
}
</script>

<template>
  <header class="sticky top-0 z-50 flex flex-col bg-white border-b border-gray-200">
    <Menubar
      :model="items"
      breakpoint="48rem"
      style="border: none; background: none; max-width: 64rem"
    >
      <template #start>
        <i class="pi pi-user" />
      </template>
      <template #end>
        <Button text severity="secondary" @click="openMenu">
          <div class="flex items-center">
            <p>Олег</p>
            <i class="pi pi-user" />
          </div>
        </Button>
        <UserPopupMenu ref="menuComponent" />
      </template>
    </Menubar>
  </header>
</template>
