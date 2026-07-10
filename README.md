# RAGFlow - 智能医疗问答系统

基于 RAG（Retrieval-Augmented Generation）技术的智能医疗问答系统，支持多知识库管理、文档导入、对话历史持久化和用户权限控制。

## 📋 目录

- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [安装步骤](#安装步骤)
- [使用方法](#使用方法)
- [项目结构](#项目结构)
- [API 接口](#api-接口)
- [开发指南](#开发指南)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

## ✨ 功能特性

### 🔍 核心功能
- **智能问答**：基于大语言模型的问答能力，结合知识库上下文
- **多知识库管理**：支持创建、删除、应用多个独立知识库
- **文档导入**：支持 `.txt`、`.docx`、`.pdf`、`.pptx` 格式文件导入
- **文档管理**：支持文档查看、分页浏览、批量删除
- **对话历史**：自动保存对话记录，支持会话切换和历史回顾
- **用户隔离**：不同用户账号的对话历史完全独立隔离

### 🎯 用户权限
- **管理员**：可创建/删除知识库、导入文档、管理用户、系统监控
- **普通用户**：可浏览知识库、进行问答、管理个人对话

### 📁 数据持久化
- 向量数据库持久化存储（Chroma）
- 对话历史文件系统存储
- 知识库数据独立隔离
- 删除的知识库不会在重启后自动重建

## 🛠️ 技术栈

### 后端
| 组件 | 技术 | 版本要求 |
|------|------|----------|
| 框架 | FastAPI | Python 3.10+ |
| 向量数据库 | Chroma | LangChain-Chroma |
| 嵌入模型 | Qwen/Qwen3-Embedding-8B | - |
| LLM | DeepSeek Chat | - |

### 前端
| 组件 | 技术 | 版本要求 |
|------|------|----------|
| 框架 | React 18 + TypeScript | - |
| UI | Ant Design | - |
| 状态管理 | Zustand | - |
| 构建工具 | Vite | - |
| 路由 | React Router DOM | - |

## 📦 安装步骤

### 1. 克隆项目

```bash
git clone https://github.com/ygdcw/RAGFlow.git
cd RAGFlow
git checkout RAG_MedicalTool-v2.0
```

### 2. 后端环境配置

```bash
cd back
pip install -r requirements.txt
```

#### 配置 API 密钥

创建 `AI_KEY.env` 文件：

```env
# 嵌入模型配置
OPENAI_API_KEY=your-embedding-api-key
OPENAI_API_BASE=https://api.siliconflow.cn/v1

# LLM 对话模型配置
OPENAI_API_KEY1=your-llm-api-key
OPENAI_API_BASE1=https://api.deepseek.com/v1
```

### 3. 前端环境配置

```bash
cd ../frontend
npm install
```

## 🚀 使用方法

### 启动服务

#### 后端服务

```bash
cd back
python main.py api
```

后端服务将在 `http://localhost:8000` 运行。

#### 前端服务

```bash
cd frontend
npm run dev
```

前端页面将在 `http://localhost:3000` 运行。

### 登录系统

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |
| 普通用户 | user | user123 |

### 基本操作

1. **创建知识库**：管理员登录后，在管理后台创建知识库
2. **导入文档**：选择知识库，点击导入按钮上传文档
3. **应用知识库**：点击"应用"按钮，AI将使用该知识库内容进行问答
4. **问答交互**：在聊天页面输入问题，AI将基于知识库内容回答

## 📁 项目结构

```
RAGFlow/
├── back/                    # 后端代码
│   ├── chroma_db/           # 向量数据库持久化目录（自动生成）
│   ├── chat_history/        # 对话历史存储目录（自动生成）
│   ├── uploads/             # 文件上传临时目录（自动生成）
│   ├── retrieval_engine/    # 检索引擎模块
│   │   ├── __init__.py
│   │   ├── parser.py        # 文档解析器
│   │   └── text_splitter.py # 文本分割器
│   ├── config.py            # 配置管理
│   ├── main.py              # FastAPI 主入口
│   ├── vector_db.py         # 向量数据库服务
│   ├── vector_db_extension.py # 多集合扩展
│   ├── rag_chain.py         # RAG 链式处理
│   ├── chat_history_manager.py # 对话历史管理
│   ├── document_processor.py   # 文档处理
│   ├── embedding_service.py    # 嵌入服务
│   └── llm_service.py      # LLM 服务
├── frontend/               # 前端代码
│   ├── api/                # API 调用
│   ├── assets/             # 静态资源
│   ├── components/         # 组件
│   ├── mocks/              # 模拟数据
│   ├── pages/              # 页面
│   ├── stores/             # 状态管理
│   ├── types/              # 类型定义
│   ├── App.tsx             # 应用入口
│   ├── main.tsx            # React 入口
│   └── vite.config.ts      # Vite 配置
├── tests/                  # 测试文件
├── .gitignore             # Git 忽略配置
└── README.md              # 项目说明
```

## 🔌 API 接口

### 认证接口
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/auth/login` | 用户登录 |
| GET | `/api/v1/auth/me` | 获取当前用户信息 |

### 知识库接口
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/knowledge-bases` | 获取知识库列表 |
| POST | `/api/v1/knowledge-bases` | 创建知识库（管理员） |
| DELETE | `/api/v1/knowledge-bases/{kb_id}` | 删除知识库（管理员） |
| POST | `/api/v1/knowledge-bases/{kb_id}/apply` | 应用知识库（管理员） |

### 文档接口
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/documents/upload` | 上传文档 |
| GET | `/api/v1/documents` | 获取文档列表 |
| DELETE | `/api/v1/admin/documents/{doc_id}` | 删除文档（管理员） |

### 对话接口
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/conversations` | 获取对话列表 |
| POST | `/api/v1/conversations` | 创建新对话 |
| DELETE | `/api/v1/conversations/{id}` | 删除对话 |
| GET | `/api/v1/conversations/{id}/messages` | 获取对话消息 |

### 问答接口
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/chat/session` | 带会话的问答 |
| POST | `/api/v1/chat/send` | SSE 流式问答 |

## 📖 开发指南

### 后端开发

```bash
cd back
# 运行开发服务器
python main.py api

# 运行测试
python -m pytest tests/
```

### 前端开发

```bash
cd frontend
# 运行开发服务器
npm run dev

# 构建生产版本
npm run build

# 代码检查
npm run lint
```

### 配置说明

#### 文档处理配置

在 `back/config.py` 中可以配置以下参数：

```python
DOCUMENT_CHUNK_SIZE = 500      # 每个文本块的最大字符数
DOCUMENT_CHUNK_OVERLAP = 80    # 相邻文本块之间的重叠字符数
```

#### 检索配置

```python
RETRIEVAL_TOP_K = 3            # 检索返回的文档数量
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/your-feature`)
3. 提交更改 (`git commit -m 'Add your feature'`)
4. 推送到分支 (`git push origin feature/your-feature`)
5. 创建 Pull Request

## 📜 许可证

MIT License

## 📞 联系方式

如有问题或建议，请提交 Issue 或联系项目维护者。