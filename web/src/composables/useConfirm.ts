/**
 * Confirm Dialog Composable
 * Provides a programmatic way to show confirmation dialogs
 * 
 * Usage:
 * const confirm = useConfirm()
 * const result = await confirm.show({
 *   message: 'Are you sure?',
 *   title: 'Delete Item',
 *   confirmText: 'Delete',
 *   cancelText: 'Cancel',
 *   variant: 'danger'
 * })
 * if (result) { ... }
 */
import { ref, readonly } from 'vue'

export interface ConfirmOptions {
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
  variant?: 'danger' | 'warning' | 'info'
}

interface ConfirmState extends ConfirmOptions {
  open: boolean
  resolve: ((value: boolean) => void) | null
}

const state = ref<ConfirmState>({
  open: false,
  message: '',
  title: '',
  confirmText: 'Confirm',
  cancelText: 'Cancel',
  variant: 'danger',
  resolve: null,
})

function show(options: ConfirmOptions): Promise<boolean> {
  return new Promise((resolve) => {
    state.value = {
      ...options,
      open: true,
      resolve,
    }
  })
}

function handleConfirm(): void {
  if (state.value.resolve) {
    state.value.resolve(true)
  }
  state.value.open = false
  state.value.resolve = null
}

function handleCancel(): void {
  if (state.value.resolve) {
    state.value.resolve(false)
  }
  state.value.open = false
  state.value.resolve = null
}

export function useConfirm() {
  return {
    state: readonly(state),
    show,
    confirm: handleConfirm,
    cancel: handleCancel,
  }
}