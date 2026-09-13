import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export interface ApiError {
  code: string
  message: string
  request_id?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('access_token')
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail: ApiError }>) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export function getErrorMessage(error: unknown, fallback = 'An error occurred'): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (detail?.message) return detail.message
    if (typeof detail === 'string') return detail
    if (error.response?.status === 409) return 'Conflict: Resource was modified by another user.'
    if (error.response?.status === 403) return 'You do not have permission to perform this action.'
    if (error.response?.status === 404) return 'Resource not found.'
    if (error.response?.status === 422) return 'Validation error. Please check your input.'
    if (error.response?.status === 429) return 'Too many requests. Please try again later.'
    if (error.response?.status === 500) return 'Server error. Please try again later.'
    if (error.code === 'ERR_NETWORK') return 'Network error. Please check your connection.'
  }
  return fallback
}
