/**
 * Toast Composable
 * Provides a global toast notification system
 * 
 * Usage:
 * const toast = useToast()
 * toast.success('Operation completed')
 * toast.error('Something went wrong')
 */
import { ref, readonly } from 'vue'

export type ToastType = 'success' | 'error' | 'info' | 'warning'

export interface ToastMessage {
  id: string
  type: ToastType
  message: string
  duration: number
}

const toasts = ref<ToastMessage[]>([])
let toastId = 0

function generateId(): string {
  return `toast-${++toastId}`
}

function removeToast(id: string): void {
  const index = toasts.value.findIndex(t => t.id === id)
  if (index > -1) {
    toasts.value.splice(index, 1)
  }
}

function addToast(type: ToastType, message: string, duration = 3000): string {
  const id = generateId()
  const toast: ToastMessage = { id, type, message, duration }
  toasts.value.push(toast)

  if (duration > 0) {
    setTimeout(() => {
      removeToast(id)
    }, duration)
  }

  return id
}

export function useToast() {
  return {
    toasts: readonly(toasts),
    success: (message: string, duration?: number) => addToast('success', message, duration),
    error: (message: string, duration?: number) => addToast('error', message, duration),
    info: (message: string, duration?: number) => addToast('info', message, duration),
    warning: (message: string, duration?: number) => addToast('warning', message, duration),
    remove: removeToast,
  }
}