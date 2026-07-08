# parser.py
import os
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
from docx import Document as DocxDocument
from pptx import Presentation
from langchain_core.documents import Document

# ---------- 以下是解析各种文件的辅助函数 ----------

def _table_to_markdown(table:list[list[str|None]])->str:
    """将pdfplumber提取的表格转换为Markdown格式字符串"""
    if not table:
        return ""
    #过滤完全空行
    table =[row for row in  table if any(cell and cell.strip() for cell in row)]
    if not table:
        return ""

    max_cols =max(len(row)for row in table)
    #补齐列
    for row in table:
        while len(row)<max_cols:
            row.append("")

    lines = []
    #表头
    header = table[0]
    lines.append("| "+" | ".join(str(cell).strip() if cell else "" for cell in header)+" |")
    #分割线
    lines.append("|"+"|".join(["---"]*max_cols)+"|")
    #数据行
    for row in table[1:]:
        lines.append("| " + " | ".join(str(cell).strip() if cell else "" for cell in row) + " |")
        return "\n".join(lines)



def _extract_title_from_page(page) -> str:
    """从页面字符中提取最大字体文本作为标题候选（简单启发式）"""
    chars = page.chars
    if not chars:
        return ""
    # 按行聚合，记录每行最大字体
    line_fonts = {}
    line_text = {}
    for c in chars:
        # 忽略空格和空字符
        if not c['text'].strip():
            continue
        # 简单用 y0 近似行（实际应聚合到行）
        y_key = round(c['top'], 1)  # 容差
        line_fonts[y_key] = max(line_fonts.get(y_key, 0), c.get('height', 0))
        line_text[y_key] = line_text.get(y_key, "") + c['text']

    if not line_fonts:
        return ""
    # 找到最大字体的行
    max_font = max(line_fonts.values())
    # 取所有等于最大字体的行文本，拼接成标题
    title_parts = []
    for y, font in line_fonts.items():
        if font == max_font:
            title_parts.append(line_text[y].strip())
    # 通常标题只有一行，取第一行
    title = title_parts[0] if title_parts else ""
    # 限制标题长度，避免大段文字
    if len(title) > 80:
        return title[:80] + "..."
    return title

def _parse_txt(file_path: str) -> list[Document]:
    """解析 .txt 文件，整个文件当作一个 Document"""
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    return [Document(page_content=text, metadata={"source": file_path, "file_type": "txt"})]


def _parse_pdf(file_path: str) -> list[Document]:
    docs = []
    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            # ----- 1. 提取表格 -----
            tables = page.extract_tables()
            for table_idx, table in enumerate(tables):
                if not table:
                    continue
                # 转为 Markdown 表格
                md_table = _table_to_markdown(table)
                docs.append(Document(
                    page_content=md_table,
                    metadata={
                        "source": file_path,
                        "page_number": i + 1,
                        "file_type": "pdf",
                        "content_type": "table",
                        "table_index": table_idx,
                        "section_title": ""  # 待提取
                    }
                ))

            # ----- 2. 提取文本及字体信息 -----
            # 使用 page.chars 获取字符级信息，推断标题
            text = page.extract_text()
            if not text:
                continue

            # 提取页面可能的标题（最大字体文本）
            title_candidate = _extract_title_from_page(page)
            # 去除表格区域后构建纯文本（简化：直接用 extract_text，表格文字会重复但可接受）
            docs.append(Document(
                page_content=text,
                metadata={
                    "source": file_path,
                    "page_number": i + 1,
                    "file_type": "pdf",
                    "content_type": "text",
                    "section_title": title_candidate
                }
            ))

    # 如果整个文档提取文字太少，触发 OCR（保持原逻辑）
    total_text = "".join([d.page_content for d in docs if d.metadata.get("content_type") == "text"])
    if len(total_text.strip()) < 100:
        return _parse_pdf_ocr(file_path)
    return docs


def _parse_pdf_ocr(file_path: str) -> list[Document]:
    """使用 OCR 解析图片型 PDF"""
    # Windows 用户务必修改下面这一行，改为你的 tesseract.exe 安装路径
    # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    images = convert_from_path(file_path, dpi=200)
    docs = []
    for i, img in enumerate(images):
        text = pytesseract.image_to_string(img, lang='chi_sim+eng')
        docs.append(Document(
            page_content=text,
            metadata={"source": file_path, "page_number": i + 1, "file_type": "pdf_ocr"}
        ))
    return docs


