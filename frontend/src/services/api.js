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

export const apiGetUserProfile = async () => {
  const currentRole = authState.role
  try {
    if (currentRole === 'client') {
      const response = await api.get('/clients/me')
      return response.data.me
    } else if (currentRole === 'specialist') {
      const response = await api.get('/specialist/me')
      return response.data.me
    }
  } catch (e) {
    throw e
  }
}

export const apiUpdateProfile = async (data) => {
  const currentRole = authState.role
  try {
    if (currentRole === 'client') {
      const response = await api.put('/clients/me', data)
      return response.data
    } else if (currentRole === 'specialist') {
      const response = await api.put('/specialist/update', data)
      return response.data
    }
  } catch (e) {
    throw e
  }
}

export const apiDeleteUser = async () => {
  const response = await api.delete('auth/me', {
    headers: { 'Content-Type': 'application/json' },
    data: { confirm: true },
  })
  authState.clear()
  return response.data
}

export const apiGetToken = async () => {
  const response = await api.get('/auth/get-token')
  const token = response.data.access_token
  return token
}

export const apiGetPendingSpecialists = async (page = 1, perPage = 20) => {
  const response = await api.get('/moderation/specialists/pending', {
    params: { page: page, per_page: perPage },
  })
  return response.data
}

export const apiModerateSpecialist = async (id, action, reason = null) => {
  const response = await api.post(`/moderation/specialists/${id}`, {
    action,
    reason,
  })
  return response.data
}

export const apiGetSlots = async (start, end) => {
  const response = await api.get('/slots/get', { params: { start_date: start, end_date: end } })
  return response.data
}

export const apiCreateSlots = async (slotsData) => {
  const response = await api.post('/slots/create', slotsData)
  return response.data
}

export const apiDeleteSlot = async (id) => {
  const response = await api.delete(`/slots/delete/${id}`)
  return response.data
}
