import os
import sys

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
BACK_DIR = os.path.join(os.path.dirname(TEST_DIR), "back")
sys.path.insert(0, BACK_DIR)

from config import config
from document_processor import document_processor
from vector_db import vector_db_service


def process_docx_to_vector(file_path, collection_name="default"):
    """
    将DOCX文件分割并存入向量数据库
    
    参数：
        file_path (str): DOCX文件路径
        collection_name (str): 目标集合名称（默认default）
    
    返回：
        dict: 处理结果统计信息
    """
    print(f"\n=== 处理DOCX文件: {os.path.basename(file_path)} ===")
    print(f"目标集合: {collection_name}")
    
    if not os.path.exists(file_path):
        print(f"✗ 文件不存在: {file_path}")
        return {"success": False, "error": "文件不存在"}
    
    try:
        print("\n1. 加载并解析DOCX文档...")
        documents = document_processor.load_and_split([file_path])
        print(f"✓ 成功解析并分割为 {len(documents)} 个文档块")
        
        if len(documents) == 0:
            print("✗ 文档内容为空，无法处理")
            return {"success": False, "error": "文档内容为空"}
        
        print("\n2. 查看文档块详情...")
        for i, doc in enumerate(documents, 1):
            content_preview = doc.page_content[:80] + "..." if len(doc.page_content) > 80 else doc.page_content
            print(f"  [{i}] 长度: {len(doc.page_content)} 字符")
            print(f"     内容: {content_preview}")
            print(f"     元数据: {doc.metadata}")
        
        print("\n3. 将文档块存入向量数据库...")
        doc_ids = vector_db_service.add_documents_to_collection(documents, collection_name)
        print(f"✓ 成功存入 {len(doc_ids)} 个文档块")
        print(f"✓ 文档ID列表: {doc_ids}")
        
        print("\n4. 验证向量数据库...")
        doc_count = vector_db_service.get_document_count()
        print(f"✓ 当前集合文档总数: {doc_count}")
        
        print("\n5. 测试检索功能...")
        query = "项目选题"
        results = vector_db_service.search_in_collection(query, collection_name, k=3)
        print(f"✓ 检索到 {len(results)} 个相关文档")
        for i, doc in enumerate(results, 1):
            content_preview = doc.page_content[:60] + "..." if len(doc.page_content) > 60 else doc.page_content
            print(f"  [{i}] {content_preview}")
        
        return {
            "success": True,
            "file_name": os.path.basename(file_path),
            "total_chunks": len(documents),
            "stored_ids": doc_ids,
            "collection_name": collection_name,
            "document_count": doc_count
        }
        
    except Exception as e:
        print(f"\n✗ 处理失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    docx_file = r"f:\RAGSearch\大一项目选题2026.docx"
    
    try:
        config.validate_config()
        print("✓ 配置验证通过")
    except ValueError as e:
        print(f"✗ 配置验证失败: {e}")
        sys.exit(1)
    
    result = process_docx_to_vector(docx_file)
    
    if result["success"]:
        print("\n=== DOCX文件处理完成 ===")
        print(f"文件: {result['file_name']}")
        print(f"分割为: {result['total_chunks']} 个文档块")
        print(f"存入集合: {result['collection_name']}")
        print(f"当前集合文档数: {result['document_count']}")
    else:
        print("\n=== DOCX文件处理失败 ===")
        print(f"错误: {result['error']}")