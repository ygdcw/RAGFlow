import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Form, Input, Button, Card, message, Typography } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { authApi } from '../api/auth'
import { useAuthStore } from '../stores/useAuthStore'
import ParticleBackground from '../components/common/ParticleBackground'

const { Title } = Typography

export default function LoginPage() {
  const [loading, setLoading] = useState(false)
  const [hovered, setHovered] = useState(false)
  const navigate = useNavigate()
  const loginStore = useAuthStore((s) => s.login)

  const handleLogin = async (values: LoginRequest) => {
    setLoading(true)
    try {
      const res = await authApi.login(values)
      loginStore(res.user)
      message.success(`欢迎回来，${res.user.username}！`)
      if (res.user.role === 'admin') {
        navigate('/admin', { replace: true })
      } else {
        navigate('/chat', { replace: true })
      }
    } catch (err: any) {
      message.error(err.message || '登录失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh',
      position: 'relative',
    }}>
      <ParticleBackground />
      <Card
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        style={{
          width: 420,
          borderRadius: 20,
          boxShadow: hovered
            ? '0 30px 80px rgba(102,126,234,0.35)'
            : '0 20px 60px rgba(0,0,0,0.4)',
          background: hovered
            ? 'rgba(255,255,255,0.15)'
            : 'rgba(255,255,255,0.1)',
          backdropFilter: 'blur(30px)',
          WebkitBackdropFilter: 'blur(30px)',
          border: hovered
            ? '1px solid rgba(255,255,255,0.25)'
            : '1px solid rgba(255,255,255,0.15)',
          transform: hovered ? 'translateY(-6px)' : 'translateY(0)',
          transition: 'all 0.4s ease',
          zIndex: 1,
          position: 'relative',
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{
            width: 56,
            height: 56,
            margin: '0 auto 16px',
            borderRadius: 14,
            background: 'linear-gradient(135deg, #667eea, #764ba2)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 28,
            transform: hovered ? 'scale(1.08)' : 'scale(1)',
            transition: 'all 0.4s ease',
          }}>
            ✦
          </div>
          <Title level={3} style={{ marginBottom: 4, color: '#fff' }}>RAG 智能问答系统</Title>
          <p style={{ color: 'rgba(255,255,255,0.6)' }}>请登录以继续</p>
        </div>

        <Form onFinish={handleLogin} size="large" autoComplete="off">
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input
              prefix={<UserOutlined style={{ color: 'rgba(255,255,255,0.5)' }} />}
              placeholder="用户名"
              style={{
                borderRadius: 10,
                height: 46,
                background: 'rgba(255,255,255,0.08)',
                border: '1px solid rgba(255,255,255,0.12)',
                color: '#fff',
              }}
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined style={{ color: 'rgba(255,255,255,0.5)' }} />}
              placeholder="密码"
              style={{
                borderRadius: 10,
                height: 46,
                background: 'rgba(255,255,255,0.08)',
                border: '1px solid rgba(255,255,255,0.12)',
                color: '#fff',
              }}
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              style={{
                height: 46,
                borderRadius: 10,
                fontSize: 16,
                fontWeight: 500,
                background: 'linear-gradient(135deg, #667eea, #764ba2)',
                border: 'none',
              }}
            >
              登 录
            </Button>
          </Form.Item>
        </Form>

        <div style={{
          marginTop: 16,
          padding: '14px',
          background: 'rgba(255,255,255,0.06)',
          borderRadius: 10,
          fontSize: 13,
          color: 'rgba(255,255,255,0.6)',
          border: '1px solid rgba(255,255,255,0.08)',
        }}>
          <p style={{ fontWeight: 'bold', marginBottom: 6, color: 'rgba(255,255,255,0.7)' }}>测试账号：</p>
          <p>管理员：admin / admin123</p>
          <p>普通用户：user / user123</p>
        </div>
      </Card>
    </div>
  )
}