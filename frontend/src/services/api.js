import axios from 'axios'
import { authState } from './auth'

const API_URL = import.meta.env.VITE_API_URL

export const api = axios.create({
  baseURL: API_URL,
  timeout: 10000,
  withCredentials: true,
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      authState.clear()
      window.location.href = `${import.meta.env.VITE_API_URL}/auth/login`
    }
    return Promise.reject(error)
  },
)

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('user_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  },
)

export const apiGetSpecialists = async (params) => {
  try {
    const response = await api.get('/specialist/specialists', { params })
    return response.data
  } catch (error) {
    console.error('Failed to fetch specialists list', error)
    return { items: [], total: 0 }
  }
}

export const apiGetSpecialistProfile = async (id) => {
  const response = await api.get(`/specialist/profile/${id}`)
  return response.data
}

export const apiGetUserRoles = async () => {
  const response = await api.get('/auth/me')
  return response.data.all_roles
}

export const apiAssignRole = async (roleName) => {
  try {
    const response = await api.post('/auth/assign-role', {
      role: roleName,
    })
    return response.data
  } catch (error) {
    throw error
  }
}

export const apiGetUserIdentity = async () => {
  const currentRole = authState.role
  try {
    if (currentRole === 'client') {
      const response = await api.get('/clients/me')
      return { displayName: response.data.me.display_name, photo: response.data.me.photo_url }
    } else if (currentRole === 'specialist') {
      const response = await api.get('/specialist/me')
      return { displayName: response.data.me.first_name, photo: response.data.me.photo_url }
    } else if (currentRole === 'admin') {
      return { displayName: 'Админ', photo: '' }
    }
  } catch (e) {
    console.error(e)
  }
  return { displayName: '', photo: '' }
}

export const apiGetToken = async () => {
  const response = await api.get('/auth/get-token')
  const token = response.data.access_token
  return token
}
