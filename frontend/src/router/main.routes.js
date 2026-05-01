import CatalogView from '@/views/CatalogView.vue'
import DashboardView from '@/views/DashboardView.vue'
import LandingView from '@/views/LandingView.vue'

export default [
  {
    path: '',
    component: LandingView,
    meta: { requiresAuth: false },
  },
  {
    path: 'catalog',
    component: CatalogView,
    meta: { requiresAuth: false },
  },
  {
    path: 'dashboard',
    component: DashboardView,
    meta: { requiresAuth: true },
  },
]
