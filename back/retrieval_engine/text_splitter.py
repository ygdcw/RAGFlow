# text_splitter.py
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

def get_splitter(chunk_size=500, chunk_overlap=80):
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", ".", "！", "？", " ", ""]
    )

def split_documents(docs: list[Document]) -> list[Document]:
    splitter = get_splitter()
    return splitter.split_documents(docs)