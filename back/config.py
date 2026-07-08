import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "AI_KEY.env"))


class Config:
    """
    配置管理类
    负责加载和管理所有API密钥、模型配置和系统参数
    
    【人A负责】：配置加载与管理
    【协作需求】：无
    """

    # === 嵌入模型配置（Qwen/Qwen3-Embedding-8B）===
    # 使用siliconflow平台的Qwen3-Embedding-8B模型
    EMBEDDING_API_KEY = os.getenv("OPENAI_API_KEY")
    EMBEDDING_API_BASE = os.getenv("OPENAI_API_BASE")
    EMBEDDING_MODEL_NAME = "Qwen/Qwen3-Embedding-8B"

    # === LLM对话模型配置（deepseek-chat）===
    # 使用DeepSeek平台的deepseek-chat模型
    LLM_API_KEY = os.getenv("OPENAI_API_KEY1")
    LLM_API_BASE = os.getenv("OPENAI_API_BASE1")
    LLM_MODEL_NAME = "deepseek-chat"
    LLM_TEMPERATURE = 0.1

    # === 向量数据库配置 ===
    # 【人C负责】：向量数据库扩展，支持多集合管理和远程数据库
    # 接口规范：需提供与Chroma兼容的向量存储接口
    # 数据格式：Document对象列表，包含page_content和metadata字段
    VECTOR_DB_PERSIST_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")
    VECTOR_DB_COLLECTION_NAME = "knowledge_base"
    
    # 远程数据库配置（【人C负责】后续扩展）
    # 启用远程数据库时，设置VECTOR_DB_USE_REMOTE=True
    # 接口规范：需提供Chroma远程客户端连接参数
    VECTOR_DB_USE_REMOTE = False
    VECTOR_DB_REMOTE_HOST = "localhost"
    VECTOR_DB_REMOTE_PORT = 8000
    
    # 多集合配置（【人C负责】）
    # 支持按类别创建不同的文档集合
    # 数据格式：{"category_name": "collection_name"}
    VECTOR_DB_COLLECTIONS = {
        "default": "knowledge_base",
        "technical": "technical_docs",
        "product": "product_docs",
        "faq": "faq_docs",
    }

    # === 对话历史配置 ===
    # 【人C负责】：对话历史持久化和管理
    # 接口规范：需提供对话存储和检索接口
    # 数据格式：{"session_id": str, "messages": list, "created_at": datetime}
    CHAT_HISTORY_PERSIST_DIR = os.path.join(os.path.dirname(__file__), "chat_history")
    CHAT_HISTORY_MAX_MESSAGES = 100
    CHAT_HISTORY_MAX_SESSIONS = 1000

    # === 文档处理配置 ===
    # 【人B负责】：文档加载器扩展（支持pdf、docx、pptx等）和段落分割功能
    # 接口规范：需实现load_documents(file_paths)方法，返回Document对象列表
    # 数据格式：{"file_path": str, "content": str, "metadata": dict}
    
    # 段落分割参数（【人B负责】）
    # chunk_size: 每个文本块的最大字符数
    # chunk_overlap: 相邻文本块之间的重叠字符数
    # 分隔符优先级：["\n\n", "\n", "。", ".", "！", "？", " ", ""]
    DOCUMENT_CHUNK_SIZE = 500
    DOCUMENT_CHUNK_OVERLAP = 80
    DOCUMENT_SEPARATORS = ["\n\n", "\n", "。", ".", "！", "？", " ", ""]
    
    # OCR配置（【人B负责】PDF扫描件识别）
    # TESSERACT_CMD: Tesseract OCR引擎路径（Windows用户需要配置）
    # OCR_ENABLED: 是否启用OCR功能
    # OCR_MIN_TEXT_LENGTH: 触发OCR的最小文本长度阈值
    OCR_ENABLED = True
    TESSERACT_CMD = os.getenv("TESSERACT_CMD", r'C:\Program Files\Tesseract-OCR\tesseract.exe')
    OCR_MIN_TEXT_LENGTH = 100

    # === 检索配置 ===
    # 【人D负责】：检索策略优化
    # 接口规范：需实现retrieve(query, top_k)方法，返回相关文档列表
    # 数据格式：[{"content": str, "score": float, "metadata": dict}]
    RETRIEVAL_TOP_K = 3

    # === 系统配置 ===
    APP_NAME = "RAGFlow"
    APP_VERSION = "1.0.0"

    @classmethod
    def validate_config(cls):
        """
        验证配置完整性
        检查必要的API密钥和URL是否已配置
        """
        required_configs = [
            ("EMBEDDING_API_KEY", cls.EMBEDDING_API_KEY),
            ("EMBEDDING_API_BASE", cls.EMBEDDING_API_BASE),
            ("LLM_API_KEY", cls.LLM_API_KEY),
            ("LLM_API_BASE", cls.LLM_API_BASE),
        ]

        missing_configs = [key for key, value in required_configs if not value]
        if missing_configs:
            raise ValueError(
                f"缺少必要配置项: {', '.join(missing_configs)}\n"
                f"请检查AI_KEY.env文件是否正确配置"
            )


config = Config()
