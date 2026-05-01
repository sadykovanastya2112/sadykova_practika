import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'
import mainRoutes from './main.routes'

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

router.beforeEach(async (to) => {
  const tokenFromUrl = to.query.token

  if (tokenFromUrl) {
    localStorage.setItem('user_token', tokenFromUrl)

    // Создаем новый объект query БЕЗ токена
    const newQuery = { ...to.query }
    delete newQuery.token

    // Редиректим на тот же адрес, но без токена в URL
    return { path: to.path, query: newQuery, replace: true }
  }

  const token = localStorage.getItem('user_token')

  // Если страница требует авторизации, а токена нет — на главную
  if (to.meta.requiresAuth && !token) {
    return { path: '/' }
  }

  // В остальных случаях навигация разрешена (возвращать undefined/true)
})

export default router
