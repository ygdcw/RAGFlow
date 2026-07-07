import { create } from 'zustand'

interface AuthState {
  user: User | null
  isLoggedIn: boolean
  isAdmin: boolean

  login: (user: User) => void
  logout: () => void
  initFromStorage: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoggedIn: false,
  isAdmin: false,

  login: (user) => {
    localStorage.setItem('user', JSON.stringify(user))
    set({ user, isLoggedIn: true, isAdmin: user.role === 'admin' })
  },

  logout: () => {
    localStorage.removeItem('user')
    set({ user: null, isLoggedIn: false, isAdmin: false })
  },

  initFromStorage: () => {
    const stored = localStorage.getItem('user')
    if (stored) {
      const user: User = JSON.parse(stored)
      set({ user, isLoggedIn: true, isAdmin: user.role === 'admin' })
    }
  },
}))