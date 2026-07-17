import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '../api/client'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('access_token') || '')

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  async function login(email, password) {
    const resp = await authApi.post('/auth/login', { email, password })
    token.value = resp.data.access_token
    localStorage.setItem('access_token', resp.data.access_token)
    await fetchMe()
  }

  async function register(email, password, displayName) {
    await authApi.post('/auth/register', { email, password, display_name: displayName })
  }

  async function fetchMe() {
    if (!token.value) return
    const resp = await authApi.get('/auth/me')
    user.value = resp.data
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('access_token')
  }

  return { user, token, isLoggedIn, isAdmin, login, register, fetchMe, logout }
})
