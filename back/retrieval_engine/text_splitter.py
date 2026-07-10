# text_splitter.py
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import Iterator

def get_splitter(chunk_size=500, chunk_overlap=80):
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", ".", "！", "？", " ", ""]
    )

def split_documents(docs: list[Document]) -> list[Document]:
    splitter = get_splitter()
    return splitter.split_documents(docs)

def split_text_incrementally(text: str, chunk_size=500, chunk_overlap=80) -> Iterator[str]:
    """增量分割文本，返回迭代器，减少内存占用"""
    separators = ["\n\n", "\n", "。", ".", "！", "？", " "]
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = min(start + chunk_size, text_length)
        
        if end < text_length:
            for sep in separators:
                idx = text.rfind(sep, start + chunk_overlap, end)
                if idx > start:
                    end = idx + len(sep)
                    break
        
        chunk = text[start:end]
        
        if chunk.strip():
            yield chunk
        
        start = end - chunk_overlap
        if start < 0:
            start = 0