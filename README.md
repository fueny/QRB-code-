# 项目建设中，无法正常使用
# 项目建设中，无法正常使用
# 项目建设中，无法正常使用
# 项目建设中，无法正常使用
# 项目建设中，无法正常使用
# 项目建设中，无法正常使用
# 项目建设中，无法正常使用
# 项目建设中，无法正常使用
# 项目建设中，无法正常使用


# 读书项目使用说明

## 项目概述

本项目是一个自动化读书工具，可以处理不同格式的书籍（如PDF、EPUB等），将其转换为Markdown格式，并通过先进的NLP技术进行内容分析，生成章节总结、提取重点内容和值得阅读的部分。

## 功能特点

1. **格式检测与转换**：自动检测书籍格式（PDF、EPUB等），并将其转换为Markdown文档
2. **目录提取**：智能识别书籍目录结构，支持多种格式的目录提取方法
3. **章节分割**：根据提取的目录将书籍内容分割为独立的章节文件
4. **内容清理**：使用langchain和langgraph审查分割后的章节，删除乱码，修复段落格式
5. **内容分析**：使用向量数据库、RAG技术和大语言模型分析章节内容，生成总结和提取重点

## 环境要求

- Python 3.12+
- OpenAI API密钥（用于内容分析）
- 足够的磁盘空间（处理大型书籍时需要）

## 安装步骤

1. 克隆或下载项目代码

2. 创建并激活虚拟环境：
   ```bash
   python3.12 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或
   venv\Scripts\activate  # Windows
   ```

3. 安装依赖：
   ```bash
   pip install langchain langchain-openai langgraph python-dotenv pypdf ebooklib beautifulsoup4 markdown faiss-cpu sentence-transformers chromadb pdfplumber
   ```

4. 配置OpenAI API密钥：
   在项目根目录创建`.env`文件，添加以下内容：
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

## 使用方法

### 基本用法

使用主程序处理书籍：

```bash
python main.py 你的书籍文件路径 --output-dir output --model gpt-3.5-turbo
```

参数说明：
- `你的书籍文件路径`：要处理的书籍文件（PDF、EPUB等）
- `--output-dir`：输出目录，默认为"output"
- `--model`：使用的OpenAI模型，默认为"gpt-3.5-turbo"

### 输出结构

处理完成后，在输出目录中会生成以下子目录：

- `converted/`：转换后的Markdown文件和提取的目录结构
- `chapters/`：根据目录分割的章节文件
- `cleaned/`：清理后的章节文件
- `summary/`：包含总结文档（sum.md）

### 单独使用各模块

也可以单独使用各个模块：

1. **文件转换**：
   ```bash
   python file_converter.py 你的书籍文件路径 --output-dir output/converted
   ```

2. **目录提取**：
   ```bash
   python toc_extractor.py 你的书籍文件路径 --output-file output/converted/toc.json
   ```

3. **章节分割**：
   ```bash
   python chapter_splitter.py 你的Markdown文件 --toc-file 你的目录文件 --output-dir output/chapters
   ```

4. **内容清理**：
   ```bash
   python content_cleaner.py --input output/chapters --output output/cleaned
   ```

5. **内容分析**：
   ```bash
   python content_analyzer.py --input-dir output/cleaned --output-file output/summary/sum.md
   ```

## 项目结构

```
reading_project/
├── main.py                # 主程序，整合所有功能
├── file_converter.py      # 文件格式检测与转换模块
├── toc_extractor.py       # 目录提取模块
├── chapter_splitter.py    # 章节分割模块
├── content_cleaner.py     # 内容清理模块
├── content_analyzer.py    # 内容分析模块
├── .env                   # 环境变量配置
├── venv/                  # 虚拟环境
└── output/                # 输出目录
    ├── converted/         # 转换后的文件
    ├── chapters/          # 分割的章节
    ├── cleaned/           # 清理后的章节
    └── summary/           # 分析结果和总结
```

## 性能优化

本项目已采用多种方法优化性能：

1. 使用向量数据库进行高效内容检索
2. 采用分块处理策略处理大型文档
3. 实现多级错误处理和回退机制
4. 使用LangGraph工作流管理复杂处理流程

## 注意事项

1. 处理大型书籍可能需要较长时间，特别是在内容分析阶段
2. 目录提取的准确性取决于书籍的格式和结构
3. 使用更强大的模型（如GPT-4）可以提高分析质量，但会增加API成本
4. 确保OpenAI API密钥有足够的配额

## 故障排除

1. **内存不足错误**：处理大型文件时可能发生，尝试增加系统内存或减小处理的文件大小
2. **API限制错误**：可能是由于OpenAI API限制，尝试降低请求频率或升级API计划
3. **格式检测失败**：尝试手动指定文件格式或转换为其他格式后再处理
4. **目录提取失败**：系统会自动回退到基于内容的分割方法

## 未来改进

1. 支持更多书籍格式（如MOBI、TXT等）
2. 改进目录提取算法，提高准确性
3. 添加多语言支持
4. 实现并行处理以提高性能
5. 添加Web界面，使用更加便捷

## 许可证

本项目采用MIT许可证。

## 联系方式

如有问题或建议，请提交Issue或联系项目维护者。
