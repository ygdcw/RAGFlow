import { create } from 'zustand'
import { conversationApi } from '../api/conversation'

interface ChatState {
  conversations: Conversation[]
  currentConversationId: string | null
  messages: Message[]
  isStreaming: boolean
  loadingMessages: boolean

  loadConversations: () => Promise<void>
  createConversation: () => Promise<string>
  deleteConversation: (id: string) => Promise<void>
  switchConversation: (id: string) => Promise<void>
  setMessages: (msgs: Message[]) => void
  addMessage: (msg: Message) => void
  appendToLastAssistant: (text: string) => void
  setLastMessageStatus: (status: Message['status']) => void
  setLastMessageSources: (sources: SourceDocument[]) => void
  setStreaming: (v: boolean) => void
  clearMessages: () => void
}

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: [],
  currentConversationId: null,
  messages: [],
  isStreaming: false,
  loadingMessages: false,

  // 加载对话列表
  loadConversations: async () => {
    try {
      const data = await conversationApi.getList()
      set({ conversations: data.items })
    } catch {
      // 静默失败
    }
  },

  // 创建新对话
  createConversation: async () => {
    const conv = await conversationApi.create()
    set((state) => ({
      conversations: [conv, ...state.conversations],
      currentConversationId: conv.id,
      messages: [],
    }))
    return conv.id
  },

  // 删除对话
  deleteConversation: async (id: string) => {
    await conversationApi.delete(id)
    const { currentConversationId, conversations } = get()
    const newList = conversations.filter((c) => c.id !== id)
    
    // 如果删除的是当前对话，切换到第一个或清空
    if (currentConversationId === id) {
      const next = newList[0]
      set({
        conversations: newList,
        currentConversationId: next?.id || null,
        messages: [],
      })
      if (next) {
        get().switchConversation(next.id)
      }
    } else {
      set({ conversations: newList })
    }
  },

  // 切换对话
  switchConversation: async (id: string) => {
    set({ currentConversationId: id, loadingMessages: true })
    try {
      const data = await conversationApi.getMessages(id)
      set({ messages: data.items, loadingMessages: false })
    } catch {
      set({ messages: [], loadingMessages: false })
    }
  },

  setMessages: (msgs) => set({ messages: msgs }),

  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),

  appendToLastAssistant: (text) =>
    set((state) => {
      const msgs = [...state.messages]
      const last = msgs[msgs.length - 1]
      if (last && last.role === 'assistant') {
        msgs[msgs.length - 1] = { ...last, content: last.content + text }
      }
      return { messages: msgs }
    }),

  setLastMessageStatus: (status) =>
    set((state) => {
      const msgs = [...state.messages]
      const last = msgs[msgs.length - 1]
      if (last) {
        msgs[msgs.length - 1] = { ...last, status }
      }
      return { messages: msgs }
    }),

  setLastMessageSources: (sources) =>
    set((state) => {
      const msgs = [...state.messages]
      const last = msgs[msgs.length - 1]
      if (last && last.role === 'assistant') {
        msgs[msgs.length - 1] = { ...last, sources }
      }
      return { messages: msgs }
    }),

  setStreaming: (v) => set({ isStreaming: v }),

  clearMessages: () => set({ messages: [], currentConversationId: null }),
}))