import { describe, it, expect, vi, beforeEach } from 'vitest'
import api from '../index'
import {
  getHistoryBatches,
  getHistoryByBatch,
  updateBatchName,
  deleteBatch,
} from '../history'
import type { HistoryBatchesResponse, HistoryResponse, HistoryBatch } from '@/types/history'

vi.mock('../index', () => ({
  default: {
    get: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}))

describe('history API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getHistoryBatches', () => {
    it('should call GET /history/batches with default params', async () => {
      const mockResponse: HistoryBatchesResponse = {
        batches: [],
        total_batches: 0,
        total_items: 0,
      }
      vi.mocked(api.get).mockResolvedValue(mockResponse)

      const result = await getHistoryBatches()

      expect(api.get).toHaveBeenCalledWith('/history/batches?limit=50&offset=0')
      expect(result).toEqual(mockResponse)
    })

    it('should call GET /history/batches with custom params', async () => {
      const mockResponse: HistoryBatchesResponse = {
        batches: [
          {
            id: 1,
            name: 'Test Batch',
            items_count: 10,
            sources: ['https://example.com/feed.xml'],
            created_at: '2024-01-15T10:00:00',
            latest_fetched_at: '2024-01-15T10:00:00',
            latest_published_at: '2024-01-15T09:00:00',
          },
        ],
        total_batches: 1,
        total_items: 10,
      }
      vi.mocked(api.get).mockResolvedValue(mockResponse)

      const result = await getHistoryBatches(20, 10)

      expect(api.get).toHaveBeenCalledWith('/history/batches?limit=20&offset=10')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getHistoryByBatch', () => {
    it('should call GET /history/batches/{id} with default params', async () => {
      const mockResponse: HistoryResponse = {
        items: [],
        pagination: {
          page: 1,
          page_size: 50,
          total_items: 0,
          total_pages: 0,
        },
      }
      vi.mocked(api.get).mockResolvedValue(mockResponse)

      const result = await getHistoryByBatch(1)

      expect(api.get).toHaveBeenCalledWith('/history/batches/1?page=1&page_size=50')
      expect(result).toEqual(mockResponse)
    })

    it('should call GET /history/batches/{id} with custom params', async () => {
      const mockResponse: HistoryResponse = {
        items: [
          {
            id: 1,
            source_id: 1,
            source: 'Test Source',
            title: 'Test Item',
            link: 'https://example.com/item',
            description: 'Test description',
            published_at: '2024-01-15T09:00:00',
            fetched_at: '2024-01-15T10:00:00',
          },
        ],
        pagination: {
          page: 2,
          page_size: 20,
          total_items: 30,
          total_pages: 2,
        },
      }
      vi.mocked(api.get).mockResolvedValue(mockResponse)

      const result = await getHistoryByBatch(5, 2, 20)

      expect(api.get).toHaveBeenCalledWith('/history/batches/5?page=2&page_size=20')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('updateBatchName', () => {
    it('should call PATCH /history/batches/{id}/name with request body', async () => {
      const mockResponse: HistoryBatch = {
        id: 1,
        name: 'Updated Name',
        items_count: 10,
        sources: ['https://example.com/feed.xml'],
        created_at: '2024-01-15T10:00:00',
        latest_fetched_at: '2024-01-15T10:00:00',
        latest_published_at: '2024-01-15T09:00:00',
      }
      vi.mocked(api.patch).mockResolvedValue(mockResponse)

      const result = await updateBatchName(1, { name: 'Updated Name' })

      expect(api.patch).toHaveBeenCalledWith('/history/batches/1/name', { name: 'Updated Name' })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('deleteBatch', () => {
    it('should call DELETE /history/batches/{id}', async () => {
      const mockResponse = { success: true }
      vi.mocked(api.delete).mockResolvedValue(mockResponse)

      const result = await deleteBatch(1)

      expect(api.delete).toHaveBeenCalledWith('/history/batches/1')
      expect(result).toEqual(mockResponse)
    })
  })
})