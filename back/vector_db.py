import os
from langchain_chroma import Chroma
from langchain_core.documents import Document
from config import config
from embedding_service import embedding_service
from vector_db_extension import vector_db_extension


class VectorDBService:
    """
    向量数据库服务类
    负责管理Chroma向量数据库的初始化、文档存储和检索
    
    【人A负责】：向量数据库集成与管理
    【人C扩展】：通过vector_db_extension提供多集合管理和远程数据库支持
    【协作需求】：
    - 【人B】文档处理模块处理完文档后传入此类存储
    - 【人D】检索模块调用此类进行文档检索
    - 【人A】嵌入服务模块提供向量化能力
    - 【人C】扩展模块提供高级功能（多集合、远程数据库）
    """

    def __init__(self):
        """
        初始化向量数据库服务
        如果持久化目录存在则加载现有数据库，否则创建新数据库
        """
        self.persist_directory = config.VECTOR_DB_PERSIST_DIR
        self.collection_name = config.VECTOR_DB_COLLECTION_NAME
        
        if os.path.exists(self.persist_directory):
            self._load_existing_db()
        else:
            self._create_new_db()

    def _create_new_db(self):
        """创建新的向量数据库"""
        self.db = Chroma(
            collection_name=self.collection_name,
            embedding_function=embedding_service.embeddings,
            persist_directory=self.persist_directory,
        )

    def _load_existing_db(self):
        """加载已存在的向量数据库"""
        self.db = Chroma(
            collection_name=self.collection_name,
            embedding_function=embedding_service.embeddings,
            persist_directory=self.persist_directory,
        )

    def add_documents(self, documents):
        """
        添加文档到向量数据库
        
        参数：
            documents (list[Document]): Document对象列表
        
        返回：
            list[str]: 添加的文档ID列表
        
        【人B协作接口】：文档处理模块调用此方法存储文档
        数据格式：Document对象列表，每个对象包含page_content和metadata
        """
        if not documents:
            return []
        
        try:
            doc_ids = self.db.add_documents(documents)
            return doc_ids
        except Exception as e:
            raise RuntimeError(f"添加文档到向量数据库失败: {str(e)}") from e

    def add_texts(self, texts, metadatas=None):
        """
        添加文本到向量数据库
        
        参数：
            texts (list[str]): 文本列表
            metadatas (list[dict], optional): 元数据列表
        
        返回：
            list[str]: 添加的文档ID列表
        
        【人B协作接口】：文档处理模块调用此方法存储文本
        数据格式：texts为字符串列表，metadatas为字典列表
        """
        if not texts:
            return []
        
        try:
            doc_ids = self.db.add_texts(texts, metadatas=metadatas)
            return doc_ids
        except Exception as e:
            raise RuntimeError(f"添加文本到向量数据库失败: {str(e)}") from e

    def similarity_search(self, query, k=3):
        """
        基于相似度检索相关文档
        
        参数：
            query (str): 查询文本
            k (int): 返回文档数量，默认为3
        
        返回：
            list[Document]: 检索到的文档列表
        
        【人D协作接口】：检索模块调用此方法进行文档检索
        数据格式：输入为查询字符串，输出为Document对象列表
        """
        if not query:
            return []
        
        try:
            results = self.db.similarity_search(query, k=k)
            return results
        except Exception as e:
            raise RuntimeError(f"相似度检索失败: {str(e)}") from e

    def similarity_search_with_score(self, query, k=3):
        """
        基于相似度检索相关文档，并返回匹配分数
        
        参数：
            query (str): 查询文本
            k (int): 返回文档数量，默认为3
        
        返回：
            list[tuple[Document, float]]: 检索到的文档及其分数列表
        
        【人D协作接口】：检索模块调用此方法进行带分数的文档检索
        数据格式：输入为查询字符串，输出为(Document, score)元组列表
        """
        if not query:
            return []
        
        try:
            results = self.db.similarity_search_with_score(query, k=k)
            return results
        except Exception as e:
            raise RuntimeError(f"带分数的相似度检索失败: {str(e)}") from e

    def get_retriever(self, search_kwargs=None):
        """
        获取检索器对象
        
        参数：
            search_kwargs (dict, optional): 检索参数，如{"k": 3}
        
        返回：
            Retriever: 检索器对象
        
        【人D协作接口】：检索模块调用此方法获取检索器
        数据格式：返回LangChain标准Retriever对象
        """
        if search_kwargs is None:
            search_kwargs = {"k": config.RETRIEVAL_TOP_K}
        
        return self.db.as_retriever(search_kwargs=search_kwargs)

    def delete_documents(self, doc_ids):
        """
        删除指定ID的文档
        
        参数：
            doc_ids (list[str]): 要删除的文档ID列表
        
        【人B协作接口】：文档管理模块调用此方法删除文档
        数据格式：字符串ID列表
        """
        if not doc_ids:
            return
        
        try:
            self.db.delete(doc_ids)
        except Exception as e:
            raise RuntimeError(f"删除文档失败: {str(e)}") from e

    def get_document_count(self):
        """
        获取数据库中文档总数
        
        返回：
            int: 文档数量
        """
        return len(self.db.get()["ids"])

    def clear_all_documents(self):
        """
        清空向量数据库中的所有文档
        
        警告：此操作不可逆，请谨慎使用
        """
        all_ids = self.db.get()["ids"]
        if all_ids:
            self.delete_documents(all_ids)

    def add_documents_to_collection(self, documents, collection_name="default"):
        """
        【人C扩展方法】向指定集合添加文档
        
        参数：
            documents (list[Document]): Document对象列表
            collection_name (str): 集合名称或类别名称，默认为"default"
        
        返回：
            list[str]: 添加的文档ID列表
        
        委托给vector_db_extension处理多集合管理
        """
        return vector_db_extension.add_documents_to_collection(documents, collection_name)

    def search_in_collection(self, query, collection_name="default", k=3):
        """
        【人C扩展方法】在指定集合中检索相关文档
        
        参数：
            query (str): 查询文本
            collection_name (str): 集合名称或类别名称，默认为"default"
            k (int): 返回文档数量，默认为3
        
        返回：
            list[Document]: 检索到的文档列表
        
        委托给vector_db_extension处理多集合检索
        """
        return vector_db_extension.search_in_collection(query, collection_name, k)

    def search_cross_collections(self, query, collections=None, k=3):
        """
        【人C扩展方法】跨多个集合检索相关文档
        
        参数：
            query (str): 查询文本
            collections (list): 要检索的集合名称列表，默认为所有集合
            k (int): 每个集合返回的文档数量，默认为3
        
        返回：
            list[dict]: 检索到的文档列表，包含来源集合信息
        
        委托给vector_db_extension处理跨集合检索
        """
        return vector_db_extension.search_cross_collections(query, collections, k)

    def get_collection_info(self, collection_name=None):
        """
        【人C扩展方法】获取集合信息
        
        参数：
            collection_name (str, optional): 集合名称或类别名称，默认为获取所有集合信息
        
        返回：
            dict: 集合信息字典
        
        委托给vector_db_extension获取集合元数据
        """
        return vector_db_extension.get_collection_info(collection_name)

    def create_new_collection(self, collection_name, category=None, description=""):
        """
        【人C扩展方法】创建新集合
        
        参数：
            collection_name (str): 新集合名称
            category (str, optional): 集合类别
            description (str, optional): 集合描述
        
        委托给vector_db_extension创建新集合
        """
        return vector_db_extension.create_new_collection(collection_name, category, description)

    def get_retriever_for_collection(self, collection_name="default", search_kwargs=None):
        """
        【人C扩展方法】获取指定集合的检索器
        
        参数：
            collection_name (str): 集合名称或类别名称，默认为"default"
            search_kwargs (dict, optional): 检索参数，如{"k": 3}
        
        返回：
            Retriever: 检索器对象
        
        委托给vector_db_extension获取指定集合的检索器
        """
        return vector_db_extension.get_retriever_for_collection(collection_name, search_kwargs)

    def delete_collection(self, collection_name):
        """
        【人C扩展方法】删除指定集合
        
        参数：
            collection_name (str): 集合名称或类别名称
        
        委托给vector_db_extension删除集合
        """
        return vector_db_extension.delete_collection(collection_name)


vector_db_service = VectorDBService()
