import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL

const api = axios.create({
  baseURL: API_URL,
  timeout: 10000,
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      //localStorage.removeItem('user_token')
      //window.location.href = '/'
    }
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

export const apiGetUserRole = async () => {
  const token = localStorage.getItem('user_token')
  const response = await api.get('/auth/me', { headers: { Authorization: `Bearer ${token}` } })
  return response.data
}
