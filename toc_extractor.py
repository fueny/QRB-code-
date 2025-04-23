#!/usr/bin/env python3
"""
目录提取模块 - 专门用于从不同格式的书籍中提取目录结构
支持的格式: PDF, EPUB, 等
"""

import os
import sys
import argparse
from pathlib import Path
import json
import logging
from typing import List, Dict, Any, Optional

# PDF处理
from pypdf import PdfReader
import pdfplumber

# EPUB处理
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('toc_extractor')

class PDFTOCExtractor:
    """从PDF提取目录的类"""
    
    def __init__(self, file_path: str):
        """
        初始化PDF目录提取器
        
        Args:
            file_path: PDF文件路径
        """
        self.file_path = file_path
        try:
            self.pdf = PdfReader(file_path)
            self.plumber_pdf = pdfplumber.open(file_path)
            logger.info(f"成功加载PDF文件: {file_path}")
        except Exception as e:
            logger.error(f"加载PDF文件失败: {e}")
            raise
    
    def extract_toc(self) -> List[Dict[str, Any]]:
        """
        提取PDF的目录结构
        
        Returns:
            List[Dict[str, Any]]: 目录结构列表，每项包含 {'title': 标题, 'page': 页码, 'level': 层级}
        """
        toc = []
        
        # 方法1: 从PDF元数据中提取目录
        try:
            outline = self.pdf.outline
            if outline:
                # 递归处理大纲
                def process_outline(outline_item, level=1):
                    results = []
                    for item in outline_item:
                        if isinstance(item, list):
                            results.extend(process_outline(item, level+1))
                        else:
                            # 提取页码和标题
                            if hasattr(item, 'title') and hasattr(item, 'page'):
                                page_num = self.pdf.get_destination_page_number(item)
                                results.append({
                                    'title': item.title,
                                    'page': page_num,
                                    'level': level
                                })
                    return results
                
                toc = process_outline(outline)
                logger.info(f"从PDF元数据中提取到 {len(toc)} 个目录项")
                if toc:
                    return toc
        except Exception as e:
            logger.warning(f"从PDF元数据提取目录失败: {e}")
        
        # 方法2: 通过文本分析识别目录页
        try:
            # 查找可能的目录页
            potential_toc_pages = []
            for i, page in enumerate(self.plumber_pdf.pages[:15]):  # 检查前15页
                text = page.extract_text() or ""
                # 查找常见的目录标题
                if any(title in text.lower() for title in ["目录", "contents", "table of contents", "toc", "index"]):
                    potential_toc_pages.append(i)
                    # 如果找到明确的目录标题页，优先处理这一页和后续几页
                    if any(title.lower() in text.lower() for title in ["目录", "contents", "table of contents"]):
                        potential_toc_pages = list(range(i, min(i+5, len(self.plumber_pdf.pages))))
                        break
            
            # 从潜在的目录页中提取目录项
            for page_idx in potential_toc_pages:
                page = self.plumber_pdf.pages[page_idx]
                text = page.extract_text() or ""
                lines = text.split('\n')
                
                # 更复杂的目录项识别
                current_level = 1
                for line in lines:
                    line = line.strip()
                    if not line or len(line) < 5:
                        continue
                    
                    # 跳过目录标题行
                    if any(title.lower() in line.lower() for title in ["目录", "contents", "table of contents", "toc", "index"]):
                        continue
                    
                    # 检测缩进级别（简单启发式方法）
                    indent_level = 1
                    if line.startswith('    ') or line.startswith('\t\t'):
                        indent_level = 3
                    elif line.startswith('  ') or line.startswith('\t'):
                        indent_level = 2
                    
                    # 查找包含页码的行
                    # 尝试多种页码模式: "标题 123", "标题..123", "标题 . . . 123"
                    if any(c.isdigit() for c in line):
                        # 尝试从行尾提取页码
                        parts = line.rsplit(' ', 1)
                        if len(parts) == 2 and parts[1].isdigit():
                            title, page_num = parts
                            toc.append({
                                'title': title.strip().rstrip('.'),
                                'page': int(page_num),
                                'level': indent_level
                            })
                            continue
                        
                        # 尝试提取带点的页码格式
                        if '...' in line or '. . .' in line:
                            parts = line.replace('. . .', '...').split('...')
                            if len(parts) == 2 and parts[1].strip().isdigit():
                                title, page_num = parts
                                toc.append({
                                    'title': title.strip(),
                                    'page': int(page_num.strip()),
                                    'level': indent_level
                                })
                                continue
                        
                        # 尝试从行中提取章节编号和标题
                        import re
                        chapter_match = re.match(r'^(第?\s*[0-9一二三四五六七八九十百千]+\s*[章节篇部])\s*(.*?)(\d+)$', line)
                        if chapter_match:
                            chapter_num, title, page_num = chapter_match.groups()
                            toc.append({
                                'title': f"{chapter_num} {title}".strip(),
                                'page': int(page_num),
                                'level': 1
                            })
                            continue
                        
                        # 尝试匹配英文章节格式 "Chapter 1: Title 123"
                        chapter_match = re.match(r'^(Chapter|Section|Part)\s+(\d+)[\s:]+(.+?)(\d+)$', line, re.IGNORECASE)
                        if chapter_match:
                            ch_type, ch_num, title, page_num = chapter_match.groups()
                            toc.append({
                                'title': f"{ch_type} {ch_num}: {title}".strip(),
                                'page': int(page_num),
                                'level': 1
                            })
                            continue
            
            if toc:
                logger.info(f"通过文本分析识别到 {len(toc)} 个目录项")
                return toc
        except Exception as e:
            logger.warning(f"通过文本分析识别目录失败: {e}")
        
        # 方法3: 使用页面布局分析
        try:
            toc_items = []
            for page_idx in range(min(15, len(self.plumber_pdf.pages))):
                page = self.plumber_pdf.pages[page_idx]
                
                # 提取文本并保留位置信息
                words = page.extract_words()
                lines = []
                current_line = []
                current_y = None
                
                # 按行分组单词
                for word in words:
                    if current_y is None or abs(word['top'] - current_y) < 5:  # 同一行的容差
                        current_line.append(word)
                        current_y = word['top']
                    else:
                        if current_line:
                            lines.append(current_line)
                        current_line = [word]
                        current_y = word['top']
                
                if current_line:
                    lines.append(current_line)
                
                # 分析每一行，查找目录模式
                for line in lines:
                    # 检查行尾是否有数字（可能是页码）
                    if line and line[-1]['text'].isdigit():
                        # 构建行文本
                        line_text = ' '.join(word['text'] for word in line[:-1])
                        page_num = int(line[-1]['text'])
                        
                        # 检查是否是有效的目录项
                        if len(line_text) > 3 and not line_text.isdigit():
                            # 估计缩进级别
                            indent_level = 1
                            if line[0]['x0'] > 100:
                                indent_level = 2
                            if line[0]['x0'] > 150:
                                indent_level = 3
                            
                            toc_items.append({
                                'title': line_text.strip(),
                                'page': page_num,
                                'level': indent_level
                            })
            
            if toc_items:
                logger.info(f"通过页面布局分析识别到 {len(toc_items)} 个目录项")
                return toc_items
        except Exception as e:
            logger.warning(f"通过页面布局分析识别目录失败: {e}")
        
        # 方法4: 如果以上方法都失败，尝试识别章节标题
        try:
            chapter_patterns = [
                r'^第\s*[0-9一二三四五六七八九十百千]+\s*[章节篇部]',  # 中文章节格式
                r'^Chapter\s+\d+',  # 英文章节格式
                r'^CHAPTER\s+\d+',  # 英文章节格式（大写）
                r'^Part\s+\d+',     # 英文部分格式
                r'^Section\s+\d+',  # 英文节格式
            ]
            
            chapters = []
            for i, page in enumerate(self.plumber_pdf.pages):
                text = page.extract_text() or ""
                lines = text.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if not line or len(line) < 5 or len(line) > 100:
                        continue
                    
                    # 检查是否匹配章节模式
                    import re
                    if any(re.match(pattern, line) for pattern in chapter_patterns):
                        chapters.append({
                            'title': line,
                            'page': i,
                            'level': 1
                        })
            
            if chapters:
                logger.info(f"通过章节标题识别到 {len(chapters)} 个章节")
                return chapters
        except Exception as e:
            logger.warning(f"通过章节标题识别目录失败: {e}")
        
        logger.warning("无法提取PDF目录，将使用页码作为章节划分")
        # 如果无法提取目录，则使用页码作为章节划分
        total_pages = len(self.pdf.pages)
        # 每10页创建一个章节
        chapters = []
        for i in range(0, total_pages, 10):
            end_page = min(i + 9, total_pages - 1)
            chapters.append({
                'title': f"第 {i+1}-{end_page+1} 页",
                'page': i,
                'level': 1
            })
        
        return chapters

