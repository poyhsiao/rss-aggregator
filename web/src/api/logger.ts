import type { LogAction, OperationLogDetails } from '@/types/log'
import { useLogStore } from '@/stores/log'

export interface ApiLogConfig {
  action: LogAction
  target?: string
  targetId?: number
}

export function getActionFromUrl(method: string, url: string): ApiLogConfig | null {
  if (url.includes('/sources')) {
    if (method === 'POST') {
      return { action: 'create_source' }
    }
    if (method === 'PUT' || method === 'PATCH') {
      const match = url.match(/\/sources\/(\d+)/)
      return { action: 'update_source', targetId: match ? parseInt(match[1]) : undefined }
    }
    if (method === 'DELETE') {
      const match = url.match(/\/sources\/(\d+)/)
      return { action: 'delete_source', targetId: match ? parseInt(match[1]) : undefined }
    }
    if (url.includes('/refresh')) {
      if (url.includes('/sources/refresh')) {
        return { action: 'refresh_all' }
      }
      const match = url.match(/\/sources\/(\d+)\/refresh/)
      return { action: 'refresh_source', targetId: match ? parseInt(match[1]) : undefined }
    }
  }

  if (url.includes('/keys')) {
    if (method === 'POST') {
      return { action: 'create_key' }
    }
    if (method === 'DELETE') {
      const match = url.match(/\/keys\/(\d+)/)
      return { action: 'delete_key', targetId: match ? parseInt(match[1]) : undefined }
    }
  }

  return null
}

export function getActionMessage(action: LogAction, status: 'success' | 'error'): string {
  const messages: Record<LogAction, { success: string; error: string }> = {
    create_source: {
      success: 'Source created successfully',
      error: 'Failed to create source',
    },
    update_source: {
      success: 'Source updated successfully',
      error: 'Failed to update source',
    },
    delete_source: {
      success: 'Source deleted successfully',
      error: 'Failed to delete source',
    },
    create_key: {
      success: 'API key created successfully',
      error: 'Failed to create API key',
    },
    delete_key: {
      success: 'API key deleted successfully',
      error: 'Failed to delete API key',
    },
    refresh_source: {
      success: 'Source refreshed successfully',
      error: 'Failed to refresh source',
    },
    refresh_all: {
      success: 'All sources refreshed successfully',
      error: 'Failed to refresh sources',
    },
  }

  return messages[action][status]
}

export function logApiOperation(params: {
  action: LogAction
  status: 'success' | 'error'
  target?: string
  targetId?: number
  request?: unknown
  response?: unknown
  error?: string
}): void {
  try {
    const logStore = useLogStore()
    const details: OperationLogDetails = {
      target: params.target,
      targetId: params.targetId,
      request: params.request,
      response: params.response,
      error: params.error,
    }

    logStore.addLog({
      action: params.action,
      status: params.status,
      message: getActionMessage(params.action, params.status),
      details,
    })
  } catch {
    // Ignore logging errors
  }
}

export function sanitizeRequestData(data: unknown): unknown {
  if (!data || typeof data !== 'object') {
    return data
  }

  const sanitized = { ...data as Record<string, unknown> }
  delete sanitized.apiKey
  delete sanitized['X-API-Key']
  delete sanitized.password
  delete sanitized.token

  return sanitized
}