import client, { API_BASE_URL } from './client'

export const authApi = {
  register: (data) => client.post('/api/auth/register', data),
  registerAdmin: (data) => client.post('/api/auth/register-admin', data),
  login: (data) => client.post('/api/auth/login', data),
  me: () => client.get('/api/auth/me'),
}

export const chatApi = {
  listConversations: () => client.get('/api/chat/conversations'),
  createConversation: (title) => client.post('/api/chat/conversations', { title }),
  getConversation: (id) => client.get(`/api/chat/conversations/${id}`),
  deleteConversation: (id) => client.delete(`/api/chat/conversations/${id}`),
  sendMessage: (conversationId, content) =>
    client.post(`/api/chat/conversations/${conversationId}/messages`, { content }),
  rateFeedback: (messageId, isHelpful) =>
    client.post(`/api/chat/messages/${messageId}/feedback`, { is_helpful: isHelpful }),
}

export const documentApi = {
  list: () => client.get('/api/documents'),
  stats: () => client.get('/api/documents/stats'),
  upload: (formData) =>
    client.post('/api/documents', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  remove: (id) => client.delete(`/api/documents/${id}`),
  reprocess: (id) => client.post(`/api/documents/${id}/reprocess`),
  fetchFileObjectUrl: async (id) => {
    const res = await client.get(`/api/documents/${id}/file`, { responseType: 'blob' })
    return URL.createObjectURL(res.data)
  },
}

export { API_BASE_URL }