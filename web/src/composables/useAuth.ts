import { useAuthStore } from '@/stores/auth'

export function useAuth() {
  const authStore = useAuthStore()

  async function verify(key: string): Promise<boolean> {
    return authStore.verifyKey(key)
  }

  function logout(): void {
    authStore.logout()
  }

  return {
    apiKey: authStore.apiKey,
    isValid: authStore.isValid,
    isVerifying: authStore.isVerifying,
    error: authStore.error,
    verify,
    logout,
  }
}