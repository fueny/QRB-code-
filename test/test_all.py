#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
综合测试脚本，用于测试读书项目的所有主要功能
"""

import os
import sys
import logging
import shutil
import argparse
import json
from pathlib import Path

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入项目模块
from file_converter import BookConverter
from chapter_splitter import ChapterSplitter
from content_cleaner import ContentCleaner
from content_analyzer import ContentAnalyzer
from toc_extractor import TOCExtractor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_all')

class TestAll:
    """测试所有功能的类"""

    def __init__(self):
        """初始化测试环境"""
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.test_dir, 'data')
        self.output_dir = os.path.join(self.test_dir, 'output')

        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, 'chapters'), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, 'cleaned'), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, 'converted'), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, 'summary'), exist_ok=True)

        # 测试文件路径
        self.test_md_file = os.path.join(self.data_dir, 'test_content.md')
        self.converted_md_file = os.path.join(self.output_dir, 'converted', 'test_content.md')

        # 复制测试文件到转换目录
        shutil.copy(self.test_md_file, self.converted_md_file)

        # 创建目录结构文件
        self.create_toc_file()

    def create_toc_file(self):
        """创建测试用的目录结构文件"""
        toc_data = [
            {"level": 1, "title": "测试书籍：功能验证", "page": 1},
            {"level": 2, "title": "第一章：简介", "page": 1},
            {"level": 2, "title": "第二章：内容转换", "page": 2},
            {"level": 2, "title": "第三章：内容清理", "page": 3},
            {"level": 2, "title": "第四章：内容分析", "page": 4},
            {"level": 2, "title": "第五章：总结", "page": 5}
        ]

        import json
        toc_file = os.path.join(self.output_dir, 'converted', 'test_content_toc.json')
        with open(toc_file, 'w', encoding='utf-8') as f:
            json.dump(toc_data, f, ensure_ascii=False, indent=2)

        logger.info(f"创建目录结构文件: {toc_file}")

    def test_chapter_splitter(self):
        """测试章节分割功能"""
        logger.info("开始测试章节分割功能")

        try:
            # 加载目录结构
            toc_file = os.path.join(self.output_dir, 'converted', 'test_content_toc.json')
            with open(toc_file, 'r', encoding='utf-8') as f:
                toc = json.load(f)

            # 初始化章节分割器
            splitter = ChapterSplitter(self.converted_md_file, toc)

            # 分割章节
            chapter_files = splitter.split(os.path.join(self.output_dir, 'chapters'))

            # 检查分割结果
            logger.info(f"章节分割完成，共生成 {len(chapter_files)} 个章节文件")

            return True
        except Exception as e:
            logger.error(f"章节分割测试失败: {e}")
            return False

    def test_content_cleaner(self):
        """测试内容清理功能"""
        logger.info("开始测试内容清理功能")

        try:
            # 初始化内容清理器
            cleaner = ContentCleaner()

            # 清理章节文件
            chapter_files = list(Path(os.path.join(self.output_dir, 'chapters')).glob('*.md'))

            # 只清理第一个章节文件作为测试
            if chapter_files:
                test_file = str(chapter_files[0])
                output_file = os.path.join(self.output_dir, 'cleaned', os.path.basename(test_file))

                cleaner.clean_file(test_file, output_file)
                logger.info(f"内容清理完成: {output_file}")

            return True
        except Exception as e:
            logger.error(f"内容清理测试失败: {e}")
            return False

    def test_content_analyzer(self):
        """测试内容分析功能"""
        logger.info("开始测试内容分析功能")

        try:
            # 初始化内容分析器
            analyzer = ContentAnalyzer()

            # 分析章节文件
            chapter_files = list(Path(os.path.join(self.output_dir, 'cleaned')).glob('*.md'))

            # 只分析第一个章节文件作为测试
            if chapter_files:
                test_file = str(chapter_files[0])

                # 分析章节
                analysis = analyzer.analyze_chapter(test_file)

                # 保存分析结果
                output_file = os.path.join(self.output_dir, 'summary', os.path.basename(test_file).replace('.md', '_summary.md'))

                # 创建简单的总结文档
                summary_content = [
                    f"# {analysis['title']} 分析结果\n",
                    "## 章节总结\n",
                    analysis['summary'],
                    "\n## 重点内容\n"
                ]

                for point in analysis['key_points']:
                    summary_content.append(f"- {point}\n")

                # 添加值得阅读的部分
                summary_content.append("\n## 值得阅读的部分\n")
                for section in analysis['notable_sections']:
                    summary_content.append(f"### {section.get('reason', '值得阅读的部分')}\n")
                    summary_content.append(f"{section.get('content', '')}\n\n")

                # 写入文件
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write("\n".join(summary_content))

                logger.info(f"内容分析完成: {output_file}")

            return True
        except Exception as e:
            logger.error(f"内容分析测试失败: {e}")
            return False

    def run_all_tests(self):
        """运行所有测试"""
        logger.info("开始运行所有测试")

        # 测试章节分割
        chapter_split_result = self.test_chapter_splitter()

        # 测试内容清理
        content_clean_result = self.test_content_cleaner()

        # 测试内容分析
        content_analyze_result = self.test_content_analyzer()

        # 输出测试结果
        logger.info("测试结果:")
        logger.info(f"章节分割: {'成功' if chapter_split_result else '失败'}")
        logger.info(f"内容清理: {'成功' if content_clean_result else '失败'}")
        logger.info(f"内容分析: {'成功' if content_analyze_result else '失败'}")

        # 总体结果
        overall_result = chapter_split_result and content_clean_result and content_analyze_result
        logger.info(f"总体测试结果: {'成功' if overall_result else '失败'}")

        return overall_result

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='测试读书项目的所有功能')
    parser.add_argument('--clean', action='store_true', help='清理测试输出目录')
    args = parser.parse_args()

    # 清理测试输出目录
    if args.clean:
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
            logger.info(f"已清理测试输出目录: {output_dir}")
        return

    # 运行测试
    test = TestAll()
    result = test.run_all_tests()

    # 返回测试结果
    sys.exit(0 if result else 1)

if __name__ == '__main__':
    main()
