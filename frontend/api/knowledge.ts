import request from './request'

export const knowledgeApi = {
  // 获取知识库列表
  getList: (page = 1, pageSize = 20): Promise<PaginatedData<KnowledgeBase>> =>
    request.get('/knowledge-bases', { params: { page, page_size: pageSize } }),

  // 创建知识库
  create: (name: string): Promise<KnowledgeBase> =>
    request.post('/knowledge-bases', { name }),

  // 删除知识库
  delete: (kbId: string): Promise<void> =>
    request.delete(`/knowledge-bases/${kbId}`),

  // 获取知识库下的文档列表
  getDocuments: (kbId: string): Promise<PaginatedData<Document>> =>
    request.get(`/knowledge-bases/${kbId}/documents`),

  // 上传文档
  upload: (kbId: string, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('knowledge_base_id', kbId)
    return request.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000,
    })
  },

  // 删除文档
  deleteDocument: (docId: string): Promise<void> =>
    request.delete(`/documents/${docId}`),
}