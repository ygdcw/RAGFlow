import { useState, useRef, useEffect } from 'react'
import { Input, Button, Space, Empty } from 'antd'
import { SendOutlined, StopOutlined } from '@ant-design/icons'
import { useChatStore } from '../../stores/useChatStore'
import { createChatSSE } from '../../api/sse'
import MessageBubble from './MessageBubble'

export default function ChatWindow() {
  const {
    messages, isStreaming, currentConversationId,
    addMessage, appendToLastAssistant,
    setLastMessageStatus, setLastMessageSources, setStreaming,
    createConversation, loadConversations,
  } = useChatStore()

  const [inputValue, setInputValue] = useState('')
  const abortRef = useRef<AbortController | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    const text = inputValue.trim()
    if (!text || isStreaming) return

    let convId = currentConversationId
    if (!convId) {
      try {
        convId = await createConversation()
      } catch {
        convId = 'temp_' + Date.now()
      }
    }

    addMessage({
      id: Date.now().toString(),
      conversation_id: convId,
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    })

    addMessage({
      id: (Date.now() + 1).toString(),
      conversation_id: convId,
      role: 'assistant',
      content: '',
      status: 'generating',
      created_at: new Date().toISOString(),
    })

    setInputValue('')
    setStreaming(true)

    abortRef.current = createChatSSE(text, convId, {
      onMessage: (token) => appendToLastAssistant(token),
      onDone: () => {
        setLastMessageStatus('done')
        setStreaming(false)
        abortRef.current = null
        loadConversations()
      },
      onError: (err) => {
        appendToLastAssistant(`\n\n[错误: ${err}]`)
        setLastMessageStatus('error')
        setStreaming(false)
        abortRef.current = null
      },
      onRetrieve: (docs) => setLastMessageSources(docs),
    })
  }

  const handleStop = () => {
    abortRef.current?.abort()
    setLastMessageStatus('stopped')
    setStreaming(false)
    abortRef.current = null
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '24px',
        background: 'transparent',
      }}>
        {messages.length === 0 ? (
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            height: '100%',
          }}>
            <Empty
              description={
                <span style={{ color: 'rgba(255,255,255,0.5)' }}>
                  👋 欢迎使用智能问答系统<br />
                  <span style={{ fontSize: 13, color: 'rgba(255,255,255,0.3)' }}>点击左侧「新对话」开始，或直接输入问题</span>
                </span>
              }
            />
          </div>
        ) : (
          messages.map(msg => (
            <MessageBubble key={msg.id} message={msg} />
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <div style={{
        padding: '16px 24px',
        borderTop: '1px solid rgba(255,255,255,0.06)',
        background: 'rgba(255,255,255,0.03)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
      }}>
        <Space.Compact style={{ width: '100%' }}>
          <Input.TextArea
            className="chat-input"
            value={inputValue}
            onChange={e => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入你的问题... (Enter 发送, Shift+Enter 换行)"
            autoSize={{ minRows: 1, maxRows: 4 }}
            disabled={isStreaming}
            style={{
              resize: 'none',
              background: 'rgba(255,255,255,0.06)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '10px 0 0 10px',
              color: '#e0e0e0',
            }}
          />
          {isStreaming ? (
            <Button type="primary" danger icon={<StopOutlined />} onClick={handleStop}
              style={{ borderRadius: '0 10px 10px 0', height: 'auto' }}>
              停止
            </Button>
          ) : (
            <Button type="primary" icon={<SendOutlined />} onClick={handleSend}
              disabled={!inputValue.trim()}
              style={{
                borderRadius: '0 10px 10px 0',
                height: 'auto',
                background: 'linear-gradient(135deg, #667eea, #764ba2)',
                border: 'none',
              }}>
              发送
            </Button>
          )}
        </Space.Compact>
      </div>
    </div>
  )
}