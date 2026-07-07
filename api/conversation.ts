import request from './request'

export const conversationApi = {
  // 获取对话列表
  getList: (): Promise<PaginatedData<Conversation>> =>
    request.get('/conversations'),

  // 新建对话
  create: (): Promise<Conversation> =>
    request.post('/conversations'),

  // 删除对话
  delete: (id: string): Promise<void> =>
    request.delete(`/conversations/${id}`),

  // 获取对话消息
  getMessages: (conversationId: string): Promise<PaginatedData<Message>> =>
    request.get(`/conversations/${conversationId}/messages`),
}