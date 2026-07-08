# text_splitter.py
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


def get_splitter(chunk_size: int = 500, chunk_overlap: int = 80):
    """返回一个配置好的分块器（可自定义 chunk 大小和重叠量）"""
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", ".", "！", "？", " ", ""]
    )


def merge_short_chunks(docs: list[Document], min_length: int = 100) -> list[Document]:
    """
    将长度小于 min_length 的碎片合并到前一个 chunk 中，
    避免产生大量孤立短文本，提高检索质量。
    """
    if not docs:
        return docs
    merged = []
    for doc in docs:
        if merged and len(doc.page_content) < min_length:
            # 合并内容，保留前一个 chunk 的元数据
            merged[-1].page_content += "\n" + doc.page_content
        else:
            merged.append(doc)
    return merged


def split_documents(
    docs: list[Document],
    chunk_size: int = 500,
    chunk_overlap: int = 80
) -> list[Document]:
    """
    完整的文档分块流程：
    1. 使用 RecursiveCharacterTextSplitter 切分
    2. 自动合并过短的 chunk（< 100 字符）
    """
    splitter = get_splitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = splitter.split_documents(docs)
    chunks = merge_short_chunks(chunks, min_length=100)
    return chunks