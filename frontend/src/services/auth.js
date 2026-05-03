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
  window.location.href = `${import.meta.env.VITE_API_URL}/auth/login` //не должно ли быть return?
}

export const logout = async () => {
  authState.clear()
  try {
    const response = await api.post('/auth/assign-role')
    return response.data
  } catch (error) {
    throw error
  }
}
