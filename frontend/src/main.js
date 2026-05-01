import './assets/main.css'

import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

import { createLogto } from '@logto/vue'

import PrimeVue from 'primevue/config'
import ToastService from 'primevue/toastservice'
import Tooltip from 'primevue/tooltip'
import Aura from '@primeuix/themes/aura'

const app = createApp(App)

app.directive('tooltip', Tooltip)

app.use(router)
app.use(createLogto, {
  endpoint: import.meta.env.VITE_LOGTO_ENDPOINT,
  appId: import.meta.env.VITE_LOGTO_APP_ID,
})
app.use(PrimeVue, {
  theme: {
    preset: Aura,
    options: {
      darkModeSelector: false,
    },
  },
})
app.use(ToastService)

app.mount('#app')
