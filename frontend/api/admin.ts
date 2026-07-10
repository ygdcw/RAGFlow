import request, { uploadRequest } from './request'

export const adminApi = {
  // 用户管理
  getUserList: (): Promise<AdminUser[]> =>
    request.get('/admin/users'),

  addUser: (data: { username: string; password: string; role: string }): Promise<void> =>
    request.post('/admin/users', data),

  deleteUser: (userId: string): Promise<void> =>
    request.delete(`/admin/users/${userId}`),

  toggleUserStatus: (userId: string): Promise<void> =>
    request.post(`/admin/users/${userId}/toggle`),

  // 系统监控
  getSystemStats: (): Promise<SystemStats> =>
    request.get('/admin/stats'),

  // 操作日志
  getOperationLogs: (): Promise<OperationLog[]> =>
    request.get('/admin/logs'),

  // 知识库管理（管理员视角）
  getAllKnowledgeBases: (): Promise<AdminKnowledgeBase[]> =>
    request.get('/admin/knowledge-bases'),

  deleteKnowledgeBase: (kbId: string): Promise<void> =>
    request.delete(`/admin/knowledge-bases/${kbId}`),

    // 文档管理
  getAllDocuments: (params?: { page?: number; page_size?: number; knowledge_base?: string }): Promise<{ items: AdminDocument[]; total: number; page: number; page_size: number }> =>
    request.get('/admin/documents', { params }),

  deleteDocument: (docId: string): Promise<void> =>
    request.delete(`/admin/documents/${docId}`),

  reparseDocument: (docId: string): Promise<void> =>
    request.post(`/admin/documents/${docId}/reparse`),

  updateDocumentTags: (docId: string, tags: string[]): Promise<void> =>
    request.put(`/admin/documents/${docId}/tags`, { tags }),

  getDocumentContent: (docId: string): Promise<{ id: string; content: string; filename: string; knowledge_base: string }> =>
    request.get(`/admin/documents/${docId}/content`),

  batchDeleteDocuments: (docIds: string[]): Promise<{ deleted_count: number; message: string }> =>
    request.delete('/admin/documents/batch', { data: docIds }),

  createKnowledgeBase: (name: string): Promise<void> =>
  request.post('/admin/knowledge-bases', null, { params: { name } }),

uploadDocument: (formData: FormData): Promise<void> =>
  uploadRequest.post('/documents/upload', formData),
}

