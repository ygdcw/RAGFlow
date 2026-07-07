import { http, HttpResponse, delay } from 'msw'

export const handlers = [
  // ========== 登录 ==========
  http.post('/api/v1/auth/login', async ({ request }) => {
    await delay(500)
    const body = await request.json() as LoginRequest

    if (body.username === 'admin' && body.password === 'admin123') {
      return HttpResponse.json({
        code: 200,
        data: {
          user: {
            id: 'u1',
            username: 'admin',
            role: 'admin',
            token: 'mock-admin-token-xyz',
          },
        },
        message: '登录成功',
      })
    }

    if (body.username === 'user' && body.password === 'user123') {
      return HttpResponse.json({
        code: 200,
        data: {
          user: {
            id: 'u2',
            username: 'user',
            role: 'user',
            token: 'mock-user-token-xyz',
          },
        },
        message: '登录成功',
      })
    }

    return HttpResponse.json(
      { code: 401, data: null, message: '用户名或密码错误' },
      { status: 401 }
    )
  }),

  http.get('/api/v1/auth/me', async ({ request }) => {
    await delay(200)
    const authHeader = request.headers.get('Authorization') || ''

    if (authHeader.includes('mock-admin-token')) {
      return HttpResponse.json({
        code: 200,
        data: {
          id: 'u1',
          username: 'admin',
          role: 'admin',
          token: 'mock-admin-token-xyz',
        },
        message: 'success',
      })
    }

    if (authHeader.includes('mock-user-token')) {
      return HttpResponse.json({
        code: 200,
        data: {
          id: 'u2',
          username: 'user',
          role: 'user',
          token: 'mock-user-token-xyz',
        },
        message: 'success',
      })
    }

    return HttpResponse.json(
      { code: 401, data: null, message: '未登录' },
      { status: 401 }
    )
  }),

  http.post('/api/v1/auth/logout', async () => {
    await delay(200)
    return HttpResponse.json({ code: 200, data: null, message: '已退出' })
  }),

  // ========== 知识库列表 ==========
  http.get('/api/v1/knowledge-bases', async () => {
    await delay(300)
    return HttpResponse.json({
      code: 200,
      data: {
        items: [
          { id: 'kb1', name: '项目文档库', doc_count: 3, created_at: '2026-07-01T10:00:00Z' },
          { id: 'kb2', name: '技术手册库', doc_count: 1, created_at: '2026-07-05T14:00:00Z' }
        ],
        total: 2,
        page: 1,
        page_size: 20
      },
      message: 'success'
    })
  }),

  // ========== 对话列表 ==========
  http.get('/api/v1/conversations', async () => {
    await delay(300)
    return HttpResponse.json({
      code: 200,
      data: {
        items: [
          { id: 'conv1', title: 'RAG系统架构讨论', created_at: '2026-07-07T10:00:00Z' },
          { id: 'conv2', title: '向量数据库选型', created_at: '2026-07-07T11:00:00Z' }
        ],
        total: 2,
        page: 1,
        page_size: 20
      },
      message: 'success'
    })
  }),

  // ========== 新建对话 ==========
  http.post('/api/v1/conversations', async () => {
    await delay(200)
    return HttpResponse.json({
      code: 200,
      data: { id: 'conv3', title: '新对话', created_at: new Date().toISOString() },
      message: 'success'
    })
  }),

  // ========== 删除对话 ==========
  http.delete('/api/v1/conversations/:id', async () => {
    await delay(200)
    return HttpResponse.json({ code: 200, data: null, message: '删除成功' })
  }),

  // ========== 对话消息列表 ==========
  http.get('/api/v1/conversations/:id/messages', async ({ params }) => {
    await delay(300)
    return HttpResponse.json({
      code: 200,
      data: {
        items: [
          { id: 'msg1', conversation_id: params.id, role: 'user', content: '什么是RAG？', created_at: '2026-07-07T10:00:00Z' },
          { id: 'msg2', conversation_id: params.id, role: 'assistant', content: 'RAG（Retrieval-Augmented Generation）是检索增强生成技术，它结合了信息检索和文本生成...', status: 'done', created_at: '2026-07-07T10:00:05Z' },
          { id: 'msg3', conversation_id: params.id, role: 'user', content: '它有什么优点？', created_at: '2026-07-07T10:01:00Z' },
          { id: 'msg4', conversation_id: params.id, role: 'assistant', content: 'RAG的主要优点包括：1. 知识实时更新 2. 答案可溯源 3. 减少幻觉...', sources: [{ doc_id: 'doc1', filename: 'RAG综述.pdf', chunk_text: 'RAG的优势在于...' }], status: 'done', created_at: '2026-07-07T10:01:10Z' }
        ],
        total: 4,
        page: 1,
        page_size: 50
      },
      message: 'success'
    })
  }),

  // ========== 发送消息（SSE流式模拟） ==========
  http.post('/api/v1/chat/send', async ({ request }) => {
    const body = await request.json() as { question: string; conversation_id: string }

    const encoder = new TextEncoder()
    const fullAnswer = `关于"${body.question}"，根据知识库中的资料，我为您总结如下：RAG技术是当前大语言模型应用的重要方向，它有效解决了模型知识滞后和幻觉问题。在实际应用中，RAG系统通常包括文档解析、文本分块、向量化存储、语义检索和答案生成五个核心环节。`

    const stream = new ReadableStream({
      start(controller) {
        let index = 0
        const timer = setInterval(() => {
          if (index < fullAnswer.length) {
            const chunk = JSON.stringify({ type: 'token', content: fullAnswer[index] })
            controller.enqueue(encoder.encode(`data: ${chunk}\n\n`))
            index++
          } else {
            const sources = JSON.stringify({
              type: 'sources',
              documents: [
                { doc_id: 'doc1', filename: 'RAG技术白皮书.pdf', chunk_text: 'RAG技术是当前大语言模型应用的重要方向...' }
              ]
            })
            controller.enqueue(encoder.encode(`data: ${sources}\n\n`))
            controller.enqueue(encoder.encode(`data: ${JSON.stringify({ type: 'done' })}\n\n`))
            clearInterval(timer)
            controller.close()
          }
        }, 30)
      }
    })

    return new HttpResponse(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive'
      }
    })
  }),

  // ========== 文件上传 ==========
  http.post('/api/v1/documents/upload', async () => {
    await delay(1500)
    return HttpResponse.json({
      code: 200,
      data: { id: 'doc_new', knowledge_base_id: 'kb1', filename: '新上传文档.pdf', status: 'processing', created_at: new Date().toISOString() },
      message: '上传成功'
    })
  }),

  // ========== 删除文档 ==========
  http.delete('/api/v1/documents/:id', async () => {
    await delay(200)
    return HttpResponse.json({ code: 200, data: null, message: '删除成功' })
  }),

  // ========== 知识库管理 ==========
  http.post('/api/v1/knowledge-bases', async ({ request }) => {
    await delay(300)
    const body = await request.json() as { name: string }
    return HttpResponse.json({
      code: 200,
      data: { id: 'kb' + Date.now(), name: body.name, doc_count: 0, created_at: new Date().toISOString() },
      message: '创建成功',
    })
  }),

  http.delete('/api/v1/knowledge-bases/:id', async () => {
    await delay(300)
    return HttpResponse.json({ code: 200, data: null, message: '删除成功' })
  }),

  http.get('/api/v1/knowledge-bases/:id/documents', async ({ params }) => {
    await delay(300)
    return HttpResponse.json({
      code: 200,
      data: {
        items: [
          { id: 'doc1', knowledge_base_id: params.id as string, filename: 'RAG技术白皮书.pdf', status: 'ready', created_at: '2026-07-01T10:00:00Z' },
          { id: 'doc2', knowledge_base_id: params.id as string, filename: '向量数据库对比.docx', status: 'ready', created_at: '2026-07-02T14:00:00Z' },
          { id: 'doc3', knowledge_base_id: params.id as string, filename: '系统架构设计.pptx', status: 'processing', created_at: '2026-07-05T09:00:00Z' },
        ],
        total: 3,
        page: 1,
        page_size: 20,
      },
      message: 'success',
    })
  }),

  // ========== 管理后台：用户管理 ==========
  http.get('/api/v1/admin/users', async () => {
    await delay(300)
    return HttpResponse.json({
      code: 200,
      data: [
        { id: 'u1', username: 'admin', role: 'admin', created_at: '2026-06-01T10:00:00Z', last_login: '2026-07-07T09:30:00Z', status: 'active' },
        { id: 'u2', username: 'user', role: 'user', created_at: '2026-06-15T14:00:00Z', last_login: '2026-07-07T08:00:00Z', status: 'active' },
        { id: 'u3', username: 'zhangsan', role: 'user', created_at: '2026-06-20T09:00:00Z', last_login: '2026-07-06T16:00:00Z', status: 'disabled' },
      ],
      message: 'success',
    })
  }),

  http.post('/api/v1/admin/users', async () => {
    await delay(300)
    return HttpResponse.json({ code: 200, data: null, message: '用户添加成功' })
  }),

  http.delete('/api/v1/admin/users/:id', async () => {
    await delay(300)
    return HttpResponse.json({ code: 200, data: null, message: '用户删除成功' })
  }),

  http.put('/api/v1/admin/users/:id/toggle', async () => {
    await delay(300)
    return HttpResponse.json({ code: 200, data: null, message: '状态更新成功' })
  }),

  // ========== 管理后台：系统监控 ==========
  http.get('/api/v1/admin/stats', async () => {
    await delay(500)
    return HttpResponse.json({
      code: 200,
      data: {
        total_users: 12,
        total_documents: 45,
        total_questions: 1283,
        avg_response_time: 1.8,
        cpu_usage: 34.5,
        memory_usage: 62.1,
        disk_usage: 48.3,
      },
      message: 'success',
    })
  }),

  // ========== 管理后台：操作日志 ==========
  http.get('/api/v1/admin/logs', async () => {
    await delay(300)
    return HttpResponse.json({
      code: 200,
      data: [
        { id: 'log1', user: 'admin', action: '删除用户', detail: '删除了用户 zhangsan', created_at: '2026-07-07T10:30:00Z' },
        { id: 'log2', user: 'admin', action: '上传文档', detail: '上传了 RAG技术白皮书.pdf', created_at: '2026-07-07T09:15:00Z' },
        { id: 'log3', user: 'user', action: '提问', detail: '什么是RAG？', created_at: '2026-07-07T08:45:00Z' },
        { id: 'log4', user: 'admin', action: '添加用户', detail: '添加了用户 lisi', created_at: '2026-07-06T16:20:00Z' },
      ],
      message: 'success',
    })
  }),

  // ========== 管理后台：知识库管理 ==========
  http.get('/api/v1/admin/knowledge-bases', async () => {
    await delay(300)
    return HttpResponse.json({
      code: 200,
      data: [
        { id: 'kb1', name: '项目文档库', doc_count: 12, owner: 'admin', created_at: '2026-06-01T10:00:00Z', status: 'active' },
        { id: 'kb2', name: '技术手册库', doc_count: 5, owner: 'admin', created_at: '2026-06-15T14:00:00Z', status: 'active' },
        { id: 'kb3', name: '测试知识库', doc_count: 0, owner: 'user', created_at: '2026-07-01T09:00:00Z', status: 'empty' },
      ],
      message: 'success',
    })
  }),

  http.delete('/api/v1/admin/knowledge-bases/:id', async () => {
    await delay(300)
    return HttpResponse.json({ code: 200, data: null, message: '知识库已删除' })
  }),

    // ========== 管理后台：文档管理 ==========
  http.get('/api/v1/admin/documents', async () => {
    await delay(300)
    return HttpResponse.json({
      code: 200,
      data: [
        { id: 'doc1', filename: 'RAG技术白皮书.pdf', knowledge_base: '项目文档库', size: '2.4 MB', status: 'ready', tags: ['RAG', '技术'], created_at: '2026-07-01T10:00:00Z' },
        { id: 'doc2', filename: '向量数据库对比.docx', knowledge_base: '技术手册库', size: '1.1 MB', status: 'ready', tags: ['数据库'], created_at: '2026-07-02T14:00:00Z' },
        { id: 'doc3', filename: '系统架构设计.pptx', knowledge_base: '项目文档库', size: '5.8 MB', status: 'processing', tags: ['架构'], created_at: '2026-07-05T09:00:00Z' },
        { id: 'doc4', filename: '用户手册.md', knowledge_base: '项目文档库', size: '0.3 MB', status: 'error', tags: ['文档'], created_at: '2026-07-06T11:00:00Z' },
      ],
      message: 'success',
    })
  }),

  http.delete('/api/v1/admin/documents/:id', async () => {
    await delay(300)
    return HttpResponse.json({ code: 200, data: null, message: '文档已删除' })
  }),

  http.post('/api/v1/admin/documents/:id/reparse', async () => {
    await delay(1000)
    return HttpResponse.json({ code: 200, data: null, message: '重新解析已触发' })
  }),

  http.put('/api/v1/admin/documents/:id/tags', async () => {
    await delay(300)
    return HttpResponse.json({ code: 200, data: null, message: '标签已更新' })
  }),
    // ========== 管理后台：创建知识库 ==========
  http.post('/api/v1/admin/knowledge-bases', async ({ request }) => {
    await delay(300)
    const body = await request.json() as { name: string }
    return HttpResponse.json({ code: 200, data: null, message: '创建成功' })
  }),

  // ========== 管理后台：上传文档 ==========
  http.post('/api/v1/admin/documents/upload', async () => {
    await delay(1500)
    return HttpResponse.json({ code: 200, data: null, message: '上传成功' })
  }),
]