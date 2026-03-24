import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { OperationLog, LogAction, OperationLogDetails } from '@/types/log'

const STORAGE_KEY = 'rss-operation-logs'
const MAX_LOGS = 100

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`
}

function loadFromStorage(): OperationLog[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      return JSON.parse(stored) as OperationLog[]
    }
  } catch {
    // Ignore parsing errors
  }
  return []
}

function saveToStorage(logs: OperationLog[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(logs))
  } catch {
    // Ignore storage errors
  }
}

export const useLogStore = defineStore('log', () => {
  const logs = ref<OperationLog[]>(loadFromStorage())

  function addLog(params: {
    action: LogAction
    status: 'success' | 'error'
    message: string
    details: OperationLogDetails
  }): void {
    const newLog: OperationLog = {
      id: generateId(),
      timestamp: new Date().toISOString(),
      action: params.action,
      status: params.status,
      message: params.message,
      details: params.details,
    }

    logs.value = [newLog, ...logs.value]

    if (logs.value.length > MAX_LOGS) {
      logs.value = logs.value.slice(0, MAX_LOGS)
    }

    saveToStorage(logs.value)
  }

  function clearLogs(): void {
    logs.value = []
    saveToStorage([])
  }

  function getLogsByStatus(status: 'success' | 'error'): OperationLog[] {
    return logs.value.filter((log) => log.status === status)
  }

  function getLogsByAction(action: LogAction): OperationLog[] {
    return logs.value.filter((log) => log.action === action)
  }

  function getLatestLogs(count: number = 10): OperationLog[] {
    return logs.value.slice(0, count)
  }

  const errorLogs = computed(() => logs.value.filter((log) => log.status === 'error'))
  const successLogs = computed(() => logs.value.filter((log) => log.status === 'success'))
  const hasLogs = computed(() => logs.value.length > 0)
  const logCount = computed(() => logs.value.length)

  return {
    logs,
    errorLogs,
    successLogs,
    hasLogs,
    logCount,
    addLog,
    clearLogs,
    getLogsByStatus,
    getLogsByAction,
    getLatestLogs,
  }
})