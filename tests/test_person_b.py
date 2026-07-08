import os
import sys

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
BACK_DIR = os.path.join(os.path.dirname(TEST_DIR), "back")
sys.path.insert(0, BACK_DIR)

print(f"TEST_DIR: {TEST_DIR}")
print(f"BACK_DIR: {BACK_DIR}")
print(f"back exists: {os.path.exists(BACK_DIR)}")

from config import config
from document_processor import document_processor
from retrieval_engine.parser import parse_document
from retrieval_engine.text_splitter import get_splitter, split_documents


def test_document_parser():
    print("\n=== 测试人B的文档解析功能 ===")
    
    try:
        print("\n1. 测试TXT文档解析...")
        txt_file = os.path.join(BACK_DIR, "example.txt")
        docs = parse_document(txt_file)
        print(f"✓ TXT解析成功，生成 {len(docs)} 个Document")
        print(f"  - 内容预览: {docs[0].page_content[:50]}...")
        print(f"  - 元数据: {docs[0].metadata}")
        
    except Exception as e:
        print(f"✗ TXT解析失败: {str(e)}")
    
    try:
        print("\n2. 测试加载不存在的文件...")
        try:
            parse_document("non_existent.txt")
            print("✗ 应该抛出异常")
        except (FileNotFoundError, ValueError) as e:
            print(f"✓ 正确抛出异常: {type(e).__name__}")
            
    except Exception as e:
        print(f"✗ 异常处理失败: {str(e)}")


def test_text_splitter():
    print("\n=== 测试人B的段落分割功能 ===")
    
    from langchain_core.documents import Document
    
    try:
        print("\n1. 创建测试文档...")
        test_text = """这是第一段。这是第一段的继续。
        
这是第二段。这是第二段的继续。这是第二段的继续。这是第二段的继续。

这是第三段。"""
        
        docs = [Document(page_content=test_text, metadata={"source": "test"})]
        print(f"✓ 创建测试文档成功")
        
        print("\n2. 测试段落分割...")
        split_docs = split_documents(docs)
        print(f"✓ 分割成功，生成 {len(split_docs)} 个文档块")
        
        for i, doc in enumerate(split_docs, 1):
            print(f"  [{i}] 长度: {len(doc.page_content)} 字符")
            print(f"     内容: {doc.page_content}")
            
    except Exception as e:
        print(f"✗ 段落分割失败: {str(e)}")
    
    try:
        print("\n3. 测试自定义分割参数...")
        custom_splitter = get_splitter(chunk_size=100, chunk_overlap=10)
        docs = [Document(page_content="A" * 250, metadata={"source": "test"})]
        split_docs = custom_splitter.split_documents(docs)
        print(f"✓ 自定义参数分割成功，生成 {len(split_docs)} 个文档块")
        
    except Exception as e:
        print(f"✗ 自定义参数分割失败: {str(e)}")


def test_document_processor_integration():
    print("\n=== 测试DocumentProcessor整合人B功能 ===")
    
    try:
        print("\n1. 测试load_and_split方法...")
        test_file = os.path.join(BACK_DIR, "example.txt")
        docs = document_processor.load_and_split([test_file])
        print(f"✓ load_and_split成功，生成 {len(docs)} 个文档块")
        
        for i, doc in enumerate(docs[:3], 1):
            print(f"  [{i}] 长度: {len(doc.page_content)} 字符")
            
    except Exception as e:
        print(f"✗ load_and_split失败: {str(e)}")
    
    try:
        print("\n2. 测试load_and_split_with_custom_params方法...")
        test_file = os.path.join(BACK_DIR, "example.txt")
        docs = document_processor.load_and_split_with_custom_params(
            [test_file], chunk_size=300, chunk_overlap=30
        )
        print(f"✓ 自定义参数分割成功，生成 {len(docs)} 个文档块")
        
    except Exception as e:
        print(f"✗ 自定义参数分割失败: {str(e)}")


def test_config_integration():
    print("\n=== 测试人B功能配置项 ===")
    
    try:
        print("\n1. 检查段落分割配置...")
        print(f"✓ DOCUMENT_CHUNK_SIZE: {config.DOCUMENT_CHUNK_SIZE}")
        print(f"✓ DOCUMENT_CHUNK_OVERLAP: {config.DOCUMENT_CHUNK_OVERLAP}")
        print(f"✓ DOCUMENT_SEPARATORS: {config.DOCUMENT_SEPARATORS}")
        
        print("\n2. 检查OCR配置...")
        print(f"✓ OCR_ENABLED: {config.OCR_ENABLED}")
        print(f"✓ TESSERACT_CMD: {config.TESSERACT_CMD}")
        print(f"✓ OCR_MIN_TEXT_LENGTH: {config.OCR_MIN_TEXT_LENGTH}")
        
    except Exception as e:
        print(f"✗ 配置检查失败: {str(e)}")


if __name__ == "__main__":
    try:
        config.validate_config()
        print("✓ 配置验证通过")
    except ValueError as e:
        print(f"✗ 配置验证失败: {e}")
    
    test_document_parser()
    test_text_splitter()
    test_document_processor_integration()
    test_config_integration()
    
    print("\n=== 人B负责模块测试完成 ===")