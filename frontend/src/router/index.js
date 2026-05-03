import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'
import mainRoutes from './main.routes'
import { authState, logout } from '@/services/auth'
import { apiGetToken, apiGetUserRoles } from '@/services/api.js'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: MainLayout,
      children: mainRoutes,
    },
    {
      path: '/403',
      name: 'AccessDenied',
      component: () => import('@/views/AccessDeniedView.vue'),
    },
  ],
})

router.beforeEach(async (to, from, next) => {
  //Завершение аутентификации
  if (sessionStorage.getItem('auth_in_progress')) {
    sessionStorage.removeItem('auth_in_progress')
    try {
      const token = await apiGetToken()
      localStorage.setItem('user_token', token)
      const userRoles = await apiGetUserRoles()
      authState.setRole(userRoles[0])
    } catch (e) {
      console.error(e)
      logout()
    }
  }

  //Авторизация
  const requiredRole = to.meta.requiredRole
  if (!requiredRole) {
    next()
  } else if (authState.role === requiredRole || requiredRole === 'any') {
    next()
  } else {
    next({ name: 'AccessDenied' })
  }
})

export default router
