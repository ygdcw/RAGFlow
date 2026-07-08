# retrieval_engine/__init__.py
# 【人B负责】段落分割功能模块
# 提供文档解析和段落分割功能
# 接口规范：供【人A】DocumentProcessor调用，返回Document对象列表

# 导出文档解析器
from .parser import (
    parse_document,
    _parse_txt,
    _parse_pdf,
    _parse_pdf_ocr,
    _parse_docx,
    _parse_pptx,
)

# 导出文本分割器
from .text_splitter import (
    get_splitter,
    split_documents,
)

__all__ = [
    "parse_document",
    "_parse_txt",
    "_parse_pdf",
    "_parse_pdf_ocr",
    "_parse_docx",
    "_parse_pptx",
    "get_splitter",
    "split_documents",
]