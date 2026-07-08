import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import rehypeHighlight from 'rehype-highlight'
import remarkGfm from 'remark-gfm'
import 'highlight.js/styles/github-dark.css'
import { UserOutlined, RobotOutlined } from '@ant-design/icons'

interface Props {
  message: Message
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user'
  const [hovered, setHovered] = useState(false)

  const statusConfig: Record<string, { text: string; color: string }> = {
    generating: { text: '● 生成中', color: '#667eea' },
    stopped: { text: '◇ 已停止', color: '#888' },
    error: { text: '✕ 生成失败', color: '#ff4d4f' },
    done: { text: '', color: '' },
  }

  const status = message.status ? statusConfig[message.status] : null

  return (
    <div className="fade-in" style={{
      display: 'flex',
      gap: 12,
      marginBottom: 20,
      flexDirection: isUser ? 'row-reverse' : 'row',
      alignItems: 'flex-start',
    }}>
      {/* 头像 */}
      <div style={{
        width: 38,
        height: 38,
        borderRadius: 10,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: isUser
          ? 'linear-gradient(135deg, #667eea, #764ba2)'
          : 'linear-gradient(135deg, #11998e, #38ef7d)',
        flexShrink: 0,
        boxShadow: hovered
          ? (isUser ? '0 4px 18px rgba(102,126,234,0.6)' : '0 4px 18px rgba(17,153,142,0.6)')
          : (isUser ? '0 2px 12px rgba(102,126,234,0.4)' : '0 2px 12px rgba(17,153,142,0.4)'),
        transform: hovered ? 'scale(1.06)' : 'scale(1)',
        transition: 'all 0.25s ease',
      }}>
        {isUser ? (
          <UserOutlined style={{ color: '#fff', fontSize: 18 }} />
        ) : (
          <RobotOutlined style={{ color: '#fff', fontSize: 18 }} />
        )}
      </div>

      {/* 内容区 */}
      <div
        style={{ maxWidth: '75%', minWidth: 100 }}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
      >
        {/* 消息主体 */}
        <div style={{
          padding: '14px 18px',
          borderRadius: 16,
          borderBottomRightRadius: isUser ? 4 : 16,
          borderBottomLeftRadius: isUser ? 16 : 4,
          background: isUser
            ? 'linear-gradient(135deg, #667eea, #764ba2)'
            : hovered
              ? 'rgba(255,255,255,0.12)'
              : 'rgba(255,255,255,0.06)',
          color: isUser ? '#fff' : '#e0e0e0',
          boxShadow: hovered
            ? (isUser ? '0 4px 20px rgba(102,126,234,0.45)' : '0 4px 16px rgba(0,0,0,0.35)')
            : (isUser ? '0 2px 12px rgba(102,126,234,0.3)' : '0 2px 8px rgba(0,0,0,0.2)'),
          border: isUser
            ? 'none'
            : hovered
              ? '1px solid rgba(255,255,255,0.14)'
              : '1px solid rgba(255,255,255,0.06)',
          lineHeight: 1.8,
          transform: hovered ? 'translateY(-2px)' : 'translateY(0)',
          transition: 'all 0.25s ease',
          cursor: 'default',
        }}>
          {isUser ? (
            <span>{message.content}</span>
          ) : (
            <div>
              {message.content ? (
                <ReactMarkdown
                  rehypePlugins={[rehypeHighlight]}
                  remarkPlugins={[remarkGfm]}
                >
                  {message.content}
                </ReactMarkdown>
              ) : (
                <span style={{ color: '#667eea' }}>
                  <span className="typing-cursor">▋</span>
                </span>
              )}
            </div>
          )}
        </div>

        {/* 引用来源 */}
        {message.sources && message.sources.length > 0 && (
          <div style={{
            marginTop: 8,
            padding: '10px 14px',
            background: 'rgba(255,255,255,0.04)',
            borderRadius: 10,
            border: '1px solid rgba(255,255,255,0.06)',
            transition: 'all 0.25s ease',
          }}>
            <div style={{ fontSize: 12, color: '#888', marginBottom: 6, fontWeight: 500 }}>
              📚 引用来源
            </div>
            {message.sources.map((s, i) => (
              <div key={i} style={{
                fontSize: 13,
                color: '#aaa',
                padding: '3px 0',
                display: 'flex',
                alignItems: 'center',
                gap: 6,
              }}>
                <span style={{ color: '#667eea' }}>📄</span>
                {s.filename}
              </div>
            ))}
          </div>
        )}

        {/* 状态提示 */}
        {status && status.text && (
          <div style={{
            marginTop: 6,
            fontSize: 12,
            color: status.color,
            fontWeight: 500,
          }}>
            {status.text}
          </div>
        )}
      </div>
    </div>
  )
}