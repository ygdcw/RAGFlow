import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button, Modal, Typography, Spin, Empty, message } from 'antd'
import { PlusOutlined, DeleteOutlined, MessageOutlined, MenuFoldOutlined, MenuUnfoldOutlined, SettingOutlined } from '@ant-design/icons'
import { useChatStore } from '../../stores/useChatStore'
import { useAuthStore } from '../../stores/useAuthStore'
import ParticleBackground from '../common/ParticleBackground'
import ChatWindow from './ChatWindow'

const { Text } = Typography

export default function ChatLayout() {
  const navigate = useNavigate()

  const {
    conversations, currentConversationId, loadingMessages,
    loadConversations, createConversation, deleteConversation, switchConversation,
  } = useChatStore()

  const isAdmin = useAuthStore((s) => s.isAdmin)

  const [collapsed, setCollapsed] = useState(false)
  const [creating, setCreating] = useState(false)
  const [hoveredConvId, setHoveredConvId] = useState<string | null>(null)

  useEffect(() => {
    loadConversations()
  }, [])

  const handleCreate = async () => {
    setCreating(true)
    try {
      await createConversation()
    } catch {
      message.error('创建对话失败')
    } finally {
      setCreating(false)
    }
  }

  const handleDelete = (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    Modal.confirm({
      title: '确认删除',
      content: '删除后对话记录不可恢复，确定继续吗？',
      okButtonProps: { danger: true },
      onOk: async () => {
        try {
          await deleteConversation(id)
          message.success('对话已删除')
        } catch {
          message.error('删除失败')
        }
      },
    })
  }

  const formatTime = (dateStr: string) => {
    const d = new Date(dateStr)
    const now = new Date()
    const diff = now.getTime() - d.getTime()
    if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
    if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
    return d.toLocaleDateString('zh-CN')
  }

  return (
    <div style={{ position: 'relative', height: '100vh', display: 'flex' }}>
      <ParticleBackground />

      {/* 左侧对话历史 */}
      {!collapsed && (
        <div style={{
          width: 280,
          height: '100vh',
          background: 'rgba(15,15,35,0.92)',
          borderRight: '1px solid rgba(255,255,255,0.06)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          display: 'flex',
          flexDirection: 'column',
          flexShrink: 0,
          zIndex: 1,
          position: 'relative',
        }}>
          <div style={{
            padding: '20px 16px',
            borderBottom: '1px solid rgba(255,255,255,0.06)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexShrink: 0,
          }}>
            <Text strong style={{ fontSize: 16, color: '#e0e0e0' }}>对话历史</Text>
            <Button type="primary" size="small" icon={<PlusOutlined />} onClick={handleCreate} loading={creating}
              style={{ borderRadius: 8 }}
            >
              新对话
            </Button>
          </div>

          <div style={{ flex: 1, overflowY: 'auto' }}>
            {conversations.length === 0 ? (
              <Empty
                description={<span style={{ color: '#666' }}>暂无对话</span>}
                style={{ marginTop: 60 }}
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            ) : (
              conversations.map((item) => {
                const isActive = item.id === currentConversationId
                const isHovered = hoveredConvId === item.id

                return (
                  <div
                    key={item.id}
                    onClick={() => switchConversation(item.id)}
                    onMouseEnter={() => setHoveredConvId(item.id)}
                    onMouseLeave={() => setHoveredConvId(null)}
                    style={{
                      padding: '14px 16px',
                      cursor: 'pointer',
                      background: isActive
                        ? 'rgba(102,126,234,0.18)'
                        : isHovered
                          ? 'rgba(255,255,255,0.05)'
                          : 'transparent',
                      borderLeft: isActive
                        ? '3px solid #667eea'
                        : '3px solid transparent',
                      borderBottom: '1px solid rgba(255,255,255,0.04)',
                      transform: isHovered && !isActive ? 'translateX(4px)' : 'translateX(0)',
                      transition: 'all 0.25s ease',
                      display: 'flex',
                      alignItems: 'center',
                    }}
                  >
                    <div style={{ flex: 1, overflow: 'hidden' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <MessageOutlined style={{ color: '#667eea', fontSize: 14 }} />
                        <Text ellipsis style={{ flex: 1, fontSize: 14, color: '#d0d0d0' }}>
                          {item.title}
                        </Text>
                      </div>
                      <Text style={{ fontSize: 12, marginLeft: 22, color: '#666' }}>
                        {formatTime(item.created_at)}
                      </Text>
                    </div>
                    <Button
                      type="text"
                      size="small"
                      danger
                      icon={<DeleteOutlined />}
                      onClick={(e) => handleDelete(e, item.id)}
                      style={{ opacity: isHovered ? 0.8 : 0.4, transition: 'opacity 0.2s' }}
                    />
                  </div>
                )
              })
            )}
          </div>
        </div>
      )}

      {/* 右侧对话窗口 */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        position: 'relative',
        zIndex: 1,
        background: 'transparent',
      }}>
        <div style={{
          padding: '4px 12px',
          background: 'rgba(255,255,255,0.03)',
          borderBottom: '1px solid rgba(255,255,255,0.06)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          flexShrink: 0,
        }}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            style={{ color: '#ccc' }}
          />
          {isAdmin && (
            <Button
              type="link"
              icon={<SettingOutlined />}
              onClick={() => navigate('/admin')}
              style={{ color: '#aac8ff' }}
            >
              管理后台
            </Button>
          )}
        </div>
        <div style={{ flex: 1, background: 'transparent', overflow: 'hidden' }}>
          {loadingMessages ? (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
              <Spin size="large" />
            </div>
          ) : (
            <ChatWindow />
          )}
        </div>
      </div>
    </div>
  )
}