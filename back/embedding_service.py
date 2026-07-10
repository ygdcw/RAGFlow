from langchain_openai import OpenAIEmbeddings
from config import config


class EmbeddingService:
    """
    嵌入模型服务类
    负责管理deepseek-embed嵌入模型的初始化和调用
    
    【人A负责】：嵌入模型集成与服务封装
    【协作需求】：
    - 【人C】向量数据库模块需要调用此类获取嵌入向量
    - 【人B】文档处理模块处理完文档后需传入此类进行向量化
    """

    def __init__(self):
        """
        初始化嵌入模型服务
        使用配置文件中的deepseek-embed模型参数
        """
        config.validate_config()
        
        self.embeddings = OpenAIEmbeddings(
            api_key=config.EMBEDDING_API_KEY,
            base_url=config.EMBEDDING_API_BASE,
            model=config.EMBEDDING_MODEL_NAME,
        )

    def embed_documents(self, texts):
        """
        对文档列表进行向量化
        
        参数：
            texts (list[str]): 文本列表，每个元素为一段文本
        
        返回：
            list[list[float]]: 嵌入向量列表，每个向量为浮点数数组
        
        【人C协作接口】：向量数据库模块调用此方法获取文档嵌入
        数据格式：输入为字符串列表，输出为二维浮点数数组
        """
        if not texts:
            return []
        
        try:
            return self.embeddings.embed_documents(texts)
        except Exception as e:
            raise RuntimeError(f"嵌入模型调用失败: {str(e)}") from e

    def embed_query(self, query):
        """
        对查询文本进行向量化
        
        参数：
            query (str): 查询文本
        
        返回：
            list[float]: 查询向量，为浮点数数组
        
        【人D协作接口】：检索模块调用此方法获取查询嵌入
        数据格式：输入为字符串，输出为浮点数数组
        """
        if not query:
            return []
        
        try:
            return self.embeddings.embed_query(query)
        except Exception as e:
            raise RuntimeError(f"查询向量化失败: {str(e)}") from e

    def get_embedding_dimension(self):
        """
        获取嵌入向量的维度
        
        返回：
            int: 嵌入向量维度
        
        注意：deepseek-embed模型的嵌入维度为1024   
        """
        sample_text = "test"
        embedding = self.embed_query(sample_text)
        return len(embedding)


embedding_service = EmbeddingService()
