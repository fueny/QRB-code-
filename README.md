# 快速读书 (QRB - Quickly Read books)

## 项目概述

QRB (Quickly Read books) 是一个智能读书辅助工具，旨在帮助读者更高效地阅读和理解书籍内容。它能够处理不同格式的书籍（如PDF、EPUB等），将其转换为结构化的Markdown文档，并通过先进的NLP技术进行内容分析，自动生成章节总结、提取重点内容和标记值得重点阅读的部分。

这个工具特别适合：
- 需要快速了解书籍核心内容的读者
- 学习和研究过程中需要提取关键信息的学生和研究人员
- 想要在有限时间内高效阅读的专业人士

## 核心功能

1. **智能格式转换**：自动检测并转换PDF、EPUB等格式的书籍为结构化Markdown文档
2. **目录结构提取**：智能识别书籍的目录结构，支持多种格式的目录提取方法
3. **章节智能分割**：根据提取的目录将书籍内容分割为独立的章节文件，便于分析和阅读
4. **内容清理优化**：使用LangChain和LangGraph技术清理文本内容，删除乱码，修复格式问题
5. **深度内容分析**：结合向量数据库和RAG技术，分析章节内容并生成以下关键信息：
   - **章节总结**：提供简洁而全面的章节内容概述
   - **重点内容提取**：自动识别并提取章节中的关键信息和核心概念
   - **值得阅读部分标记**：智能标记最值得仔细阅读的段落，并说明原因

## 环境要求

- Python 3.12+
- OpenAI API密钥或兼容的API服务（用于内容分析）
- 足够的磁盘空间（处理大型书籍时需要）

## 快速开始

1. **克隆仓库**

2. **创建并激活虚拟环境**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或
   venv\Scripts\activate  # Windows
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **配置API密钥**
   在项目根目录创建`.env`文件，添加以下内容：
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

   也可以使用其他兼容OpenAI API的服务，如Azure OpenAI或本地模型服务。

## 使用指南

### 基本用法

使用主程序一键处理整本书籍：

```bash
python main.py 你的书籍文件路径 --output-dir output --model gpt-3.5-turbo
```

**参数说明**：
- `你的书籍文件路径`：要处理的书籍文件（PDF、EPUB等）
- `--output-dir`：输出目录，默认为"output"
- `--model`：使用的语言模型，默认为"gpt-3.5-turbo"

### 输出结构

处理完成后，在输出目录中会生成以下结构：

```
output/
├── converted/  # 转换后的Markdown文件和提取的目录结构
├── chapters/   # 根据目录分割的章节文件
├── cleaned/    # 清理后的章节文件
└── summary/    # 包含总结文档和分析结果
    └── sum.md  # 主要分析结果文件
```

### 分步使用各模块

也可以分步使用各个功能模块，适合需要自定义处理流程的用户：

1. **文件格式转换**
   ```bash
   python file_converter.py 你的书籍文件路径 --output-dir output/converted
   ```

2. **目录结构提取**
   ```bash
   python toc_extractor.py 你的书籍文件路径 --output-file output/converted/toc.json
   ```

3. **章节智能分割**
   ```bash
   python chapter_splitter.py 你的Markdown文件 --toc-file 你的目录文件 --output-dir output/chapters
   ```

4. **内容清理优化**
   ```bash
   python content_cleaner.py --input output/chapters --output output/cleaned
   ```

5. **深度内容分析**
   ```bash
   python content_analyzer.py --input-dir output/cleaned --output-file output/summary/sum.md
   ```

### 分析结果示例

处理完成后，`summary/sum.md` 文件将包含以下内容：

- **总体概述**：整本书的核心内容和主要观点
- **各章节分析**：
  - 章节总结：每个章节的简明概述
  - 重点内容：自动提取的关键信息和核心概念
  - 值得阅读的部分：标记最有价值的段落，并说明为什么值得阅读

## 项目结构

```
QRB/
├── main.py                # 主程序，整合所有功能模块
├── file_converter.py      # 文件格式检测与转换模块
├── toc_extractor.py       # 目录结构提取模块
├── chapter_splitter.py    # 章节智能分割模块
├── content_cleaner.py     # 内容清理优化模块
├── content_analyzer.py    # 深度内容分析模块
├── requirements.txt       # 项目依赖列表
├── .env                   # 环境变量配置（需自行创建）
├── test/                  # 测试目录
│   ├── data/              # 测试数据
│   ├── full_test/         # 完整测试用例
│   └── test_all.py        # 综合测试脚本
└── output/                # 输出目录（自动创建）
    ├── converted/         # 转换后的文件
    ├── chapters/          # 分割的章节
    ├── cleaned/           # 清理后的章节
    └── summary/           # 分析结果和总结
```

## 技术特点

QRB 采用了多种先进技术来提高处理效率和分析质量：

1. **向量数据库检索**：使用FAISS向量数据库进行高效的语义检索
2. **RAG技术**：结合检索增强生成技术，提高内容分析的准确性和相关性
3. **LangGraph工作流**：使用LangGraph管理复杂的处理流程，提高系统稳定性
4. **分块处理策略**：智能分块处理大型文档，有效避免内存溢出问题
5. **多级错误处理**：实现完善的错误处理和回退机制，确保处理过程的稳定性

## 使用建议

1. **选择合适的模型**：
   - 对于一般用途，gpt-3.5-turbo提供了良好的性能/成本比
   - 对于需要更高质量分析的专业书籍，推荐使用gpt-4或更高级模型

2. **处理大型书籍**：
   - 对于超过500页的大型书籍，建议先分章节处理
   - 可以使用`--chunk-size`参数调整分块大小，平衡处理速度和内存使用

3. **自定义分析深度**：
   - 使用`--analysis-depth`参数调整分析深度（默认为"medium"）
   - 可选值："light"（快速但简略）、"medium"（平衡）、"deep"（详细但耗时）

## 测试

项目包含完整的测试套件，可以通过以下命令运行：

```bash
python test/test_all.py
```

测试将验证所有核心功能，包括文件转换、章节分割、内容清理和内容分析。

## 贡献指南

欢迎贡献代码、报告问题或提出改进建议！请遵循以下步骤：

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启一个 Pull Request

## 许可证

本项目采用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。

