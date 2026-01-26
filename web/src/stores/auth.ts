import { ref } from 'vue'
import api from '@/api'

// Global state
const isAuthEnabled = ref(true) // Default to true to be safe
const isInitialized = ref(false)

export const useAuthStore = () => {
  const fetchAuthConfig = async () => {
    if (isInitialized.value) return
    try {
      const res = await api.auth.getAuthConfig()
      if (res.success && res.data.code === 200 && res.data.data) {
        isAuthEnabled.value = res.data.data.enabled
      }
    } catch (e) {
      console.error('Failed to fetch auth config', e)
      // On error, default to true (safe)
      isAuthEnabled.value = true
    } finally {
      isInitialized.value = true
    }
  }

  return {
    isAuthEnabled,
    isInitialized,
    fetchAuthConfig
  }
}
