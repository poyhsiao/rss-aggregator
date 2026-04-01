import { describe, it, expect, vi, beforeEach } from 'vitest'
import api from '../index'
import {
  getGroups,
  createGroup,
  updateGroup,
  deleteGroup,
  getGroupSources,
  addSourceToGroup,
  removeSourceFromGroup,
} from '../source-groups'
import type { SourceGroup } from '@/types/source-group'

vi.mock('../index', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

describe('source groups API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getGroups', () => {
    it('should call GET /source-groups', async () => {
      const mockGroups: SourceGroup[] = [
        { id: 1, name: 'Tech', member_count: 2, created_at: '2024-01-01T00:00:00', updated_at: '2024-01-01T00:00:00' },
      ]
      vi.mocked(api.get).mockResolvedValue(mockGroups)

      const result = await getGroups()

      expect(api.get).toHaveBeenCalledWith('/source-groups')
      expect(result).toEqual(mockGroups)
    })
  })

  describe('createGroup', () => {
    it('should call POST /source-groups with name', async () => {
      const mockGroup: SourceGroup = {
        id: 1, name: 'News', member_count: 0, created_at: '2024-01-01T00:00:00', updated_at: '2024-01-01T00:00:00',
      }
      vi.mocked(api.post).mockResolvedValue(mockGroup)

      const result = await createGroup({ name: 'News' })

      expect(api.post).toHaveBeenCalledWith('/source-groups', { name: 'News' })
      expect(result).toEqual(mockGroup)
    })
  })

  describe('updateGroup', () => {
    it('should call PUT /source-groups/{id} with name', async () => {
      const mockGroup: SourceGroup = {
        id: 1, name: 'Updated', member_count: 0, created_at: '2024-01-01T00:00:00', updated_at: '2024-01-01T00:00:00',
      }
      vi.mocked(api.put).mockResolvedValue(mockGroup)

      const result = await updateGroup(1, { name: 'Updated' })

      expect(api.put).toHaveBeenCalledWith('/source-groups/1', { name: 'Updated' })
      expect(result).toEqual(mockGroup)
    })
  })

  describe('deleteGroup', () => {
    it('should call DELETE /source-groups/{id}', async () => {
      vi.mocked(api.delete).mockResolvedValue(undefined)

      await deleteGroup(1)

      expect(api.delete).toHaveBeenCalledWith('/source-groups/1')
    })
  })

  describe('getGroupSources', () => {
    it('should call GET /source-groups/{id}/sources', async () => {
      const mockSources = [
        { id: 1, name: 'Feed', url: 'https://example.com/rss', is_active: true, last_fetched_at: null, last_error: null, created_at: '', updated_at: '', groups: [] },
      ]
      vi.mocked(api.get).mockResolvedValue(mockSources)

      const result = await getGroupSources(1)

      expect(api.get).toHaveBeenCalledWith('/source-groups/1/sources')
      expect(result).toEqual(mockSources)
    })
  })

  describe('addSourceToGroup', () => {
    it('should call POST /source-groups/{id}/sources with source_id', async () => {
      vi.mocked(api.post).mockResolvedValue({ message: 'ok' })

      await addSourceToGroup(1, 5)

      expect(api.post).toHaveBeenCalledWith('/source-groups/1/sources', { source_id: 5 })
    })
  })

  describe('removeSourceFromGroup', () => {
    it('should call DELETE /source-groups/{id}/sources/{sourceId}', async () => {
      vi.mocked(api.delete).mockResolvedValue(undefined)

      await removeSourceFromGroup(1, 5)

      expect(api.delete).toHaveBeenCalledWith('/source-groups/1/sources/5')
    })
  })
})
