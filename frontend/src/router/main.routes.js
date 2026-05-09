export default [
  {
    path: '',
    component: () => import('@/views/LandingView.vue'),
    meta: { requiredRole: null },
  },
  {
    path: 'catalog',
    component: () => import('@/views/CatalogView.vue'),
    meta: { requiredRole: null },
  },
  {
    path: 'client/appointments',
    component: () => import('@/views/ClientAppointmentsView.vue'),
    meta: { requiredRole: 'client' },
  },
  {
    path: 'specialist/sessions',
    component: () => import('@/views/SpecialistSessionsView.vue'),
    meta: { requiredRole: 'specialist' },
  },
  {
    path: 'specialist/schedule',
    component: () => import('@/views/SpecialistScheduleView.vue'),
    meta: { requiredRole: 'specialist' },
  },
  {
    path: 'admin/control-panel',
    component: () => import('@/views/AdminControlPanelView.vue'),
    meta: { requiredRole: 'admin' },
  },
  {
    path: 'payment/callback',
    component: () => import('@/views/PaymentCallback.vue'),
    meta: { requiresRole: 'any' },
  },
]
