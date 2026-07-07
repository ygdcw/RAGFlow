import { create } from 'zustand'
import { knowledgeApi } from '../api/knowledge'

interface KnowledgeState {
  knowledgeBases: KnowledgeBase[]
  currentKnowledgeBase: KnowledgeBase | null
  documents: Document[]
  loading: boolean
  uploadProgress: number
  isUploading: boolean

  loadKnowledgeBases: () => Promise<void>
  setCurrentKnowledgeBase: (kb: KnowledgeBase | null) => void
  loadDocuments: (kbId: string) => Promise<void>
  uploadDocument: (kbId: string, file: File) => Promise<void>
  deleteDocument: (docId: string) => Promise<void>
  setUploadProgress: (progress: number) => void
  setIsUploading: (v: boolean) => void
}

export const useKnowledgeStore = create<KnowledgeState>((set, get) => ({
  knowledgeBases: [],
  currentKnowledgeBase: null,
  documents: [],
  loading: false,
  uploadProgress: 0,
  isUploading: false,

  loadKnowledgeBases: async () => {
    set({ loading: true })
    try {
      const data = await knowledgeApi.getList()
      set({ knowledgeBases: data.items })
    } finally {
      set({ loading: false })
    }
  },

  setCurrentKnowledgeBase: (kb) => {
    set({ currentKnowledgeBase: kb, documents: [] })
    if (kb) {
      get().loadDocuments(kb.id)
    }
  },

  loadDocuments: async (kbId: string) => {
    set({ loading: true })
    try {
      const data = await knowledgeApi.getDocuments(kbId)
      set({ documents: data.items })
    } finally {
      set({ loading: false })
    }
  },

  uploadDocument: async (kbId: string, file: File) => {
    set({ isUploading: true, uploadProgress: 0 })

    // 模拟进度更新
    const progressInterval = setInterval(() => {
      set((state) => ({
        uploadProgress: Math.min(state.uploadProgress + 10, 90),
      }))
    }, 200)

    try {
      await knowledgeApi.upload(kbId, file)
      clearInterval(progressInterval)
      set({ uploadProgress: 100, isUploading: false })
      // 重新加载文档列表
      get().loadDocuments(kbId)
    } catch {
      clearInterval(progressInterval)
      set({ isUploading: false, uploadProgress: 0 })
    }
  },

  deleteDocument: async (docId: string) => {
    await knowledgeApi.deleteDocument(docId)
    const { currentKnowledgeBase } = get()
    if (currentKnowledgeBase) {
      get().loadDocuments(currentKnowledgeBase.id)
    }
  },

  setUploadProgress: (progress) => set({ uploadProgress: progress }),
  setIsUploading: (v) => set({ isUploading: v }),
}))