import CatalogView from '@/views/CatalogView.vue'
import ClientAppointmentsView from '@/views/ClientAppointmentsView.vue'
import SpecialistSessionsView from '@/views/SpecialistSessionsView.vue'
import SpecialistScheduleView from '@/views/SpecialistScheduleView.vue'
import AdminControlPanelView from '@/views/AdminControlPanelView.vue'
import LandingView from '@/views/LandingView.vue'

export default [
  {
    path: '',
    component: LandingView,
    meta: { requiredRole: null },
  },
  {
    path: 'catalog',
    component: CatalogView,
    meta: { requiredRole: null },
  },
  {
    path: 'client/appointments',
    component: ClientAppointmentsView,
    meta: { requiredRole: 'client' },
  },
  {
    path: 'specialist/sessions',
    component: SpecialistSessionsView,
    meta: { requiredRole: 'specialist' },
  },
  {
    path: 'specialist/schedule',
    component: SpecialistScheduleView,
    meta: { requiredRole: 'specialist' },
  },
  {
    path: 'admin/control-panel',
    component: AdminControlPanelView,
    meta: { requiredRole: 'admin' },
  },
]
