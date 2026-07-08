// ========== 统一响应格式 ==========
interface ApiResponse<T = any> {
  code: number
  data: T
  message: string
}

interface PaginatedData<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

// ========== 知识库 ==========
interface KnowledgeBase {
  id: string
  name: string
  doc_count: number
  created_at: string
}

// ========== 文档 ==========
interface Document {
  id: string
  knowledge_base_id: string
  filename: string
  status: 'processing' | 'ready' | 'error'
  created_at: string
}

// ========== 对话 ==========
interface Conversation {
  id: string
  title: string
  created_at: string
}

interface Message {
  id: string
  conversation_id: string
  role: 'user' | 'assistant'
  content: string
  sources?: SourceDocument[]
  status?: 'generating' | 'done' | 'stopped' | 'error'
  created_at: string
}

interface SourceDocument {
  doc_id: string
  filename: string
  chunk_text: string
}

// ========== SSE事件 ==========
type SSEEvent =
  | { type: 'token'; content: string }
  | { type: 'sources'; documents: SourceDocument[] }
  | { type: 'done' }

  // ========== 用户与登录 ==========
interface User {
  id: string
  username: string
  role: 'user' | 'admin'
  token: string
}

interface LoginRequest {
  username: string
  password: string
}

interface LoginResponse {
  user: User
}

// ========== 管理后台 ==========
interface AdminUser {
  id: string
  username: string
  role: 'user' | 'admin'
  created_at: string
  last_login: string
  status: 'active' | 'disabled'
}

interface SystemStats {
  total_users: number
  total_documents: number
  total_questions: number
  avg_response_time: number
  cpu_usage: number
  memory_usage: number
  disk_usage: number
}

interface OperationLog {
  id: string
  user: string
  action: string
  detail: string
  created_at: string
}

// ========== 管理后台扩展 ==========
interface AdminKnowledgeBase {
  id: string
  name: string
  doc_count: number
  owner: string
  created_at: string
  status: 'active' | 'empty'
}

interface AdminDocument {
  id: string
  filename: string
  knowledge_base: string
  size: string
  status: 'processing' | 'ready' | 'error'
  tags: string[]
  created_at: string
}