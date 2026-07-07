# test_parser.py
# 把 retrieval_engine 目录加入 Python 路径（防止导入失败）
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from retrieval_engine.parser import parse_document

# 指向刚才创建的测试文件
test_file = "test_files/hello.txt"

print("开始测试解析...")
print(f"文件路径: {test_file}")

docs = parse_document(test_file)

print(f"\n成功解析！共得到 {len(docs)} 个 Document")
for i, doc in enumerate(docs, 1):
    print(f"\n--- Document {i} ---")
    print("内容:")
    print(doc.page_content)
    print("元数据:")
    print(doc.metadata)