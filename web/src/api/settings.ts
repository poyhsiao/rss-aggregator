import api from '.'

export const feedUrlApi = {
  async get() {
    return await api.get<{ enabled: boolean }>('/settings/feed-url')
  },

  async set(enabled: boolean) {
    await api.post('/settings/feed-url', { enabled })
  },
}