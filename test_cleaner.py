#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging
from content_cleaner import ContentCleaner

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_cleaner')

def main():
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("用法: python test_cleaner.py <输入文件>")
        sys.exit(1)

    input_file = sys.argv[1]

    # 创建测试目录
    os.makedirs("test/chapters", exist_ok=True)
    os.makedirs("test/cleaned", exist_ok=True)

    # 创建测试文件
    test_content = """# 第一章：测试标题

<!-- PAGE 1 -->

这是第一章的内容。这是一个测试文件，用于测试内容清理功能。

这段文本包含一些常见的问题，比如重复的单词单词单词，错误的标点符号；；；还有一些格式问题。
这行没有适当的换行符这很容易导致阅读困难。

#第二章：另一个测试标题（这个标题格式错误，没有空格）

<!-- PAGE 2 -->

这是第二章的内容。这章将测试更多的清理功能。

这段文本有一些排版问题,比如逗号后面没有空格,或者句子之间没有适当的间隔。这很难阅读。
-这是一个错误格式的列表项
-这也是错误格式的列表项

# 第三章：最后的测试

<!-- PAGE 3 -->

这是最后一章。我们将测试一些特殊情况。

这段文本包含一些特殊字符和符号：@#$%^&*()。还有一些数字123和英文单词mixed in。
这段文本包含一些乱码字符：�����这些应该被清理掉。

*这是一个未闭合的强调标记

THE END
"""

    # 保存测试文件
    test_file_path = os.path.join("test/chapters", os.path.basename(input_file))
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write(test_content)

    logger.info(f"已创建测试文件: {test_file_path}")

    # 初始化内容清理器
    cleaner = ContentCleaner()

    # 清理文件
    output_file = os.path.join("test/cleaned", os.path.basename(input_file))
    cleaner.clean_file(test_file_path, output_file)

    logger.info(f"清理后的文件: {output_file}")

    # 显示清理前后的内容
    logger.info("清理前的内容:")
    with open(test_file_path, "r", encoding="utf-8") as f:
        print(f.read())

    logger.info("清理后的内容:")
    with open(output_file, "r", encoding="utf-8") as f:
        print(f.read())

if __name__ == "__main__":
    main()
