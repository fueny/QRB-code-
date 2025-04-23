#!/usr/bin/env python3
"""
章节分割模块 - 根据提取的目录结构将Markdown文档分割为多个章节文件
"""

import os
import sys
import argparse
from pathlib import Path
import json
import re
import logging
from typing import List, Dict, Any, Optional, Tuple

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('chapter_splitter')

class ChapterSplitter:
    """根据目录结构分割Markdown文档的类"""
    
    def __init__(self, markdown_file: str, toc: List[Dict[str, Any]]):
        """
        初始化章节分割器
        
        Args:
            markdown_file: Markdown文件路径
            toc: 目录结构列表
        """
        self.markdown_file = markdown_file
        self.toc = toc
        self.content = ""
        
        try:
            with open(markdown_file, 'r', encoding='utf-8') as f:
                self.content = f.read()
            logger.info(f"成功加载Markdown文件: {markdown_file}")
        except Exception as e:
            logger.error(f"加载Markdown文件失败: {e}")
            raise
    
    def _get_page_markers(self) -> Dict[int, int]:
        """
        获取Markdown文档中的页码标记位置
        
        Returns:
            Dict[int, int]: 页码到位置的映射
        """
        page_markers = {}
        
        # 查找页码标记 <!-- PAGE X -->
        pattern = r'<!-- PAGE (\d+) -->'
        for match in re.finditer(pattern, self.content):
            page_num = int(match.group(1)) - 1  # 转换为0索引
            position = match.start()
            page_markers[page_num] = position
        
        logger.info(f"在Markdown文档中找到 {len(page_markers)} 个页码标记")
        return page_markers
    
    def _get_chapter_markers(self) -> Dict[str, int]:
        """
        获取Markdown文档中的章节标记位置
        
        Returns:
            Dict[str, int]: 章节标识符到位置的映射
        """
        chapter_markers = {}
        
        # 查找章节标记 <!-- CHAPTER X -->
        pattern = r'<!-- CHAPTER (.*?) -->'
        for match in re.finditer(pattern, self.content):
            chapter_id = match.group(1)
            position = match.start()
            chapter_markers[chapter_id] = position
        
        logger.info(f"在Markdown文档中找到 {len(chapter_markers)} 个章节标记")
        return chapter_markers
    
    def _split_by_pdf_toc(self, output_dir: str) -> List[str]:
        """
        根据PDF目录结构分割Markdown文档
        
        Args:
            output_dir: 输出目录
            
        Returns:
            List[str]: 分割后的章节文件路径列表
        """
        # 获取页码标记
        page_markers = self._get_page_markers()
        if not page_markers:
            logger.warning("未找到页码标记，无法按PDF目录分割")
            return self._split_by_content(output_dir)
        
        # 确保目录项按页码排序
        sorted_toc = sorted(self.toc, key=lambda x: x.get('page', 0))
        
        # 提取章节内容
        chapters = []
        for i, item in enumerate(sorted_toc):
            page_num = item.get('page', 0)
            title = item.get('title', f"Chapter {i+1}")
            level = item.get('level', 1)
            
            # 查找章节起始位置
            start_pos = page_markers.get(page_num, 0)
            
            # 查找章节结束位置
            end_pos = len(self.content)
            if i < len(sorted_toc) - 1:
                next_page = sorted_toc[i+1].get('page', 0)
                end_pos = page_markers.get(next_page, end_pos)
            
            # 提取章节内容
            chapter_content = self.content[start_pos:end_pos]
            
            # 添加章节标题
            prefix = '#' * level
            chapter_content = f"{prefix} {title}\n\n{chapter_content}"
            
            chapters.append({
                'title': title,
                'level': level,
                'content': chapter_content
            })
        
        return self._save_chapters(chapters, output_dir)
    
    def _split_by_epub_toc(self, output_dir: str) -> List[str]:
        """
        根据EPUB目录结构分割Markdown文档
        
        Args:
            output_dir: 输出目录
            
        Returns:
            List[str]: 分割后的章节文件路径列表
        """
        # 获取章节标记
        chapter_markers = self._get_chapter_markers()
        if not chapter_markers:
            logger.warning("未找到章节标记，无法按EPUB目录分割")
            return self._split_by_content(output_dir)
        
        # 将目录项映射到章节标记
        chapters = []
        for i, item in enumerate(self.toc):
            title = item.get('title', f"Chapter {i+1}")
            level = item.get('level', 1)
            href = item.get('href', '')
            
            # 查找章节起始位置
            start_pos = 0
            for chapter_id, pos in chapter_markers.items():
                if href in chapter_id:
                    start_pos = pos
                    break
            
            # 如果找不到精确匹配，尝试部分匹配
            if start_pos == 0 and href:
                href_parts = href.split('#')[0]  # 移除锚点
                for chapter_id, pos in chapter_markers.items():
                    if href_parts in chapter_id:
                        start_pos = pos
                        break
            
            # 如果仍然找不到匹配，使用顺序匹配
            if start_pos == 0 and i < len(chapter_markers):
                start_pos = list(chapter_markers.values())[i]
            
            # 查找章节结束位置
            end_pos = len(self.content)
            if i < len(self.toc) - 1:
                next_href = self.toc[i+1].get('href', '')
                for chapter_id, pos in chapter_markers.items():
                    if next_href in chapter_id and pos > start_pos:
                        end_pos = pos
                        break
                
                # 如果找不到精确匹配，尝试部分匹配
                if end_pos == len(self.content) and next_href:
                    next_href_parts = next_href.split('#')[0]  # 移除锚点
                    for chapter_id, pos in chapter_markers.items():
                        if next_href_parts in chapter_id and pos > start_pos:
                            end_pos = pos
                            break
                
                # 如果仍然找不到匹配，使用顺序匹配
                if end_pos == len(self.content) and i+1 < len(chapter_markers):
                    marker_values = list(chapter_markers.values())
                    marker_values.sort()
                    for pos in marker_values:
                        if pos > start_pos:
                            end_pos = pos
                            break
            
            # 提取章节内容
            chapter_content = self.content[start_pos:end_pos]
            
            # 添加章节标题
            prefix = '#' * level
            chapter_content = f"{prefix} {title}\n\n{chapter_content}"
            
            chapters.append({
                'title': title,
                'level': level,
                'content': chapter_content
            })
        
        return self._save_chapters(chapters, output_dir)
    
    def _split_by_content(self, output_dir: str) -> List[str]:
        """
        根据内容结构分割Markdown文档（当无法使用目录时的备选方法）
        
        Args:
            output_dir: 输出目录
            
        Returns:
            List[str]: 分割后的章节文件路径列表
        """
        logger.info("使用内容结构分割Markdown文档")
        
        # 查找所有标题
        heading_pattern = r'^(#{1,6})\s+(.+?)$'
        headings = []
        
        for match in re.finditer(heading_pattern, self.content, re.MULTILINE):
            level = len(match.group(1))
            title = match.group(2).strip()
            position = match.start()
            
            headings.append({
                'title': title,
                'level': level,
                'position': position
            })
        
        # 如果没有找到标题，按固定大小分割
        if not headings:
            logger.warning("未找到标题，按固定大小分割")
            return self._split_by_size(output_dir)
        
        # 只保留顶级标题作为章节分割点
        min_level = min(h['level'] for h in headings)
        chapter_headings = [h for h in headings if h['level'] == min_level]
        
        # 提取章节内容
        chapters = []
        for i, heading in enumerate(chapter_headings):
            title = heading['title']
            level = heading['level']
            start_pos = heading['position']
            
            # 查找章节结束位置
            end_pos = len(self.content)
            if i < len(chapter_headings) - 1:
                end_pos = chapter_headings[i+1]['position']
            
            # 提取章节内容
            chapter_content = self.content[start_pos:end_pos]
            
            chapters.append({
                'title': title,
                'level': level,
                'content': chapter_content
            })
        
        return self._save_chapters(chapters, output_dir)
    
    def _split_by_size(self, output_dir: str, chunk_size: int = 50000) -> List[str]:
        """
        按固定大小分割Markdown文档
        
        Args:
            output_dir: 输出目录
            chunk_size: 每个分块的大小（字符数）
            
        Returns:
            List[str]: 分割后的章节文件路径列表
        """
        logger.info(f"按固定大小分割Markdown文档，每块约 {chunk_size} 字符")
        
        # 获取文件名（不含扩展名）
        base_name = Path(self.markdown_file).stem
        
        # 分割内容
        chunks = []
        content_length = len(self.content)
        
        for i in range(0, content_length, chunk_size):
            chunk_start = i
            # 尝试在段落边界分割
            chunk_end = min(i + chunk_size, content_length)
            if chunk_end < content_length:
                # 查找下一个段落结束位置
                next_para = self.content.find('\n\n', chunk_end)
                if next_para != -1 and next_para - chunk_end < 1000:  # 不要偏离太远
                    chunk_end = next_para + 2
            
            chunk_content = self.content[chunk_start:chunk_end]
            chunks.append({
                'title': f"{base_name} 部分 {i//chunk_size + 1}",
                'level': 1,
                'content': chunk_content
            })
        
        return self._save_chapters(chunks, output_dir)
    
    def _save_chapters(self, chapters: List[Dict[str, Any]], output_dir: str) -> List[str]:
        """
        保存章节到文件
        
        Args:
            chapters: 章节列表
            output_dir: 输出目录
            
        Returns:
            List[str]: 保存的文件路径列表
        """
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 获取文件名（不含扩展名）
        base_name = Path(self.markdown_file).stem
        
        # 保存章节
        output_files = []
        for i, chapter in enumerate(chapters):
            # 创建文件名
            safe_title = re.sub(r'[^\w\s-]', '', chapter['title']).strip().replace(' ', '_')
            if len(safe_title) > 50:  # 限制文件名长度
                safe_title = safe_title[:50]
            
            file_name = f"{base_name}_{i+1:02d}_{safe_title}.md"
            file_path = os.path.join(output_dir, file_name)
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(chapter['content'])
            
            logger.info(f"保存章节 {i+1}: {file_path}")
            output_files.append(file_path)
        
        return output_files
    
    def split(self, output_dir: str) -> List[str]:
        """
        分割Markdown文档为多个章节文件
        
        Args:
            output_dir: 输出目录
            
        Returns:
            List[str]: 分割后的章节文件路径列表
        """
        # 检查目录结构类型
        if self.toc and 'page' in self.toc[0]:
            # PDF类型目录
            return self._split_by_pdf_toc(output_dir)
        elif self.toc and 'href' in self.toc[0]:
            # EPUB类型目录
            return self._split_by_epub_toc(output_dir)
        else:
            # 无法识别的目录类型或没有目录
            logger.warning("无法识别的目录类型或没有目录，尝试按内容结构分割")
            return self._split_by_content(output_dir)

