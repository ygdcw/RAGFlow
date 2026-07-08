import request from './request'

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
  getAllDocuments: (): Promise<AdminDocument[]> =>
    request.get('/admin/documents'),

  deleteDocument: (docId: string): Promise<void> =>
    request.delete(`/admin/documents/${docId}`),

  reparseDocument: (docId: string): Promise<void> =>
    request.post(`/admin/documents/${docId}/reparse`),

  updateDocumentTags: (docId: string, tags: string[]): Promise<void> =>
    request.put(`/admin/documents/${docId}/tags`, { tags }),

  createKnowledgeBase: (name: string): Promise<void> =>
  request.post('/admin/knowledge-bases', null, { params: { name } }),

uploadDocument: (formData: FormData): Promise<void> =>
  request.post('/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000,
  }),
}

