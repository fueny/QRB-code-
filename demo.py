#!/usr/bin/env python3
"""
示例脚本 - 演示读书项目的完整工作流程
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# 导入主程序
from main import ReadingProject

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('demo')

def run_demo(sample_file: str, output_dir: str, model_name: str = "gpt-3.5-turbo"):
    """
    运行示例演示
    
    Args:
        sample_file: 示例书籍文件路径
        output_dir: 输出目录
        model_name: 使用的OpenAI模型名称
    """
    logger.info(f"开始演示读书项目，使用示例文件: {sample_file}")
    
    # 检查示例文件是否存在
    if not os.path.exists(sample_file):
        logger.error(f"示例文件不存在: {sample_file}")
        print(f"错误: 示例文件不存在: {sample_file}")
        print("请提供一个有效的PDF或EPUB文件路径")
        sys.exit(1)
    
    # 创建输出目录
    demo_output_dir = os.path.join(output_dir, "demo")
    os.makedirs(demo_output_dir, exist_ok=True)
    
    # 创建读书项目
    project = ReadingProject(sample_file, demo_output_dir, model_name)
    
    # 处理书籍
    try:
        summary_file = project.process()
        
        print("\n" + "="*50)
        print("读书项目演示完成!")
        print("="*50)
        print(f"\n示例书籍: {os.path.basename(sample_file)}")
        print(f"总结文档: {summary_file}")
        print(f"所有输出文件已保存到: {demo_output_dir}")
        print("\n输出目录结构:")
        print(f"  {demo_output_dir}/")
        print(f"  ├── converted/ - 转换后的Markdown文件和目录结构")
        print(f"  ├── chapters/  - 分割的章节文件")
        print(f"  ├── cleaned/   - 清理后的章节文件")
        print(f"  └── summary/   - 分析结果和总结文档")
        print("\n您可以查看总结文档了解书籍的主要内容和重点。")
        print("="*50)
    except Exception as e:
        logger.error(f"演示失败: {e}")
        print(f"\n错误: 演示失败: {e}")
        print("请检查日志获取详细信息，并确保您的OpenAI API密钥配置正确。")
        sys.exit(1)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='读书项目演示')
    parser.add_argument('sample_file', help='示例书籍文件路径（PDF或EPUB）')
    parser.add_argument('--output-dir', '-o', default='output', help='输出目录')
    parser.add_argument('--model', '-m', default="gpt-3.5-turbo", help='使用的OpenAI模型名称')
    args = parser.parse_args()
    
    run_demo(args.sample_file, args.output_dir, args.model)

if __name__ == '__main__':
    main()