def split_chapters(markdown_file: str, toc_file: str, output_dir: str) -> List[str]:
    """
    根据目录文件分割Markdown文档
    
    Args:
        markdown_file: Markdown文件路径
        toc_file: 目录JSON文件路径
        output_dir: 输出目录
        
    Returns:
        List[str]: 分割后的章节文件路径列表
    """
    # 加载目录结构
    try:
        with open(toc_file, 'r', encoding='utf-8') as f:
            toc = json.load(f)
        logger.info(f"成功加载目录文件: {toc_file}")
    except Exception as e:
        logger.error(f"加载目录文件失败: {e}")
        toc = []
    
    # 创建分割器并分割文档
    splitter = ChapterSplitter(markdown_file, toc)
    return splitter.split(output_dir)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='根据目录结构分割Markdown文档')
    parser.add_argument('markdown_file', help='Markdown文件路径')
    parser.add_argument('--toc-file', '-t', help='目录JSON文件路径')
    parser.add_argument('--output-dir', '-o', default='output/chapters', help='输出目录')
    args = parser.parse_args()
    
    try:
        # 如果没有提供目录文件，尝试按内容结构分割
        if args.toc_file:
            output_files = split_chapters(args.markdown_file, args.toc_file, args.output_dir)
        else:
            splitter = ChapterSplitter(args.markdown_file, [])
            output_files = splitter.split(args.output_dir)
        
        print(f"分割完成，共生成 {len(output_files)} 个章节文件")
        for file in output_files:
            print(f"- {file}")
    except Exception as e:
        logger.error(f"分割失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
