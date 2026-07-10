import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Layout, Menu, Card, Table, Button, Modal, Form, Input, Select,
  Statistic, Row, Col, Tag, Space, message, Typography, Popconfirm, Spin
} from 'antd'
import {
  UserOutlined, DashboardOutlined, FileTextOutlined,
  LogoutOutlined, PlusOutlined, DeleteOutlined,
  StopOutlined, CheckCircleOutlined, BookOutlined,
  ReloadOutlined, EditOutlined, ToolOutlined, UploadOutlined,
  RocketOutlined, FolderOpenOutlined, LoadingOutlined,
  EyeOutlined,
} from '@ant-design/icons'
import { useAuthStore } from '../stores/useAuthStore'
import { adminApi } from '../api/admin'
import request from '../api/request'
import ParticleBackground from '../components/common/ParticleBackground'

const { Sider, Content } = Layout
const { Title, Paragraph } = Typography

type MenuKey = 'dashboard' | 'users' | 'knowledge' | 'documents' | 'logs'

export default function AdminPage() {
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()
  const [activeMenu, setActiveMenu] = useState<MenuKey>('dashboard')

  const [stats, setStats] = useState<SystemStats | null>(null)
  const [users, setUsers] = useState<AdminUser[]>([])
  const [logs, setLogs] = useState<OperationLog[]>([])
  const [kbList, setKbList] = useState<AdminKnowledgeBase[]>([])
  const [docList, setDocList] = useState<AdminDocument[]>([])
  const [docTotal, setDocTotal] = useState(0)
  const [docPage, setDocPage] = useState(1)
  const [loading, setLoading] = useState(false)

  const [addUserOpen, setAddUserOpen] = useState(false)
  const [addUserForm] = Form.useForm()
  const [createKBOpen, setCreateKBOpen] = useState(false)
  const [createKBForm] = Form.useForm()
  const [uploadDocOpen, setUploadDocOpen] = useState(false)
  const [uploadForm] = Form.useForm()
  const [tagModalOpen, setTagModalOpen] = useState(false)
  const [editingDoc, setEditingDoc] = useState<AdminDocument | null>(null)
  const [tagForm] = Form.useForm()

  const [appliedKB, setAppliedKB] = useState<string | null>(() => {
    const saved = localStorage.getItem('appliedKB')
    return saved ? JSON.parse(saved) : null
  })
  const [applyingKB, setApplyingKB] = useState<string | null>(null)
  const [importModalOpen, setImportModalOpen] = useState(false)
  const [selectedKBForImport, setSelectedKBForImport] = useState<string | null>(null)
  const [importFile, setImportFile] = useState<File | null>(null)
  const [importLoading, setImportLoading] = useState(false)
  const [, setImportProgress] = useState(0)
  const [manageModalOpen, setManageModalOpen] = useState(false)
  const [selectedKBForManage, setSelectedKBForManage] = useState<string | null>(null)
  const [kbDocuments, setKbDocuments] = useState<AdminDocument[]>([])
  const [manageLoading, setManageLoading] = useState(false)
  
  const [managePage, setManagePage] = useState(1)
  const [manageTotal, setManageTotal] = useState(0)
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([])
  const [viewDocModalOpen, setViewDocModalOpen] = useState(false)
  const [viewingDoc, setViewingDoc] = useState<{ id: string; content: string; filename: string } | null>(null)

  const fileInputRef = useRef<HTMLInputElement>(null)

  const [hoveredCard, setHoveredCard] = useState<string | null>(null)
  const [hoveredMain, setHoveredMain] = useState(false)

  useEffect(() => {
    loadData()
  }, [activeMenu])

  useEffect(() => {
    request.get('/knowledge-bases/applied').then((res: any) => {
      if (res.id) {
        setAppliedKB(res.id)
        localStorage.setItem('appliedKB', JSON.stringify(res.id))
      }
    }).catch(() => {})
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      switch (activeMenu) {
        case 'dashboard':
          setStats(await adminApi.getSystemStats())
          break
        case 'users':
          setUsers(await adminApi.getUserList())
          break
        case 'knowledge':
          setKbList(await adminApi.getAllKnowledgeBases())
          break
        case 'documents':
          const docResult = await adminApi.getAllDocuments({ page: docPage, page_size: 10 })
          setDocList(docResult.items)
          setDocTotal(docResult.total)
          break
        case 'logs':
          setLogs(await adminApi.getOperationLogs())
          break
      }
    } catch (err: any) {
      message.error(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleAddUser = async (values: { username: string; password: string; role: string }) => {
    await adminApi.addUser(values)
    message.success('用户添加成功')
    setAddUserOpen(false)
    addUserForm.resetFields()
    loadData()
  }

  const handleDeleteUser = (userId: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个用户吗？',
      onOk: async () => {
        await adminApi.deleteUser(userId)
        message.success('删除成功')
        loadData()
      },
    })
  }

  const handleToggleUser = async (userId: string) => {
    await adminApi.toggleUserStatus(userId)
    message.success('状态已更新')
    loadData()
  }

  const handleCreateKB = async (values: { name: string }) => {
    await adminApi.createKnowledgeBase(values.name)
    message.success('知识库创建成功')
    setCreateKBOpen(false)
    createKBForm.resetFields()
    loadData()
  }

  const handleDeleteKB = (kbId: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '删除知识库将同时清除其中所有文档，确定继续吗？',
      okButtonProps: { danger: true },
      onOk: async () => {
        await adminApi.deleteKnowledgeBase(kbId)
        message.success('知识库已删除')
        loadData()
      },
    })
  }

  const handleUploadDoc = async () => {
    const values = await uploadForm.validateFields()
    const formData = new FormData()
    formData.append('file', values.file)
    formData.append('knowledge_base_id', values.knowledge_base_id)
    await adminApi.uploadDocument(formData)
    message.success('文档上传成功')
    setUploadDocOpen(false)
    uploadForm.resetFields()
    loadData()
  }

  const handleDeleteDoc = (docId: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个文档吗？',
      okButtonProps: { danger: true },
      onOk: async () => {
        await adminApi.deleteDocument(docId)
        message.success('文档已删除')
        loadData()
      },
    })
  }

  const handleApplyKB = async (kbId: string) => {
    if (applyingKB === kbId) return
    
    setApplyingKB(kbId)
    try {
      if (appliedKB === kbId) {
        await request.delete('/knowledge-bases/apply')
        setAppliedKB(null)
        localStorage.removeItem('appliedKB')
        message.success('已解除知识库应用')
      } else {
        await request.post(`/knowledge-bases/${kbId}/apply`)
        setAppliedKB(kbId)
        localStorage.setItem('appliedKB', JSON.stringify(kbId))
        message.success('知识库应用成功')
      }
    } catch (err: any) {
      message.error(err.message)
    } finally {
      setApplyingKB(null)
      loadData()
    }
  }

  const handleOpenImportModal = (kbId: string) => {
    setSelectedKBForImport(kbId)
    setImportFile(null)
    setImportProgress(0)
    setImportModalOpen(true)
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      const ext = file.name.split('.').pop()?.toLowerCase()
      if (!['txt', 'docx', 'pdf', 'pptx'].includes(ext || '')) {
        message.error('仅支持 .txt、.docx、.pdf、.pptx 格式')
        return
      }
      setImportFile(file)
    }
  }

  const handleImport = async () => {
    if (!importFile || !selectedKBForImport) return
    
    setImportLoading(true)
    setImportProgress(0)
    
    const formData = new FormData()
    formData.append('file', importFile)
    formData.append('knowledge_base_id', selectedKBForImport)
    
    try {
      await adminApi.uploadDocument(formData)
      message.success('文件导入成功')
      setImportModalOpen(false)
      setImportFile(null)
      loadData()
    } catch (err: any) {
      message.error(err.message)
    } finally {
      setImportLoading(false)
    }
  }

  const handleOpenManageModal = async (kbId: string, page: number = 1) => {
    setSelectedKBForManage(kbId)
    setManagePage(page)
    setManageLoading(true)
    if (page === 1) {
      setManageModalOpen(true)
      setSelectedDocIds([])
    }
    
    try {
      const result = await adminApi.getAllDocuments({ page, page_size: 10, knowledge_base: kbId })
      setKbDocuments(result.items)
      setManageTotal(result.total)
    } catch (err: any) {
      message.error(err.message)
      setKbDocuments([])
      setManageTotal(0)
    } finally {
      setManageLoading(false)
    }
  }

  const handleDeleteDocFromKB = async (docId: string) => {
    if (!selectedKBForManage) return
    
    try {
      await adminApi.deleteDocument(docId)
      message.success('文档已删除')
      setKbDocuments(prev => prev.filter(d => d.id !== docId))
      setSelectedDocIds(prev => prev.filter(id => id !== docId))
      setManageTotal(prev => Math.max(0, prev - 1))
    } catch (err: any) {
      message.error(err.message)
    }
  }

  const handleViewDoc = async (docId: string) => {
    try {
      const result = await adminApi.getDocumentContent(docId)
      setViewingDoc({
        id: result.id,
        content: result.content,
        filename: result.filename,
      })
      setViewDocModalOpen(true)
    } catch (err: any) {
      message.error(err.message)
    }
  }

  const handleBatchDelete = () => {
    if (selectedDocIds.length === 0) {
      message.warning('请先选择要删除的文档')
      return
    }
    
    Modal.confirm({
      title: '确认批量删除',
      content: `确定要删除选中的 ${selectedDocIds.length} 个文档吗？此操作不可撤销。`,
      okButtonProps: { danger: true },
      onOk: async () => {
        try {
          const result = await adminApi.batchDeleteDocuments(selectedDocIds)
          message.success(result.message)
          setKbDocuments(prev => prev.filter(d => !selectedDocIds.includes(d.id)))
          setSelectedDocIds([])
          setManageTotal(prev => Math.max(0, prev - selectedDocIds.length))
        } catch (err: any) {
          message.error(err.message)
        }
      },
    })
  }

  const handleReparse = async (docId: string) => {
    await adminApi.reparseDocument(docId)
    message.success('重新解析已触发')
    loadData()
  }

  const handleEditTags = (doc: AdminDocument) => {
    setEditingDoc(doc)
    tagForm.setFieldsValue({ tags: doc.tags.join(', ') })
    setTagModalOpen(true)
  }

  const handleSaveTags = async () => {
    const values = await tagForm.validateFields()
    const tags = values.tags.split(',').map((t: string) => t.trim()).filter(Boolean)
    await adminApi.updateDocumentTags(editingDoc!.id, tags)
    message.success('标签已更新')
    setTagModalOpen(false)
    loadData()
  }

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  const cardStyle = (key: string) => ({
    background: hoveredCard === key ? 'rgba(255,255,255,0.12)' : 'rgba(255,255,255,0.06)',
    border: hoveredCard === key ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(255,255,255,0.1)',
    backdropFilter: 'blur(15px)',
    WebkitBackdropFilter: 'blur(15px)',
    borderRadius: 12,
    transform: hoveredCard === key ? 'translateY(-4px)' : 'translateY(0)',
    boxShadow: hoveredCard === key ? '0 8px 30px rgba(102,126,234,0.25)' : 'none',
    transition: 'all 0.3s ease',
    cursor: 'default',
  })

  const mainCardStyle = {
    background: hoveredMain ? 'rgba(255,255,255,0.1)' : 'rgba(255,255,255,0.06)',
    border: hoveredMain ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(255,255,255,0.1)',
    backdropFilter: 'blur(20px)',
    WebkitBackdropFilter: 'blur(20px)',
    borderRadius: 16,
    transform: hoveredMain ? 'translateY(-3px)' : 'translateY(0)',
    boxShadow: hoveredMain ? '0 6px 25px rgba(102,126,234,0.2)' : 'none',
    transition: 'all 0.3s ease',
  }

  const DashboardPanel = () => (
    <div>
      <Title level={4} style={{ marginBottom: 24, color: '#e0e0e0' }}>系统概览</Title>
      <Row gutter={[16, 16]}>
        {[
          { key: 'users', title: '总用户数', value: stats?.total_users, icon: <UserOutlined /> },
          { key: 'docs', title: '文档总数', value: stats?.total_documents, icon: <FileTextOutlined /> },
          { key: 'questions', title: '总提问数', value: stats?.total_questions, icon: null },
          { key: 'time', title: '平均响应时间', value: stats?.total_questions && stats.total_questions > 0 ? stats?.avg_response_time : '-', suffix: stats?.total_questions && stats.total_questions > 0 ? '秒' : '', precision: stats?.total_questions && stats.total_questions > 0 ? 1 : undefined, icon: null },
        ].map((item) => (
          <Col span={6} key={item.key}>
            <Card style={cardStyle(item.key)}
              onMouseEnter={() => setHoveredCard(item.key)}
              onMouseLeave={() => setHoveredCard(null)}
            >
              <Statistic title={item.title} value={item.value} prefix={item.icon}
                suffix={item.suffix} precision={item.precision}
                style={{ color: '#e0e0e0' }} />
            </Card>
          </Col>
        ))}
      </Row>
      <Title level={5} style={{ marginTop: 32, marginBottom: 16, color: '#ccc' }}>服务器状态</Title>
      <Row gutter={[16, 16]}>
        {[
          { key: 'cpu', title: 'CPU 使用率', value: stats?.cpu_usage },
          { key: 'mem', title: '内存使用率', value: stats?.memory_usage },
          { key: 'disk', title: '磁盘使用率', value: stats?.disk_usage },
        ].map((item) => (
          <Col span={8} key={item.key}>
            <Card style={cardStyle(item.key)}
              onMouseEnter={() => setHoveredCard(item.key)}
              onMouseLeave={() => setHoveredCard(null)}
            >
              <Statistic title={item.title} value={item.value} suffix="%"
                style={{ color: (item.value ?? 0) > 80 ? '#ff4d4f' : '#52c41a' }} />
              <div style={{ marginTop: 8, height: 8, background: 'rgba(255,255,255,0.1)', borderRadius: 4 }}>
                <div style={{ width: `${item.value}%`, height: '100%', background: (item.value ?? 0) > 80 ? '#ff4d4f' : '#667eea', borderRadius: 4, transition: 'width 0.5s' }} />
              </div>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  )

  const UsersPanel = () => (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0, color: '#e0e0e0' }}>用户管理</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setAddUserOpen(true)}>添加用户</Button>
      </div>
      <Table dataSource={users} rowKey="id" loading={loading}
        columns={[
          { title: '用户名', dataIndex: 'username' },
          { title: '角色', dataIndex: 'role', render: (r: string) => <Tag color={r === 'admin' ? 'red' : 'blue'}>{r === 'admin' ? '管理员' : '普通用户'}</Tag> },
          { title: '状态', dataIndex: 'status', render: (s: string) => <Tag color={s === 'active' ? 'green' : 'gray'}>{s === 'active' ? '正常' : '已禁用'}</Tag> },
          { title: '创建时间', dataIndex: 'created_at', render: (t: string) => t?.slice(0, 10) },
          { title: '最后登录', dataIndex: 'last_login', render: (t: string) => t?.slice(0, 10) },
          { title: '操作', render: (_: any, r: AdminUser) => (
              <Space>
                <Button size="small" icon={r.status === 'active' ? <StopOutlined /> : <CheckCircleOutlined />} onClick={() => handleToggleUser(r.id)}>
                  {r.status === 'active' ? '禁用' : '启用'}
                </Button>
                <Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleDeleteUser(r.id)}>删除</Button>
              </Space>
            ),
          },
        ]}
      />
      <Modal title="添加用户" open={addUserOpen} onCancel={() => setAddUserOpen(false)} onOk={() => addUserForm.submit()}>
        <Form form={addUserForm} layout="vertical" onFinish={handleAddUser}>
          <Form.Item name="username" label="用户名" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="password" label="密码" rules={[{ required: true, min: 6 }]}><Input.Password /></Form.Item>
          <Form.Item name="role" label="角色" rules={[{ required: true }]}>
            <Select><Select.Option value="user">普通用户</Select.Option><Select.Option value="admin">管理员</Select.Option></Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )

  const KnowledgePanel = () => (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0, color: '#e0e0e0' }}>知识库管理</Title>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={loadData}>刷新</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateKBOpen(true)}>新建知识库</Button>
        </Space>
      </div>
      <Table dataSource={kbList} rowKey="id" loading={loading}
        columns={[
          { title: '知识库名称', dataIndex: 'name', render: (n: string) => <Space><BookOutlined style={{ color: '#667eea' }} /><span style={{ color: '#e0e0e0' }}>{n}</span></Space> },
          { title: '文档数量', dataIndex: 'doc_count' },
          { title: '创建者', dataIndex: 'owner' },
          { title: '状态', dataIndex: 'status', render: (s: string) => <Tag color={s === 'active' ? 'green' : 'orange'}>{s === 'active' ? '正常' : '空知识库'}</Tag> },
          { title: '创建时间', dataIndex: 'created_at', render: (t: string) => t?.slice(0, 10) },
          { title: '操作', render: (_: any, r: AdminKnowledgeBase) => (
              <Space>
                <Button
                  size="small"
                  type={appliedKB === r.id ? 'primary' : 'default'}
                  icon={applyingKB === r.id ? <LoadingOutlined spin /> : <RocketOutlined />}
                  onClick={() => handleApplyKB(r.id)}
                  loading={applyingKB === r.id}
                >
                  {appliedKB === r.id ? '已应用' : '应用'}
                </Button>
                <Button
                  size="small"
                  icon={<UploadOutlined />}
                  onClick={() => handleOpenImportModal(r.id)}
                >
                  导入
                </Button>
                <Button
                  size="small"
                  icon={<FolderOpenOutlined />}
                  onClick={() => handleOpenManageModal(r.id)}
                >
                  管理
                </Button>
                <Popconfirm title="确定删除此知识库？" onConfirm={() => handleDeleteKB(r.id)} okButtonProps={{ danger: true }}>
                  <Button size="small" danger icon={<DeleteOutlined />}>删除</Button>
                </Popconfirm>
              </Space>
            ),
          },
        ]}
      />
      <Modal title="新建知识库" open={createKBOpen}
        onCancel={() => setCreateKBOpen(false)}
        onOk={() => createKBForm.submit()}
      >
        <Form form={createKBForm} layout="vertical" onFinish={handleCreateKB}>
          <Form.Item name="name" label="知识库名称" rules={[{ required: true, message: '请输入名称' }]}>
            <Input placeholder="请输入知识库名称" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="导入文件"
        open={importModalOpen}
        onCancel={() => { setImportModalOpen(false); setImportFile(null) }}
        onOk={handleImport}
        confirmLoading={importLoading}
      >
        <div style={{ padding: 8 }}>
          <div style={{ marginBottom: 16 }}>
            <p style={{ color: '#ccc', marginBottom: 8 }}>选择要导入的文件（支持 .txt、.docx、.pdf、.pptx 格式）</p>
            <input
              type="file"
              ref={fileInputRef}
              accept=".txt,.docx,.pdf,.pptx"
              onChange={handleFileSelect}
              style={{ color: '#e0e0e0' }}
            />
          </div>
          {importFile && (
            <div style={{ padding: 12, background: 'rgba(255,255,255,0.05)', borderRadius: 8 }}>
              <p style={{ color: '#e0e0e0' }}>已选择文件：{importFile.name}</p>
              <p style={{ color: '#888', fontSize: 12 }}>文件大小：{(importFile.size / 1024).toFixed(2)} KB</p>
            </div>
          )}
          {importLoading && (
            <div style={{ marginTop: 16, textAlign: 'center' }}>
              <Spin tip="正在导入..." />
            </div>
          )}
        </div>
      </Modal>

      <Modal
        title="文档管理"
        open={manageModalOpen}
        onCancel={() => setManageModalOpen(false)}
        footer={null}
        width={700}
      >
        {kbDocuments.length > 0 && (
          <div style={{ marginBottom: 12, display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              danger
              size="small"
              icon={<DeleteOutlined />}
              onClick={handleBatchDelete}
              disabled={selectedDocIds.length === 0}
            >
              批量删除 ({selectedDocIds.length})
            </Button>
          </div>
        )}
        <Spin spinning={manageLoading}>
          {kbDocuments.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 40, color: '#888' }}>
              <FileTextOutlined style={{ fontSize: 48, marginBottom: 12 }} />
              <p>该知识库暂无文档</p>
            </div>
          ) : (
            <Table
              dataSource={kbDocuments}
              rowKey="id"
              rowSelection={{
                selectedRowKeys: selectedDocIds,
                onChange: (keys) => setSelectedDocIds(keys as string[]),
              }}
              pagination={{
                current: managePage,
                total: manageTotal,
                pageSize: 10,
                showSizeChanger: false,
                showTotal: (total) => `共 ${total} 条`,
                onChange: (page) => selectedKBForManage && handleOpenManageModal(selectedKBForManage, page),
              }}
              columns={[
                {
                  title: '文件名',
                  dataIndex: 'filename',
                  render: (n: string) => (
                    <Space>
                      <FileTextOutlined style={{ color: '#667eea' }} />
                      <span style={{ color: '#e0e0e0' }}>{n}</span>
                    </Space>
                  ),
                },
                {
                  title: '大小',
                  dataIndex: 'size',
                },
                {
                  title: '状态',
                  dataIndex: 'status',
                  render: (s: string) => {
                    const map: Record<string, { color: string; text: string }> = {
                      processing: { color: 'processing', text: '解析中' },
                      ready: { color: 'success', text: '就绪' },
                      error: { color: 'error', text: '失败' },
                    }
                    return <Tag color={map[s]?.color}>{map[s]?.text || s}</Tag>
                  },
                },
                {
                  title: '上传时间',
                  dataIndex: 'created_at',
                  render: (t: string) => t?.slice(0, 10),
                },
                {
                  title: '操作',
                  render: (_: any, r: AdminDocument) => (
                    <Space>
                      <Button size="small" icon={<EyeOutlined />} onClick={() => handleViewDoc(r.id)}>查看</Button>
                      <Popconfirm
                        title="确定删除此文档？"
                        onConfirm={() => handleDeleteDocFromKB(r.id)}
                        okButtonProps={{ danger: true }}
                      >
                        <Button size="small" danger icon={<DeleteOutlined />}>删除</Button>
                      </Popconfirm>
                    </Space>
                  ),
                },
              ]}
            />
          )}
        </Spin>
      </Modal>

      <Modal
        title={`查看文档 - ${viewingDoc?.filename || ''}`}
        open={viewDocModalOpen}
        onCancel={() => setViewDocModalOpen(false)}
        footer={null}
        width={700}
      >
        {viewingDoc && (
          <div style={{ maxHeight: 500, overflow: 'auto', padding: 16 }}>
            <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all', color: '#e0e0e0', fontFamily: 'inherit' }}>
              {viewingDoc.content}
            </pre>
          </div>
        )}
      </Modal>
    </div>
  )

  const DocumentsPanel = () => (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0, color: '#e0e0e0' }}>文档管理</Title>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={loadData}>刷新</Button>
          <Button type="primary" icon={<UploadOutlined />} onClick={() => setUploadDocOpen(true)}>上传文档</Button>
        </Space>
      </div>
      <Table dataSource={docList} rowKey="id" loading={loading}
        pagination={{
          current: docPage,
          total: docTotal,
          pageSize: 10,
          showSizeChanger: false,
          showTotal: (total) => `共 ${total} 条`,
          onChange: (page) => { setDocPage(page); loadData() },
        }}
        columns={[
          { title: '文件名', dataIndex: 'filename', render: (n: string) => <Space><FileTextOutlined style={{ color: '#667eea' }} /><span style={{ color: '#e0e0e0' }}>{n}</span></Space> },
          { title: '所属知识库', dataIndex: 'knowledge_base' },
          { title: '大小', dataIndex: 'size' },
          { title: '状态', dataIndex: 'status', render: (s: string) => {
              const map: Record<string, { color: string; text: string }> = {
                processing: { color: 'processing', text: '解析中' },
                ready: { color: 'success', text: '就绪' },
                error: { color: 'error', text: '失败' },
              }
              return <Tag color={map[s]?.color}>{map[s]?.text || s}</Tag>
            },
          },
          { title: '标签', dataIndex: 'tags', render: (tags: string[]) => (
              <Space size={4}>{tags.map(t => <Tag key={t} color="blue">{t}</Tag>)}</Space>
            ),
          },
          { title: '上传时间', dataIndex: 'created_at', render: (t: string) => t?.slice(0, 10) },
          { title: '操作', render: (_: any, r: AdminDocument) => (
              <Space>
                <Button size="small" icon={<EditOutlined />} onClick={() => handleEditTags(r)}>标签</Button>
                <Popconfirm title="确定重新解析此文档？" onConfirm={() => handleReparse(r.id)}>
                  <Button size="small" icon={<ToolOutlined />}>重解析</Button>
                </Popconfirm>
                <Popconfirm title="确定删除此文档？" onConfirm={() => handleDeleteDoc(r.id)} okButtonProps={{ danger: true }}>
                  <Button size="small" danger icon={<DeleteOutlined />}>删除</Button>
                </Popconfirm>
              </Space>
            ),
          },
        ]}
      />
      <Modal title={`编辑标签 - ${editingDoc?.filename}`} open={tagModalOpen}
        onCancel={() => setTagModalOpen(false)} onOk={handleSaveTags}
      >
        <Paragraph type="secondary" style={{ marginBottom: 12 }}>多个标签用逗号分隔</Paragraph>
        <Form form={tagForm}>
          <Form.Item name="tags" rules={[{ required: true, message: '请输入标签' }]}>
            <Input placeholder="例如：技术, RAG, 架构" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal title="上传文档" open={uploadDocOpen}
        onCancel={() => { setUploadDocOpen(false); uploadForm.resetFields() }}
        onOk={handleUploadDoc}
      >
        <Form form={uploadForm} layout="vertical">
          <Form.Item name="knowledge_base_id" label="所属知识库" rules={[{ required: true, message: '请选择知识库' }]}>
            <Select placeholder="选择知识库">
              {kbList.map(kb => (
                <Select.Option key={kb.id} value={kb.id}>{kb.name}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="file" label="选择文件" rules={[{ required: true, message: '请选择文件' }]}>
            <input type="file" accept=".pdf,.docx,.doc,.pptx,.ppt,.txt,.md"
              onChange={(e) => {
                if (e.target.files?.[0]) {
                  uploadForm.setFieldsValue({ file: e.target.files[0] })
                }
              }}
              style={{ color: '#e0e0e0' }}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )

  const LogsPanel = () => (
    <div>
      <Title level={4} style={{ marginBottom: 24, color: '#e0e0e0' }}>操作日志</Title>
      <Table dataSource={logs} rowKey="id" loading={loading}
        columns={[
          { title: '时间', dataIndex: 'created_at', render: (t: string) => t?.slice(0, 10) },
          { title: '用户', dataIndex: 'user' },
          { title: '操作', dataIndex: 'action', render: (a: string) => <Tag>{a}</Tag> },
          { title: '详情', dataIndex: 'detail' },
        ]}
      />
    </div>
  )

  const contentMap: Record<MenuKey, React.ReactNode> = {
    dashboard: <DashboardPanel />,
    users: <UsersPanel />,
    knowledge: <KnowledgePanel />,
    documents: <DocumentsPanel />,
    logs: <LogsPanel />,
  }

  return (
    <div style={{ position: 'relative', minHeight: '100vh' }}>
      <ParticleBackground />
      <Layout style={{ minHeight: '100vh', position: 'relative', zIndex: 1, background: 'transparent' }}>
        <Sider width={220} style={{ background: 'rgba(10,10,26,0.92)', backdropFilter: 'blur(20px)', borderRight: '1px solid rgba(255,255,255,0.06)' }}>
          <div style={{
            color: '#fff', fontSize: 16, fontWeight: 'bold',
            padding: '20px 24px', borderBottom: '1px solid rgba(255,255,255,0.08)',
            display: 'flex', alignItems: 'center', gap: 10,
          }}>
            <div style={{
              width: 32, height: 32, borderRadius: 8,
              background: 'linear-gradient(135deg, #667eea, #764ba2)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 16,
            }}>⚙</div>
            管理后台
          </div>
          <Menu theme="dark" mode="inline" selectedKeys={[activeMenu]}
            onClick={({ key }) => setActiveMenu(key as MenuKey)}
            style={{ background: 'transparent' }}
            items={[
              { key: 'dashboard', icon: <DashboardOutlined />, label: '系统监控' },
              { key: 'users', icon: <UserOutlined />, label: '用户管理' },
              { key: 'knowledge', icon: <BookOutlined />, label: '知识库管理' },
              { key: 'documents', icon: <FileTextOutlined />, label: '文档管理' },
              { key: 'logs', icon: <FileTextOutlined />, label: '操作日志' },
            ]}
          />
        </Sider>
        <Layout style={{ background: 'transparent' }}>
          <div style={{
            background: 'rgba(255,255,255,0.04)',
            backdropFilter: 'blur(20px)',
            WebkitBackdropFilter: 'blur(20px)',
            padding: '12px 24px', display: 'flex', justifyContent: 'space-between',
            alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.06)',
          }}>
            <span style={{ color: '#ccc' }}>当前用户：<Tag color="red">{user?.username}（管理员）</Tag></span>
            <Space>
              <Button onClick={() => navigate('/chat')}>前往问答</Button>
              <Button icon={<LogoutOutlined />} onClick={handleLogout}>退出登录</Button>
            </Space>
          </div>
          <Content style={{ padding: 24, overflowY: 'auto' }}>
            <Card style={mainCardStyle}
              onMouseEnter={() => setHoveredMain(true)}
              onMouseLeave={() => setHoveredMain(false)}
            >
              {contentMap[activeMenu]}
            </Card>
          </Content>
        </Layout>
      </Layout>
    </div>
  )
}