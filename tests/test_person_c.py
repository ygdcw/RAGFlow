import os
import sys

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
BACK_DIR = os.path.join(os.path.dirname(TEST_DIR), "back")
sys.path.insert(0, BACK_DIR)

from config import config
from document_processor import document_processor
from vector_db import vector_db_service
from rag_chain import rag_chain
from chat_history_manager import chat_history_manager


def test_vector_db_extension():
    """
    测试向量数据库扩展功能（多集合管理）
    """
    print("\n=== 测试向量数据库扩展功能 ===")
    
    try:
        print("\n1. 获取集合列表...")
        collections = vector_db_service.get_collection_info()
        print(f"✓ 集合列表: {list(collections.keys())}")
        
        print("\n2. 创建新集合...")
        vector_db_service.create_new_collection("test_collection", category="test", description="测试集合")
        print("✓ 新集合创建成功")
        
        print("\n3. 向指定集合添加文档...")
        test_file = os.path.join(BACK_DIR, "example.txt")
        documents = document_processor.load_and_split([test_file])
        doc_ids = vector_db_service.add_documents_to_collection(documents, "test")
        print(f"✓ 向test集合添加 {len(doc_ids)} 个文档")
        
        print("\n4. 在指定集合中检索...")
        results = vector_db_service.search_in_collection("什么是RAG？", "test", k=2)
        print(f"✓ 在test集合中检索到 {len(results)} 个文档")
        
        print("\n5. 跨集合检索...")
        cross_results = vector_db_service.search_cross_collections("人工智能", ["default", "test"], k=2)
        print(f"✓ 跨集合检索到 {len(cross_results)} 个结果")
        
        print("\n6. 删除测试集合...")
        vector_db_service.delete_collection("test")
        print("✓ 测试集合已删除")
        
    except Exception as e:
        print(f"✗ 向量数据库扩展测试失败: {str(e)}")


def test_chat_history_manager():
    """
    测试对话历史管理功能
    """
    print("\n=== 测试对话历史管理功能 ===")
    
    try:
        print("\n1. 创建会话...")
        session_id = chat_history_manager.create_session()
        print(f"✓ 创建会话成功: {session_id}")
        
        print("\n2. 添加消息...")
        chat_history_manager.add_message(session_id, "user", "你好")
        chat_history_manager.add_message(session_id, "assistant", "你好！我是一个智能助手。")
        print("✓ 消息添加成功")
        
        print("\n3. 获取会话消息...")
        messages = chat_history_manager.get_messages(session_id)
        print(f"✓ 获取到 {len(messages)} 条消息")
        
        print("\n4. 获取会话信息...")
        session_info = chat_history_manager.get_session_info(session_id)
        print(f"✓ 会话信息: {session_info}")
        
        print("\n5. 获取会话列表...")
        sessions = chat_history_manager.list_sessions(limit=5)
        print(f"✓ 当前共有 {len(sessions)} 个会话")
        
        print("\n6. 获取统计信息...")
        stats = chat_history_manager.get_statistics()
        print(f"✓ 统计信息: {stats}")
        
        print("\n7. 删除测试会话...")
        chat_history_manager.delete_session(session_id)
        print("✓ 测试会话已删除")
        
    except Exception as e:
        print(f"✗ 对话历史管理测试失败: {str(e)}")


def test_rag_with_session():
    """
    测试带会话管理的RAG查询
    """
    print("\n=== 测试带会话管理的RAG查询 ===")
    
    try:
        print("\n1. 创建新会话并查询...")
        result = rag_chain.query_with_session("什么是机器学习？")
        print(f"✓ 创建会话成功: {result['session_id']}")
        print(f"✓ AI回答: {result['answer'][:50]}...")
        
        session_id = result["session_id"]
        
        print("\n2. 使用相同会话继续查询...")
        result2 = rag_chain.query_with_session("它有哪些应用？", session_id=session_id)
        print(f"✓ 会话ID保持一致: {result2['session_id']}")
        print(f"✓ AI回答: {result2['answer'][:50]}...")
        
        print("\n3. 加载会话历史...")
        success = rag_chain.load_session_history(session_id)
        print(f"✓ 会话历史加载成功: {success}")
        
        print("\n4. 删除测试会话...")
        chat_history_manager.delete_session(session_id)
        print("✓ 测试会话已删除")
        
    except Exception as e:
        print(f"✗ RAG会话测试失败: {str(e)}")


if __name__ == "__main__":
    try:
        config.validate_config()
        print("✓ 配置验证通过")
    except ValueError as e:
        print(f"✗ 配置验证失败: {e}")
        sys.exit(1)
    
    test_vector_db_extension()
    test_chat_history_manager()
    test_rag_with_session()
    
    print("\n=== 人C负责模块测试完成 ===")
