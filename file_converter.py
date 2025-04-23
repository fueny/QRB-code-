#!/usr/bin/env python3
"""
文件转换模块 - 检测并转换不同格式的书籍为Markdown格式
支持的格式: PDF, EPUB, 等
"""

import os
import sys
import argparse
from pathlib import Path
import logging
from typing import Optional, Tuple

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
logger = logging.getLogger('file_converter')

class BookFormatDetector:
    """检测书籍格式的类"""

    @staticmethod
    def detect_format(file_path: str) -> str:
        """
        检测文件格式

        Args:
            file_path: 文件路径

        Returns:
            str: 文件格式 ('pdf', 'epub', 'unknown')
        """
        file_path = Path(file_path)
        extension = file_path.suffix.lower()

        if extension == '.pdf':
            return 'pdf'
        elif extension == '.epub':
            return 'epub'
        else:
            # 尝试通过文件内容检测
            try:
                with open(file_path, 'rb') as f:
                    header = f.read(8)  # 读取文件头部

                if header.startswith(b'%PDF'):
                    return 'pdf'
                elif b'mimetypeapplication/epub' in header:
                    return 'epub'
            except Exception as e:
                logger.error(f"检测文件格式时出错: {e}")

        return 'unknown'

class PDFConverter:
    """PDF转换为Markdown的类"""

    def __init__(self, file_path: str):
        """
        初始化PDF转换器

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

    def extract_toc(self) -> list:
        """
        提取PDF的目录结构

        Returns:
            list: 目录结构列表，每项包含 {'title': 标题, 'page': 页码, 'level': 层级}
        """
        toc = []

        # 尝试从PDF元数据中提取目录
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
                return toc
        except Exception as e:
            logger.warning(f"从PDF元数据提取目录失败: {e}")

        # 如果元数据中没有目录，尝试通过文本分析识别目录
        # 这里使用一个简单的启发式方法，实际项目中可能需要更复杂的算法
        try:
            # 查找可能的目录页
            potential_toc_pages = []
            for i, page in enumerate(self.plumber_pdf.pages[:10]):  # 只检查前10页
                text = page.extract_text() or ""
                # 查找常见的目录标题
                if any(title in text.lower() for title in ["目录", "contents", "table of contents", "toc"]):
                    potential_toc_pages.append(i)

            # 从潜在的目录页中提取目录项
            for page_idx in potential_toc_pages:
                page = self.plumber_pdf.pages[page_idx]
                text = page.extract_text() or ""
                lines = text.split('\n')

                # 简单的目录项识别
                for line in lines:
                    # 查找包含页码的行
                    if any(c.isdigit() for c in line) and len(line.strip()) > 5:
                        # 尝试分离标题和页码
                        parts = line.strip().rsplit(' ', 1)
                        if len(parts) == 2 and parts[1].isdigit():
                            title, page_num = parts
                            toc.append({
                                'title': title.strip(),
                                'page': int(page_num),
                                'level': 1  # 默认层级
                            })

            if toc:
                logger.info(f"通过文本分析识别到 {len(toc)} 个目录项")
                return toc
        except Exception as e:
            logger.warning(f"通过文本分析识别目录失败: {e}")

        logger.warning("无法提取PDF目录，将使用页码作为章节划分")
        # 如果无法提取目录，则使用页码作为章节划分
        total_pages = len(self.pdf.pages)
        # 每10页创建一个章节
        for i in range(0, total_pages, 10):
            end_page = min(i + 9, total_pages - 1)
            toc.append({
                'title': f"第 {i+1}-{end_page+1} 页",
                'page': i,
                'level': 1
            })

        return toc

    def convert_to_markdown(self, output_path: str) -> str:
        """
        将PDF转换为Markdown

        Args:
            output_path: 输出Markdown文件路径

        Returns:
            str: 输出文件路径
        """
        logger.info(f"开始将PDF转换为Markdown: {self.file_path}")

        total_pages = len(self.pdf.pages)

        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # 使用临时文件处理大型PDF，避免内存溢出
        temp_file = output_path + ".temp"

        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                # 添加文档标题
                file_name = Path(self.file_path).stem
                f.write(f"# {file_name}\n\n")

                # 逐页提取文本并直接写入文件，避免在内存中保存整个文档
                for i, page in enumerate(self.plumber_pdf.pages):
                    try:
                        if i % 10 == 0:  # 每10页记录一次日志，减少日志量
                            logger.info(f"处理第 {i+1}/{total_pages} 页")

                        text = page.extract_text()
                        if text:
                            # 添加页码标记，便于后续处理
                            f.write(f"\n\n<!-- PAGE {i+1} -->\n\n")
                            f.write(text + "\n")

                        # 每处理10页刷新一次文件缓冲区
                        if i % 10 == 0:
                            f.flush()

                    except Exception as e:
                        logger.error(f"处理第 {i+1} 页时出错: {e}")
                        f.write(f"\n\n<!-- ERROR: 处理第 {i+1} 页时出错 -->\n\n")
                        # 继续处理下一页，而不是中断整个转换过程
                        continue

            # 重命名临时文件为最终文件
            os.replace(temp_file, output_path)
            logger.info(f"PDF转换完成，已保存到: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"PDF转换过程中发生错误: {e}")
            # 如果临时文件存在，尝试保留它作为恢复点
            if os.path.exists(temp_file):
                recovery_file = output_path + ".recovery"
                try:
                    os.rename(temp_file, recovery_file)
                    logger.info(f"已保存恢复文件: {recovery_file}")
                    return recovery_file
                except:
                    logger.error(f"无法保存恢复文件")
            raise

class EPUBConverter:
    """EPUB转换为Markdown的类"""

    def __init__(self, file_path: str):
        """
        初始化EPUB转换器

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

    def extract_toc(self) -> list:
        """
        提取EPUB的目录结构

        Returns:
            list: 目录结构列表，每项包含 {'title': 标题, 'href': 链接, 'level': 层级}
        """
        toc = []

        # 尝试从EPUB的导航文档中提取目录
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

        # 如果没有导航文档，尝试从spine中提取章节
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

    def convert_to_markdown(self, output_path: str) -> str:
        """
        将EPUB转换为Markdown

        Args:
            output_path: 输出Markdown文件路径

        Returns:
            str: 输出文件路径
        """
        logger.info(f"开始将EPUB转换为Markdown: {self.file_path}")

        markdown_content = []

        # 添加文档标题
        title = "未知标题"
        if self.book.get_metadata('DC', 'title'):
            title = self.book.get_metadata('DC', 'title')[0][0]

        markdown_content.append(f"# {title}\n\n")

        # 提取作者信息
        if self.book.get_metadata('DC', 'creator'):
            authors = [author[0] for author in self.book.get_metadata('DC', 'creator')]
            markdown_content.append(f"**作者**: {', '.join(authors)}\n\n")

        # 处理所有HTML内容项
        items = list(self.book.get_items_of_type(ebooklib.ITEM_DOCUMENT))

        for i, item in enumerate(items):
            logger.info(f"处理第 {i+1}/{len(items)} 个文档")

            # 添加章节标记，便于后续处理
            markdown_content.append(f"\n\n<!-- CHAPTER {item.get_name()} -->\n\n")

            # 解析HTML内容
            soup = BeautifulSoup(item.content, 'html.parser')

            # 提取标题
            h_tag = soup.find(['h1', 'h2', 'h3', 'h4'])
            if h_tag:
                title = h_tag.get_text().strip()
                markdown_content.append(f"## {title}\n\n")

            # 提取段落
            for p in soup.find_all(['p', 'div']):
                text = p.get_text().strip()
                if text:
                    markdown_content.append(f"{text}\n\n")

        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(markdown_content))

        logger.info(f"EPUB转换完成，已保存到: {output_path}")
        return output_path

