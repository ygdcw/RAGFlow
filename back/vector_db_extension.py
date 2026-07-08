import os
import json
from typing import Dict, Optional
from langchain_chroma import Chroma
from langchain_core.documents import Document
from config import config
from embedding_service import embedding_service


class VectorDBExtension:
    """
    向量数据库扩展类
    【人C负责】：提供多集合管理和远程数据库支持
    
    功能特性：
    1. 多集合管理：支持按类别创建和管理不同的文档集合
    2. 远程数据库支持：支持连接远程Chroma服务器
    3. 集合元数据管理：管理集合的描述和配置信息
    4. 跨集合检索：支持在多个集合中同时检索
    
    协作需求：
    - 【人A】嵌入服务模块提供向量化能力
    - 【人B】文档处理模块处理完文档后传入此类存储
    - 【人D】检索模块调用此类进行文档检索
    """

    def __init__(self):
        """
        初始化向量数据库扩展服务
        """
        self.persist_directory = config.VECTOR_DB_PERSIST_DIR
        self.collections: Dict[str, Chroma] = {}
        self.collection_metadata: Dict[str, dict] = {}
        
        # 确保持久化目录存在
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # 加载已配置的集合
        self._load_collections()

    def _load_collections(self):
        """
        加载配置中定义的所有集合
        
        遍历VECTOR_DB_COLLECTIONS配置，创建或加载对应的Chroma集合
        """
        for category, collection_name in config.VECTOR_DB_COLLECTIONS.items():
            try:
                self._get_or_create_collection(collection_name)
                # 设置集合元数据
                self.collection_metadata[collection_name] = {
                    "category": category,
                    "description": f"{category} category documents",
                    "document_count": 0,
                }
            except Exception as e:
                print(f"加载集合 {collection_name} 失败: {str(e)}")

    def _get_or_create_collection(self, collection_name: str) -> Chroma:
        """
        获取或创建指定名称的集合
        
        参数：
            collection_name (str): 集合名称
        
        返回：
            Chroma: Chroma集合对象
        
        设计思路：
            - 如果集合已存在于缓存中，直接返回
            - 如果集合不存在，根据配置决定创建本地或远程集合
            - 远程集合支持通过HTTP连接到Chroma服务器
        """
        if collection_name in self.collections:
            return self.collections[collection_name]
        
        # 根据配置决定创建本地或远程集合
        if config.VECTOR_DB_USE_REMOTE:
            db = self._create_remote_collection(collection_name)
        else:
            db = self._create_local_collection(collection_name)
        
        self.collections[collection_name] = db
        return db

    def _create_local_collection(self, collection_name: str) -> Chroma:
        """
        创建本地Chroma集合
        
        参数：
            collection_name (str): 集合名称
        
        返回：
            Chroma: 本地Chroma集合对象
        
        数据格式：集合数据存储在VECTOR_DB_PERSIST_DIR目录下
        """
        return Chroma(
            collection_name=collection_name,
            embedding_function=embedding_service.embeddings,
            persist_directory=self.persist_directory,
        )

    def _create_remote_collection(self, collection_name: str) -> Chroma:
        """
        创建远程Chroma集合连接
        
        参数：
            collection_name (str): 集合名称
        
        返回：
            Chroma: 远程Chroma集合对象
        
        【人C负责】：后续扩展实现
        接口规范：需提供Chroma远程客户端连接
        数据格式：通过HTTP连接到远程Chroma服务器
        """
        raise NotImplementedError(
            "【人C负责】远程数据库连接尚未实现，请后续添加\n"
            "需要实现：通过chromadb.HttpClient连接到远程服务器\n"
            "配置参数：VECTOR_DB_REMOTE_HOST, VECTOR_DB_REMOTE_PORT"
        )

    def add_documents_to_collection(self, documents: list, collection_name: str = "default") -> list:
        """
        向指定集合添加文档
        
        参数：
            documents (list[Document]): Document对象列表
            collection_name (str): 集合名称或类别名称，默认为"default"
        
        返回：
            list[str]: 添加的文档ID列表
        
        【人B协作接口】：文档处理模块调用此方法存储文档到指定集合
        数据格式：Document对象列表，每个对象包含page_content和metadata
        """
        if not documents:
            return []
        
        # 获取实际的集合名称（支持类别名称映射）
        actual_collection_name = self._resolve_collection_name(collection_name)
        
        try:
            db = self._get_or_create_collection(actual_collection_name)
            doc_ids = db.add_documents(documents)
            
            # 更新集合元数据中的文档计数
            if actual_collection_name in self.collection_metadata:
                self.collection_metadata[actual_collection_name]["document_count"] = len(db.get()["ids"])
            
            return doc_ids
        except Exception as e:
            raise RuntimeError(f"向集合 {actual_collection_name} 添加文档失败: {str(e)}") from e

    def _resolve_collection_name(self, name: str) -> str:
        """
        解析集合名称
        
        参数：
            name (str): 集合名称或类别名称
        
        返回：
            str: 实际的集合名称
        
        设计思路：
            - 如果name在VECTOR_DB_COLLECTIONS的键中，返回对应的集合名称
            - 如果name在VECTOR_DB_COLLECTIONS的值中，直接返回
            - 否则创建新的集合名称
        """
        if name in config.VECTOR_DB_COLLECTIONS:
            return config.VECTOR_DB_COLLECTIONS[name]
        elif name in config.VECTOR_DB_COLLECTIONS.values():
            return name
        else:
            return name

    def search_in_collection(self, query: str, collection_name: str = "default", k: int = 3) -> list:
        """
        在指定集合中检索相关文档
        
        参数：
            query (str): 查询文本
            collection_name (str): 集合名称或类别名称，默认为"default"
            k (int): 返回文档数量，默认为3
        
        返回：
            list[Document]: 检索到的文档列表
        
        【人D协作接口】：检索模块调用此方法在指定集合中进行文档检索
        数据格式：输入为查询字符串，输出为Document对象列表
        """
        if not query:
            return []
        
        actual_collection_name = self._resolve_collection_name(collection_name)
        
        try:
            db = self._get_or_create_collection(actual_collection_name)
            results = db.similarity_search(query, k=k)
            return results
        except Exception as e:
            raise RuntimeError(f"在集合 {actual_collection_name} 中检索失败: {str(e)}") from e

    def search_cross_collections(self, query: str, collections: list = None, k: int = 3) -> list:
        """
        跨多个集合检索相关文档
        
        参数：
            query (str): 查询文本
            collections (list): 要检索的集合名称列表，默认为所有集合
            k (int): 每个集合返回的文档数量，默认为3
        
        返回：
            list[dict]: 检索到的文档列表，包含来源集合信息
        
        【人D协作接口】：检索模块调用此方法进行跨集合检索
        数据格式：输出为包含document和collection字段的字典列表
        
        设计思路：
            - 在多个集合中分别检索
            - 合并结果并按相似度排序
            - 返回包含来源信息的结果
        """
        if not query:
            return []
        
        if collections is None:
            collections = list(config.VECTOR_DB_COLLECTIONS.keys())
        
        all_results = []
        
        for collection in collections:
            actual_collection_name = self._resolve_collection_name(collection)
            try:
                db = self._get_or_create_collection(actual_collection_name)
                results = db.similarity_search_with_score(query, k=k)
                
                for doc, score in results:
                    all_results.append({
                        "document": doc,
                        "collection": actual_collection_name,
                        "score": score,
                    })
            except Exception as e:
                print(f"在集合 {actual_collection_name} 中检索失败: {str(e)}")
        
        # 按相似度分数排序（分数越低越相似）
        all_results.sort(key=lambda x: x["score"])
        
        return all_results

    def get_collection_info(self, collection_name: str = None) -> dict:
        """
        获取集合信息
        
        参数：
            collection_name (str, optional): 集合名称或类别名称，默认为获取所有集合信息
        
        返回：
            dict: 集合信息字典
        
        【人B协作接口】：文档管理模块调用此方法获取集合信息
        数据格式：包含集合名称、类别、文档数量等信息
        """
        if collection_name is None:
            # 返回所有集合信息
            info = {}
            for category, name in config.VECTOR_DB_COLLECTIONS.items():
                if name in self.collections:
                    db = self.collections[name]
                    info[name] = {
                        "category": category,
                        "document_count": len(db.get()["ids"]),
                        **(self.collection_metadata.get(name, {})),
                    }
            return info
        
        actual_collection_name = self._resolve_collection_name(collection_name)
        
        if actual_collection_name in self.collections:
            db = self.collections[actual_collection_name]
            return {
                "collection_name": actual_collection_name,
                "category": self.collection_metadata.get(actual_collection_name, {}).get("category"),
                "document_count": len(db.get()["ids"]),
                **(self.collection_metadata.get(actual_collection_name, {})),
            }
        
        return {"error": f"集合 {collection_name} 不存在"}

    def delete_collection(self, collection_name: str):
        """
        删除指定集合
        
        参数：
            collection_name (str): 集合名称或类别名称
        
        【人B协作接口】：文档管理模块调用此方法删除集合
        数据格式：集合名称字符串
        """
        actual_collection_name = self._resolve_collection_name(collection_name)
        
        if actual_collection_name in self.collections:
            del self.collections[actual_collection_name]
            
            if actual_collection_name in self.collection_metadata:
                del self.collection_metadata[actual_collection_name]
            
            # 删除本地文件（如果是本地集合）
            if not config.VECTOR_DB_USE_REMOTE:
                import shutil
                collection_dir = os.path.join(self.persist_directory, actual_collection_name)
                if os.path.exists(collection_dir):
                    shutil.rmtree(collection_dir)

    def create_new_collection(self, collection_name: str, category: str = None, description: str = ""):
        """
        创建新集合
        
        参数：
            collection_name (str): 新集合名称
            category (str, optional): 集合类别
            description (str, optional): 集合描述
        
        【人B协作接口】：文档管理模块调用此方法创建新集合
        数据格式：集合名称、类别和描述字符串
        """
        if collection_name in self.collections:
            raise ValueError(f"集合 {collection_name} 已存在")
        
        self._get_or_create_collection(collection_name)
        
        self.collection_metadata[collection_name] = {
            "category": category or "custom",
            "description": description,
            "document_count": 0,
        }
        
        # 如果提供了类别，添加到配置映射中
        if category:
            config.VECTOR_DB_COLLECTIONS[category] = collection_name

    def get_retriever_for_collection(self, collection_name: str = "default", search_kwargs: dict = None) -> object:
        """
        获取指定集合的检索器
        
        参数：
            collection_name (str): 集合名称或类别名称，默认为"default"
            search_kwargs (dict, optional): 检索参数，如{"k": 3}
        
        返回：
            Retriever: 检索器对象
        
        【人D协作接口】：检索模块调用此方法获取指定集合的检索器
        数据格式：返回LangChain标准Retriever对象
        """
        if search_kwargs is None:
            search_kwargs = {"k": config.RETRIEVAL_TOP_K}
        
        actual_collection_name = self._resolve_collection_name(collection_name)
        db = self._get_or_create_collection(actual_collection_name)
        
        return db.as_retriever(search_kwargs=search_kwargs)


vector_db_extension = VectorDBExtension()
