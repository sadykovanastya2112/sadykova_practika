import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'

const mainRoutes = Object.values(import.meta.glob('./modules/main-routes/*.js', { eager: true }))
  .map((m) => m.default)
  .flat()

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: MainLayout,
      children: mainRoutes,
    },
  ],
})

export default router
