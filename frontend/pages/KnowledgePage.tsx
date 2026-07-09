import { useEffect, useState } from 'react'
import {
  Card, Table, Button, Modal, Input, Upload, Progress,
  Tag, Space, message, Typography, Breadcrumb
} from 'antd'
import {
  PlusOutlined, DeleteOutlined,
  FileTextOutlined, ArrowLeftOutlined,
  InboxOutlined, ReloadOutlined
} from '@ant-design/icons'
import type { UploadProps } from 'antd'
import { useKnowledgeStore } from '../stores/useKnowledgeStore'
import { knowledgeApi } from '../api/knowledge'
import { useAuthStore } from '../stores/useAuthStore'
import ParticleBackground from '../components/common/ParticleBackground'

const { Title } = Typography
const { Dragger } = Upload

export default function KnowledgePage() {
  const {
    knowledgeBases, currentKnowledgeBase, documents,
    loading, uploadProgress, isUploading,
    loadKnowledgeBases, setCurrentKnowledgeBase,
    uploadDocument, deleteDocument,
  } = useKnowledgeStore()

  const { isAdmin } = useAuthStore()

  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [newKBName, setNewKBName] = useState('')
  const [creating, setCreating] = useState(false)
  const [hoveredKB, setHoveredKB] = useState<string | null>(null)

  useEffect(() => {
    loadKnowledgeBases()
  }, [])

  const handleCreate = async () => {
    if (!newKBName.trim()) return
    setCreating(true)
    try {
      await knowledgeApi.create(newKBName)
      message.success('知识库创建成功')
      setCreateModalOpen(false)
      setNewKBName('')
      loadKnowledgeBases()
    } catch (err: any) {
      message.error(err.message)
    } finally {
      setCreating(false)
    }
  }

  const handleDeleteKB = (kbId: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '删除知识库会同时删除其中的所有文档，确定继续吗？',
      okButtonProps: { danger: true },
      onOk: async () => {
        await knowledgeApi.delete(kbId)
        message.success('知识库已删除')
        if (currentKnowledgeBase?.id === kbId) {
          setCurrentKnowledgeBase(null)
        }
        loadKnowledgeBases()
      },
    })
  }

  const handleDeleteDoc = (docId: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个文档吗？',
      onOk: async () => {
        await deleteDocument(docId)
        message.success('文档已删除')
      },
    })
  }

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: false,
    showUploadList: false,
    beforeUpload: (file) => {
      if (currentKnowledgeBase) {
        uploadDocument(currentKnowledgeBase.id, file)
      }
      return false
    },
    accept: '.pdf,.docx,.doc,.pptx,.ppt,.txt,.md',
  }

  const KBListView = () => (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <Title level={4} style={{ margin: 0, color: '#e0e0e0' }}>知识库管理</Title>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={loadKnowledgeBases}>刷新</Button>
          {isAdmin && (
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalOpen(true)}>
              新建知识库
            </Button>
          )}
        </Space>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
        {knowledgeBases.map(kb => (
          <Card
            key={kb.id}
            hoverable={false}
            onClick={() => setCurrentKnowledgeBase(kb)}
            onMouseEnter={() => setHoveredKB(kb.id)}
            onMouseLeave={() => setHoveredKB(null)}
            style={{
              background: hoveredKB === kb.id ? 'rgba(255,255,255,0.1)' : 'rgba(255,255,255,0.05)',
              border: hoveredKB === kb.id ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(255,255,255,0.08)',
              borderRadius: 14,
              transform: hoveredKB === kb.id ? 'translateY(-4px)' : 'translateY(0)',
              boxShadow: hoveredKB === kb.id ? '0 8px 30px rgba(102,126,234,0.2)' : 'none',
              transition: 'all 0.3s ease',
              cursor: 'pointer',
            }}
            actions={isAdmin ? [
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
                onClick={(e) => { e.stopPropagation(); handleDeleteKB(kb.id) }}
                style={{ color: '#ff4d4f' }}
              >
                删除
              </Button>
            ] : []}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <FileTextOutlined style={{ fontSize: 36, color: '#667eea' }} />
              <div>
                <div style={{ fontSize: 16, fontWeight: 'bold', marginBottom: 4, color: '#e0e0e0' }}>{kb.name}</div>
                <div style={{ fontSize: 13, color: '#888' }}>
                  {kb.doc_count} 个文档 · 创建于 {kb.created_at.slice(0, 10)}
                </div>
              </div>
            </div>
          </Card>
        ))}

        {knowledgeBases.length === 0 && !loading && (
          <Card style={{
            gridColumn: '1 / -1', textAlign: 'center', padding: 60,
            background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 14,
          }}>
            <InboxOutlined style={{ fontSize: 48, color: '#555', marginBottom: 16 }} />
            <div style={{ fontSize: 16, color: '#777' }}>暂无知识库，点击上方按钮创建</div>
          </Card>
        )}
      </div>
    </div>
  )

  const DocumentListView = () => (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Breadcrumb
          items={[
            {
              title: (
                <a onClick={() => setCurrentKnowledgeBase(null)} style={{ color: '#aac8ff' }}>
                  <ArrowLeftOutlined style={{ marginRight: 4 }} />
                  知识库列表
                </a>
              ),
            },
            { title: <span style={{ color: '#ccc' }}>{currentKnowledgeBase?.name}</span> },
          ]}
        />
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0, color: '#e0e0e0' }}>{currentKnowledgeBase?.name}</Title>
        <Button icon={<ReloadOutlined />} onClick={() => {
          if (currentKnowledgeBase) {
            useKnowledgeStore.getState().loadDocuments(currentKnowledgeBase.id)
          }
        }}>
          刷新
        </Button>
      </div>

      <Card style={{
        marginBottom: 24,
        background: 'rgba(255,255,255,0.05)',
        border: '1px solid rgba(255,255,255,0.08)',
        borderRadius: 14,
      }}>
        <Dragger {...uploadProps} disabled={isUploading}
          style={{ background: 'transparent' }}
        >
          <p className="ant-upload-drag-icon">
            <InboxOutlined style={{ color: '#667eea' }} />
          </p>
          <p className="ant-upload-text" style={{ color: '#ccc' }}>点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint" style={{ color: '#777' }}>
            支持 PDF、DOCX、PPTX、TXT、MD 格式，单个文件不超过 50MB
          </p>
        </Dragger>
        {isUploading && (
          <div style={{ marginTop: 16 }}>
            <Progress percent={uploadProgress} status={uploadProgress === 100 ? 'success' : 'active'} />
            <span style={{ fontSize: 13, color: '#888' }}>正在上传并解析文档...</span>
          </div>
        )}
      </Card>

      <Table
        dataSource={documents}
        rowKey="id"
        loading={loading}
        columns={[
          {
            title: '文件名', dataIndex: 'filename', key: 'filename',
            render: (name: string) => (
              <Space><FileTextOutlined style={{ color: '#667eea' }} /><span style={{ color: '#e0e0e0' }}>{name}</span></Space>
            ),
          },
          {
            title: '状态', dataIndex: 'status', key: 'status',
            render: (status: string) => {
              const map: Record<string, { color: string; text: string }> = {
                processing: { color: 'processing', text: '解析中' },
                ready: { color: 'success', text: '就绪' },
                error: { color: 'error', text: '失败' },
              }
              return <Tag color={map[status]?.color}>{map[status]?.text || status}</Tag>
            },
          },
          { title: '上传时间', dataIndex: 'created_at', key: 'created_at', render: (t: string) => t?.slice(0, 10) },
          {
            title: '操作', key: 'action',
            render: (_: any, record: Document) => isAdmin && (
              <Button
                size="small"
                danger
                icon={<DeleteOutlined />}
                onClick={() => handleDeleteDoc(record.id)}
              >
                删除
              </Button>
            ),
          },
        ]}
      />
    </div>
  )

  return (
    <div style={{ position: 'relative', minHeight: '100vh', background: 'transparent' }}>
      <ParticleBackground />
      <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto', position: 'relative', zIndex: 1 }}>
        {currentKnowledgeBase ? <DocumentListView /> : <KBListView />}

        <Modal
          title="新建知识库"
          open={createModalOpen}
          onCancel={() => setCreateModalOpen(false)}
          onOk={handleCreate}
          confirmLoading={creating}
        >
          <Input
            placeholder="请输入知识库名称"
            value={newKBName}
            onChange={e => setNewKBName(e.target.value)}
            onPressEnter={handleCreate}
          />
        </Modal>
      </div>
    </div>
  )
}