def _parse_docx(file_path: str) -> list[Document]:
    doc = DocxDocument(file_path)
    documents = []
    current_section = ""
    text_buffer = []

    # 辅助函数：刷新文本缓冲区，生成一个 Document
    def flush_text():
        nonlocal text_buffer, current_section
        if text_buffer:
            content = "\n".join(text_buffer)
            documents.append(Document(
                page_content=content,
                metadata={
                    "source": file_path,
                    "file_type": "docx",
                    "content_type": "text",
                    "section_title": current_section
                }
            ))
            text_buffer = []

    # 遍历文档中的所有块级元素（段落和表格）
    for element in doc.element.body:
        # 处理段落
        if element.tag.endswith('p'):  # w:p
            para = element
            # 获取样式
            style = para.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pStyle')
            style_name = style.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val') if style is not None else None
            # 提取文本
            text = ''.join(node.text or '' for node in para.iter() if node.tag.endswith('t')).strip()
            if not text:
                continue
            # 如果是标题样式，更新当前小节，并刷新之前的文本
            if style_name and style_name.startswith('Heading'):
                flush_text()
                current_section = text
                # 标题本身也可以作为单独的 Document（短文本有益检索）
                documents.append(Document(
                    page_content=text,
                    metadata={
                        "source": file_path,
                        "file_type": "docx",
                        "content_type": "heading",
                        "section_title": text
                    }
                ))
            else:
                text_buffer.append(text)

        # 处理表格
        elif element.tag.endswith('tbl'):  # w:tbl
            flush_text()  # 先把前面的文本保存
            table = element
            rows = table.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tr')
            table_data = []
            for row in rows:
                cells = row.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tc')
                row_data = []
                for cell in cells:
                    # 提取单元格文本（含段落）
                    cell_text = ''.join(node.text or '' for node in cell.iter() if node.tag.endswith('t')).strip()
                    row_data.append(cell_text)
                table_data.append(row_data)
            if table_data:
                md_table = _table_to_markdown(table_data)
                documents.append(Document(
                    page_content=md_table,
                    metadata={
                        "source": file_path,
                        "file_type": "docx",
                        "content_type": "table",
                        "section_title": current_section  # 继承最近的标题
                    }
                ))

    # 处理最后一段文本
    flush_text()
    return documents if documents else [Document(page_content="", metadata={"source": file_path, "file_type": "docx"})]

def _parse_pptx(file_path: str) -> list[Document]:
    prs = Presentation(file_path)
    docs = []
    for i, slide in enumerate(prs.slides):
        slide_title = ""
        slide_texts = []
        # 先找标题占位符
        for shape in slide.shapes:
            if shape.has_text_frame:
                # 如果是标题占位符，记录为标题
                if shape.is_placeholder and shape.placeholder_format.type == 1:  # 1 = Title
                    slide_title = shape.text_frame.text.strip()
                else:
                    slide_texts.append(shape.text_frame.text)
            # 处理表格
            if shape.has_table:
                table = shape.table
                table_data = []
                for row in table.rows:
                    row_data = [cell.text for cell in row.cells]
                    table_data.append(row_data)
                if table_data:
                    md_table = _table_to_markdown(table_data)
                    docs.append(Document(
                        page_content=md_table,
                        metadata={
                            "source": file_path,
                            "slide_number": i + 1,
                            "file_type": "pptx",
                            "content_type": "table",
                            "section_title": slide_title or f"幻灯片 {i+1}"
                        }
                    ))

        # 合并正文文本
        body_text = "\n".join(slide_texts)
        if body_text:
            docs.append(Document(
                page_content=body_text,
                metadata={
                    "source": file_path,
                    "slide_number": i + 1,
                    "file_type": "pptx",
                    "content_type": "text",
                    "section_title": slide_title or f"幻灯片 {i+1}"
                }
            ))
        # 如果标题单独存在（无正文），也加入
        elif slide_title:
            docs.append(Document(
                page_content=slide_title,
                metadata={
                    "source": file_path,
                    "slide_number": i + 1,
                    "file_type": "pptx",
                    "content_type": "heading",
                    "section_title": slide_title
                }
            ))
    return docs

# ---------- 统一入口函数 ----------

def parse_document(file_path: str) -> list[Document]:
    """根据文件后缀调用对应的解析器，返回 Document 列表"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.txt':
        return _parse_txt(file_path)
    elif ext == '.pdf':
        return _parse_pdf(file_path)
    elif ext == '.docx':
        return _parse_docx(file_path)
    elif ext == '.pptx':
        return _parse_pptx(file_path)
    else:
        raise ValueError(f"不支持的文件格式: {ext}")