class BookConverter:
    """统一的书籍转换接口"""

    @staticmethod
    def convert(input_file: str, output_dir: str) -> Tuple[str, list]:
        """
        转换书籍为Markdown格式

        Args:
            input_file: 输入文件路径
            output_dir: 输出目录

        Returns:
            Tuple[str, list]: (输出文件路径, 目录结构)
        """
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

        # 检测文件格式
        file_format = BookFormatDetector.detect_format(input_file)
        logger.info(f"检测到文件格式: {file_format}")

        # 根据格式选择转换器
        if file_format == 'pdf':
            converter = PDFConverter(input_file)
        elif file_format == 'epub':
            converter = EPUBConverter(input_file)
        else:
            raise ValueError(f"不支持的文件格式: {file_format}")

        # 提取目录
        toc = converter.extract_toc()

        # 转换为Markdown
        output_file = os.path.join(output_dir, f"{Path(input_file).stem}.md")
        output_path = converter.convert_to_markdown(output_file)

        return output_path, toc

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='将书籍转换为Markdown格式')
    parser.add_argument('input_file', help='输入文件路径')
    parser.add_argument('--output-dir', '-o', default='output/converted', help='输出目录')
    args = parser.parse_args()

    try:
        output_path, toc = BookConverter.convert(args.input_file, args.output_dir)
        print(f"转换完成，输出文件: {output_path}")
        print(f"提取到 {len(toc)} 个目录项")
    except Exception as e:
        logger.error(f"转换失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
