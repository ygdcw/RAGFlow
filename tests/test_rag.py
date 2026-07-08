import os
import sys

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
BACK_DIR = os.path.join(os.path.dirname(TEST_DIR), "back")
sys.path.insert(0, BACK_DIR)

from config import config
from document_processor import document_processor
from vector_db import vector_db_service
from rag_chain import rag_chain


def test_rag_system():
    """
    测试RAG系统完整流程
    """
    print("=== RAG系统测试 ===")
    
    try:
        config.validate_config()
        print("✓ 配置验证通过")
    except ValueError as e:
        print(f"✗ 配置验证失败: {e}")
        return
    
    try:
        print("\n1. 加载文档...")
        test_file = os.path.join(BACK_DIR, "example.txt")
        documents = document_processor.load_and_split([test_file])
        print(f"✓ 加载并分割 {len(documents)} 个文档块")
    except Exception as e:
        print(f"✗ 文档加载失败: {e}")
        return
    
    try:
        print("\n2. 添加到向量数据库...")
        doc_ids = vector_db_service.add_documents(documents)
        print(f"✓ 添加 {len(doc_ids)} 个文档到向量数据库")
        print(f"✓ 当前文档总数: {vector_db_service.get_document_count()}")
    except Exception as e:
        print(f"✗ 添加文档失败: {e}")
        return
    
    try:
        print("\n3. 测试检索...")
        query = "什么是RAG？"
        results = vector_db_service.similarity_search(query, k=3)
        print(f"✓ 检索到 {len(results)} 个相关文档")
        for i, doc in enumerate(results, 1):
            print(f"  [{i}] {doc.page_content[:50]}...")
    except Exception as e:
        print(f"✗ 检索失败: {e}")
        return
    
    try:
        print("\n4. 测试RAG问答...")
        query = "什么是深度学习？"
        result = rag_chain.query_with_sources(query)
        print(f"✓ 回答生成成功")
        print(f"AI: {result['answer']}")
        
        if result["formatted_sources"]:
            print("\n参考片段:")
            for i, source in enumerate(result["formatted_sources"], 1):
                print(f"  [{i}] {source['content']}")
    except Exception as e:
        print(f"✗ 问答失败: {e}")
        return
    
    print("\n=== 测试完成 ===")


if __name__ == "__main__":
    test_rag_system()
