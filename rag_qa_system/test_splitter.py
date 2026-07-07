# test_splitter.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from retrieval_engine.parser import parse_document
from retrieval_engine.text_splitter import split_documents

# 1. 先用之前的 hello.txt 解析出一个大 Document
test_file = "test_files/long_text.txt"
raw_docs = parse_document(test_file)

# 2. 分块
chunks = split_documents(raw_docs)

# 3. 打印结果
print(f"原始文档数: {len(raw_docs)}")
print(f"切分后块数: {len(chunks)}\n")

for i, chunk in enumerate(chunks, 1):
    print(f"------ Chunk {i} ------")
    print(f"长度: {len(chunk.page_content)} 字符")
    print(chunk.page_content)
    print(chunk.metadata)
    print()