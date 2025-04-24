# 内容清理功能测试

本目录包含用于测试内容清理功能的脚本和示例文件。

## 文件说明

- `test_cleaner.py`: 测试单个文件的清理功能
- `test_full.py`: 测试整个清理流程
- `full_test/`: 完整测试的输出目录
  - `chapters/`: 原始章节文件
  - `cleaned/`: 清理后的章节文件

## 如何运行测试

### 测试单个文件的清理

```bash
python test_cleaner.py test_file.md
```

这将创建一个测试文件 `test/chapters/test_file.md`，然后清理它并将结果保存到 `test/cleaned/test_file.md`。

### 测试整个清理流程

```bash
python test_full.py <测试名称>
```

这将创建一个测试目录 `test/<测试名称>`，包含多个测试文件，然后清理它们并将结果保存到相应的目录中。

## 清理功能说明

内容清理功能可以修复以下问题：

1. 删除乱码字符和无意义的符号序列
2. 修复段落格式，确保适当的换行和分段
3. 修复Markdown语法错误，包括：
   - 确保标题符号#后有空格
   - 确保列表项符号-后有空格
   - 修复未闭合的强调标记*和_
4. 修复标点符号问题，如重复的标点符号
5. 修复句子之间缺少空格的问题

## 如何在实际项目中使用

在实际项目中，可以使用以下命令清理整个目录中的文件：

```bash
python content_cleaner.py --input <输入目录> --output <输出目录>
```

例如：

```bash
python content_cleaner.py --input output/chapters --output output/cleaned
```

这将清理 `output/chapters` 目录中的所有Markdown文件，并将结果保存到 `output/cleaned` 目录中。
