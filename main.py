#!/usr/bin/env python3
"""
主程序 - 整合所有模块，实现完整的读书项目工作流
"""

import os
import sys
import argparse
from pathlib import Path
import logging
import json
import shutil
from typing import List, Dict, Any, Optional, Tuple

# 导入项目模块
from file_converter import BookConverter
from toc_extractor import TOCExtractor
from chapter_splitter import ChapterSplitter
from content_cleaner import ContentCleaner
from content_analyzer import ContentAnalyzer

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('reading_project')

class ReadingProject:
    """读书项目主类，整合所有功能模块"""
    
    def __init__(self, input_file: str, output_dir: str, model_name: str = "gpt-3.5-turbo"):
        """
        初始化读书项目
        
        Args:
            input_file: 输入书籍文件路径
            output_dir: 输出目录
            model_name: 使用的OpenAI模型名称
        """
        self.input_file = input_file
        self.output_dir = output_dir
        self.model_name = model_name
        
        # 创建输出目录结构
        self.converted_dir = os.path.join(output_dir, "converted")
        self.chapters_dir = os.path.join(output_dir, "chapters")
        self.cleaned_dir = os.path.join(output_dir, "cleaned")
        self.summary_dir = os.path.join(output_dir, "summary")
        
        os.makedirs(self.converted_dir, exist_ok=True)
        os.makedirs(self.chapters_dir, exist_ok=True)
        os.makedirs(self.cleaned_dir, exist_ok=True)
        os.makedirs(self.summary_dir, exist_ok=True)
        
        logger.info(f"初始化读书项目，输入文件: {input_file}, 输出目录: {output_dir}")
    
    def process(self) -> str:
        """
        处理书籍，执行完整工作流
        
        Returns:
            str: 最终总结文件路径
        """
        logger.info("开始处理书籍")
        
        # 步骤1: 检测书籍格式并转换为Markdown
        logger.info("步骤1: 检测书籍格式并转换为Markdown")
        try:
            markdown_file, toc = BookConverter.convert(self.input_file, self.converted_dir)
            logger.info(f"书籍已转换为Markdown: {markdown_file}")
            
            # 保存目录结构
            toc_file = os.path.join(self.converted_dir, f"{Path(self.input_file).stem}_toc.json")
            with open(toc_file, 'w', encoding='utf-8') as f:
                json.dump(toc, f, ensure_ascii=False, indent=2)
            logger.info(f"目录结构已保存到: {toc_file}")
        except Exception as e:
            logger.error(f"转换书籍失败: {e}")
            raise
        
        # 步骤2: 提取目录结构（如果步骤1中未能提取到完整目录）
        logger.info("步骤2: 提取目录结构")
        try:
            if not toc:
                toc = TOCExtractor.extract(self.input_file, toc_file)
                logger.info(f"从书籍中提取了 {len(toc)} 个目录项")
        except Exception as e:
            logger.error(f"提取目录结构失败: {e}")
            logger.warning("将使用内容结构分割章节")
            toc = []
        
        # 步骤3: 根据目录分割章节
        logger.info("步骤3: 根据目录分割章节")
        try:
            splitter = ChapterSplitter(markdown_file, toc)
            chapter_files = splitter.split(self.chapters_dir)
            logger.info(f"已将书籍分割为 {len(chapter_files)} 个章节")
        except Exception as e:
            logger.error(f"分割章节失败: {e}")
            raise
        
        # 步骤4: 清理章节内容
        logger.info("步骤4: 清理章节内容")
        try:
            cleaner = ContentCleaner(self.model_name)
            cleaned_files = []
            
            for chapter_file in chapter_files:
                output_file = os.path.join(self.cleaned_dir, os.path.basename(chapter_file))
                cleaned_file = cleaner.clean_file(chapter_file, output_file)
                cleaned_files.append(cleaned_file)
                logger.info(f"已清理章节: {os.path.basename(chapter_file)}")
            
            logger.info(f"已清理 {len(cleaned_files)} 个章节")
        except Exception as e:
            logger.error(f"清理章节内容失败: {e}")
            # 如果清理失败，使用原始章节文件
            logger.warning("使用原始章节文件继续处理")
            cleaned_files = chapter_files
            # 复制原始文件到cleaned目录
            for chapter_file in chapter_files:
                output_file = os.path.join(self.cleaned_dir, os.path.basename(chapter_file))
                shutil.copy(chapter_file, output_file)
                cleaned_files.append(output_file)
        
        # 步骤5: 分析章节内容
        logger.info("步骤5: 分析章节内容")
        try:
            analyzer = ContentAnalyzer(self.model_name)
            analyses = analyzer.analyze_directory(self.cleaned_dir)
            
            # 生成总结文档
            summary_file = os.path.join(self.summary_dir, "sum.md")
            analyzer.generate_summary_document(analyses, summary_file)
            logger.info(f"已生成总结文档: {summary_file}")
        except Exception as e:
            logger.error(f"分析章节内容失败: {e}")
            raise
        
        logger.info("书籍处理完成")
        return summary_file

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='读书项目 - 处理书籍并生成总结')
    parser.add_argument('input_file', help='输入书籍文件路径')
    parser.add_argument('--output-dir', '-o', default='output', help='输出目录')
    parser.add_argument('--model', '-m', default="gpt-3.5-turbo", help='使用的OpenAI模型名称')
    args = parser.parse_args()
    
    try:
        # 创建读书项目
        project = ReadingProject(args.input_file, args.output_dir, args.model)
        
        # 处理书籍
        summary_file = project.process()
        
        print(f"处理完成，总结文档已保存到: {summary_file}")
        print(f"所有输出文件已保存到: {args.output_dir}")
    except Exception as e:
        logger.error(f"处理书籍失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
