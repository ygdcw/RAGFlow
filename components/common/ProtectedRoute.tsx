import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../stores/useAuthStore'

interface Props {
  children: React.ReactNode
  requiredRole?: 'user' | 'admin'
}

export default function ProtectedRoute({ children, requiredRole }: Props) {
  const { isLoggedIn, isAdmin } = useAuthStore()
  const location = useLocation()

  // 未登录 → 去登录页
  if (!isLoggedIn) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  // 需要管理员但当前不是 → 去聊天页
  if (requiredRole === 'admin' && !isAdmin) {
    return <Navigate to="/chat" replace />
  }

  return <>{children}</>
}