class EPUBTOCExtractor:
    """从EPUB提取目录的类"""
    
    def __init__(self, file_path: str):
        """
        初始化EPUB目录提取器
        
        Args:
            file_path: EPUB文件路径
        """
        self.file_path = file_path
        try:
            self.book = epub.read_epub(file_path)
            logger.info(f"成功加载EPUB文件: {file_path}")
        except Exception as e:
            logger.error(f"加载EPUB文件失败: {e}")
            raise
    
    def extract_toc(self) -> List[Dict[str, Any]]:
        """
        提取EPUB的目录结构
        
        Returns:
            List[Dict[str, Any]]: 目录结构列表，每项包含 {'title': 标题, 'href': 链接, 'level': 层级}
        """
        toc = []
        
        # 方法1: 从EPUB的导航文档中提取目录
        nav_items = self.book.get_items_of_type(ebooklib.ITEM_NAVIGATION)
        
        if nav_items:
            for nav in nav_items:
                soup = BeautifulSoup(nav.content, 'html.parser')
                # 查找导航列表
                nav_list = soup.find('nav', {'epub:type': 'toc'})
                
                if not nav_list:
                    nav_list = soup.find('nav')
                
                if nav_list:
                    # 处理导航项
                    def process_nav_items(items, level=1):
                        results = []
                        for li in items.find_all('li', recursive=False):
                            a_tag = li.find('a')
                            if a_tag:
                                title = a_tag.get_text().strip()
                                href = a_tag.get('href', '')
                                results.append({
                                    'title': title,
                                    'href': href,
                                    'level': level
                                })
                            
                            # 处理子列表
                            ol = li.find('ol')
                            if ol:
                                results.extend(process_nav_items(ol, level+1))
                        
                        return results
                    
                    ol = nav_list.find('ol')
                    if ol:
                        toc = process_nav_items(ol)
                        logger.info(f"从EPUB导航文档中提取到 {len(toc)} 个目录项")
                        return toc
        
        # 方法2: 从NCX文件中提取目录
        ncx_items = self.book.get_items_of_type(ebooklib.ITEM_NAVIGATION)
        
        for item in ncx_items:
            if item.get_name().endswith('.ncx'):
                soup = BeautifulSoup(item.content, 'html.parser')
                nav_points = soup.find_all('navpoint')
                
                if nav_points:
                    for nav_point in nav_points:
                        # 提取层级
                        level = 1
                        parent = nav_point.parent
                        while parent and parent.name == 'navpoint':
                            level += 1
                            parent = parent.parent
                        
                        # 提取标题和链接
                        text = nav_point.find('text')
                        content = nav_point.find('content')
                        
                        if text and content:
                            title = text.get_text().strip()
                            href = content.get('src', '')
                            
                            toc.append({
                                'title': title,
                                'href': href,
                                'level': level
                            })
                    
                    logger.info(f"从NCX文件中提取到 {len(toc)} 个目录项")
                    return toc
        
        # 方法3: 如果以上方法都失败，尝试从spine中提取章节
        if not toc:
            logger.warning("无法从导航文档提取目录，尝试从spine提取章节")
            for i, item in enumerate(self.book.spine):
                if isinstance(item, tuple):
                    item_id = item[0]
                    item = self.book.get_item_with_id(item_id)
                
                if item and hasattr(item, 'get_name'):
                    title = f"章节 {i+1}"
                    # 尝试从HTML内容中提取标题
                    try:
                        soup = BeautifulSoup(item.content, 'html.parser')
                        h_tag = soup.find(['h1', 'h2', 'h3', 'h4'])
                        if h_tag:
                            title = h_tag.get_text().strip()
                    except:
                        pass
                    
                    toc.append({
                        'title': title,
                        'href': item.get_name(),
                        'level': 1
                    })
            
            if toc:
                logger.info(f"从spine中提取到 {len(toc)} 个章节")
                return toc
        
        logger.warning("无法提取EPUB目录，将使用默认章节划分")
        return toc

class TOCExtractor:
    """统一的目录提取接口"""
    
    @staticmethod
    def extract(file_path: str, output_file: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        从书籍中提取目录结构
        
        Args
(Content truncated due to size limit. Use line ranges to read in chunks)