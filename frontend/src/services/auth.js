import { reactive } from 'vue'
import { api } from './api'

export const authState = reactive({
  role: localStorage.getItem('user_role') || null,
  setRole(newRole) {
    this.role = newRole
    localStorage.setItem('user_role', newRole)
  },
  clear() {
    this.role = null
    localStorage.removeItem('user_role')
    localStorage.removeItem('user_token')
  },
})

export const login = () => {
  sessionStorage.setItem('auth_in_progress', 'true')
  return window.location.href = `${import.meta.env.VITE_API_URL}/auth/login`
}

export const logout = async () => {
  authState.clear()
  const response = await api.post('/auth/logout')
  return response.data
}
