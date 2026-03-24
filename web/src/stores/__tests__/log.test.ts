import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useLogStore } from '../log'
import type { OperationLog } from '@/types/log'

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key]
    }),
    clear: vi.fn(() => {
      store = {}
    }),
  }
})()

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
})

describe('Log Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorageMock.clear()
    vi.clearAllMocks()
  })

  describe('addLog', () => {
    it('should add a log entry', () => {
      const store = useLogStore()
      
      store.addLog({
        action: 'create_source',
        status: 'success',
        message: 'Source created successfully',
        details: { target: 'Test Source' },
      })

      expect(store.logs).toHaveLength(1)
      expect(store.logs[0].action).toBe('create_source')
      expect(store.logs[0].status).toBe('success')
      expect(store.logs[0].message).toBe('Source created successfully')
      expect(store.logs[0].details.target).toBe('Test Source')
    })

    it('should generate unique id for each log', () => {
      const store = useLogStore()
      
      store.addLog({
        action: 'create_source',
        status: 'success',
        message: 'Log 1',
        details: {},
      })
      
      store.addLog({
        action: 'delete_source',
        status: 'success',
        message: 'Log 2',
        details: {},
      })

      expect(store.logs[0].id).not.toBe(store.logs[1].id)
    })

    it('should add timestamp to each log', () => {
      const store = useLogStore()
      const beforeTime = new Date().toISOString()
      
      store.addLog({
        action: 'create_source',
        status: 'success',
        message: 'Test',
        details: {},
      })
      
      const afterTime = new Date().toISOString()
      
      expect(store.logs[0].timestamp).toBeDefined()
      expect(store.logs[0].timestamp >= beforeTime).toBe(true)
      expect(store.logs[0].timestamp <= afterTime).toBe(true)
    })

    it('should limit logs to MAX_LOGS entries', () => {
      const store = useLogStore()
      
      // Add more than MAX_LOGS (100) entries
      for (let i = 0; i < 150; i++) {
        store.addLog({
          action: 'create_source',
          status: 'success',
          message: `Log ${i}`,
          details: {},
        })
      }

      expect(store.logs.length).toBeLessThanOrEqual(100)
    })

    it('should keep most recent logs when limit reached', () => {
      const store = useLogStore()
      
      for (let i = 0; i < 150; i++) {
        store.addLog({
          action: 'create_source',
          status: 'success',
          message: `Log ${i}`,
          details: {},
        })
      }

      // The oldest log should be around index 50 (150 - 100)
      const oldestMessage = parseInt(store.logs[0].message.split(' ')[1])
      expect(oldestMessage).toBeGreaterThanOrEqual(50)
    })
  })

  describe('clearLogs', () => {
    it('should clear all logs', () => {
      const store = useLogStore()
      
      store.addLog({
        action: 'create_source',
        status: 'success',
        message: 'Test',
        details: {},
      })
      
      expect(store.logs).toHaveLength(1)
      
      store.clearLogs()
      
      expect(store.logs).toHaveLength(0)
    })
  })

  describe('getLogsByStatus', () => {
    it('should filter logs by status', () => {
      const store = useLogStore()
      
      store.addLog({
        action: 'create_source',
        status: 'success',
        message: 'Success 1',
        details: {},
      })
      
      store.addLog({
        action: 'create_source',
        status: 'error',
        message: 'Error 1',
        details: { error: 'Something went wrong' },
      })
      
      store.addLog({
        action: 'delete_source',
        status: 'success',
        message: 'Success 2',
        details: {},
      })

      const successLogs = store.getLogsByStatus('success')
      const errorLogs = store.getLogsByStatus('error')

      expect(successLogs).toHaveLength(2)
      expect(errorLogs).toHaveLength(1)
    })
  })

  describe('getLogsByAction', () => {
    it('should filter logs by action', () => {
      const store = useLogStore()
      
      store.addLog({
        action: 'create_source',
        status: 'success',
        message: 'Created source',
        details: {},
      })
      
      store.addLog({
        action: 'delete_source',
        status: 'success',
        message: 'Deleted source',
        details: {},
      })
      
      store.addLog({
        action: 'create_source',
        status: 'error',
        message: 'Failed to create',
        details: { error: 'Error' },
      })

      const createLogs = store.getLogsByAction('create_source')
      const deleteLogs = store.getLogsByAction('delete_source')

      expect(createLogs).toHaveLength(2)
      expect(deleteLogs).toHaveLength(1)
    })
  })

  describe('persistence', () => {
    it('should persist logs to localStorage', () => {
      const store = useLogStore()
      
      store.addLog({
        action: 'create_source',
        status: 'success',
        message: 'Test persistence',
        details: {},
      })

      expect(localStorageMock.setItem).toHaveBeenCalled()
    })

    it('should load logs from localStorage on init', () => {
      const mockLogs: OperationLog[] = [
        {
          id: 'test-id-1',
          timestamp: new Date().toISOString(),
          action: 'create_source',
          status: 'success',
          message: 'Persisted log',
          details: {},
        },
      ]
      
      localStorageMock.getItem = vi.fn().mockReturnValue(JSON.stringify(mockLogs))
      
      setActivePinia(createPinia())
      const store = useLogStore()
      
      expect(store.logs).toHaveLength(1)
      expect(store.logs[0].message).toBe('Persisted log')
    })
  })

  describe('getLatestLogs', () => {
    it('should return specified number of latest logs', () => {
      const store = useLogStore()
      
      for (let i = 0; i < 10; i++) {
        store.addLog({
          action: 'create_source',
          status: 'success',
          message: `Log ${i}`,
          details: {},
        })
      }

      const latest5 = store.getLatestLogs(5)
      expect(latest5).toHaveLength(5)
      
      // Should be the most recent (last 5 added)
      const messages = latest5.map(l => l.message)
      expect(messages).toContain('Log 9')
      expect(messages).toContain('Log 8')
    })
  })
})