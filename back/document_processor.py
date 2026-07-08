import os
from langchain_core.documents import Document
from config import config

# 【人B整合】导入人B实现的文档解析器和文本分割器
from retrieval_engine.parser import parse_document
from retrieval_engine.text_splitter import get_splitter, split_documents as b_split_documents


class DocumentProcessor:
    """
    文档处理类
    负责加载、解析和分割文档
    
    【人A负责】：基础文档处理功能
    【人B整合】：文档解析器和段落分割功能已整合
    【协作需求】：
    - 【人B】提供了多种文件格式解析器（txt、pdf、docx、pptx）和段落分割器
    - 【人C】向量数据库模块调用此类处理文档
    """

    def __init__(self):
        """
        初始化文档处理器
        使用人B的文本分割器
        """
        # 使用人B的文本分割器，支持自定义chunk_size和chunk_overlap
        self.splitter = get_splitter(
            chunk_size=config.DOCUMENT_CHUNK_SIZE,
            chunk_overlap=config.DOCUMENT_CHUNK_OVERLAP
        )

    def load_text_file(self, file_path):
        """
        加载文本文件（兼容旧接口）
        
        参数：
            file_path (str): 文件路径
        
        返回：
            list[Document]: Document对象列表
        
        【人B整合】：委托给parse_document处理
        """
        return parse_document(file_path)

    def load_documents(self, file_paths):
        """
        批量加载文档
        
        参数：
            file_paths (list[str]): 文件路径列表
        
        返回：
            list[Document]: Document对象列表
        
        【人B整合】：使用人B的parse_document函数，支持txt、pdf、docx、pptx格式
        接口规范：根据文件扩展名自动选择对应的解析器
        数据格式：Document对象列表，包含page_content和metadata字段
        """
        all_docs = []
        
        for file_path in file_paths:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            try:
                docs = parse_document(file_path)
                all_docs.extend(docs)
            except ValueError as e:
                raise ValueError(f"不支持的文件格式: {file_path}") from e
            except Exception as e:
                raise RuntimeError(f"加载文件 {file_path} 失败: {str(e)}") from e
        
        return all_docs

    def split_documents(self, documents):
        """
        分割文档为小块
        
        参数：
            documents (list[Document]): Document对象列表
        
        返回：
            list[Document]: 分割后的Document对象列表
        
        【人B整合】：使用人B的段落分割器
        【人C协作接口】：向量数据库模块调用此方法处理文档
        数据格式：输入为Document对象列表，输出为分割后的Document对象列表
        
        人B的段落分割逻辑：
        - 使用RecursiveCharacterTextSplitter
        - 支持自定义chunk_size（默认500）和chunk_overlap（默认80）
        - 分隔符优先级：["\n\n", "\n", "。", ".", "！", "？", " ", ""]
        - 优先按段落分割，其次按换行，然后按中文标点，最后按空格和空字符串
        """
        if not documents:
            return []
        
        try:
            # 使用人B的段落分割功能
            split_docs = b_split_documents(documents)
            return split_docs
        except Exception as e:
            raise RuntimeError(f"分割文档失败: {str(e)}") from e

    def load_and_split(self, file_paths):
        """
        加载文档并分割为小块
        
        参数：
            file_paths (list[str]): 文件路径列表
        
        返回：
            list[Document]: 分割后的Document对象列表
        
        【人C协作接口】：向量数据库模块调用此方法完成文档加载和分割
        
        处理流程：
        1. 调用人B的parse_document解析文件
        2. 调用人B的split_documents进行段落分割
        3. 返回分割后的Document对象列表
        """
        documents = self.load_documents(file_paths)
        return self.split_documents(documents)

    def load_and_split_with_custom_params(self, file_paths, chunk_size=None, chunk_overlap=None):
        """
        【人B扩展方法】使用自定义参数加载文档并分割
        
        参数：
            file_paths (list[str]): 文件路径列表
            chunk_size (int, optional): 块大小，默认使用配置值
            chunk_overlap (int, optional): 重叠大小，默认使用配置值
        
        返回：
            list[Document]: 分割后的Document对象列表
        
        【人B协作接口】：允许调用方自定义分割参数
        数据格式：输入文件路径列表和分割参数，输出Document对象列表
        """
        # 创建自定义分割器
        custom_splitter = get_splitter(
            chunk_size=chunk_size or config.DOCUMENT_CHUNK_SIZE,
            chunk_overlap=chunk_overlap or config.DOCUMENT_CHUNK_OVERLAP
        )
        
        # 加载文档
        documents = self.load_documents(file_paths)
        
        # 使用自定义分割器分割
        if not documents:
            return []
        
        try:
            split_docs = custom_splitter.split_documents(documents)
            return split_docs
        except Exception as e:
            raise RuntimeError(f"分割文档失败: {str(e)}") from e


document_processor = DocumentProcessor()
