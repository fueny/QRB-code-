# 读书项目环境设置指南

## 环境要求

- Python 3.12+
- 足够的磁盘空间（处理大型书籍时需要）
- OpenAI API密钥（用于内容分析）

## 安装步骤

### Windows系统

1. 运行 `setup.bat` 脚本自动设置环境：
   ```
   .\setup.bat
   ```

   此脚本将：
   - 创建虚拟环境
   - 安装所有必要的依赖
   - 创建 `.env` 文件（如果不存在）

2. 编辑 `.env` 文件，添加您的 OpenAI API 密钥：
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

3. 激活虚拟环境：
   ```
   .\venv\Scripts\activate
   ```

### Linux/Mac系统

1. 运行 `install.sh` 脚本自动设置环境：
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

   此脚本将：
   - 创建虚拟环境
   - 安装所有必要的依赖
   - 创建 `.env` 文件（如果不存在）

2. 编辑 `.env` 文件，添加您的 OpenAI API 密钥：
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

3. 激活虚拟环境：
   ```bash
   source venv/bin/activate
   ```

### 手动安装

如果自动脚本不起作用，您可以按照以下步骤手动设置环境：

1. 创建虚拟环境：
   ```
   python -m venv venv
   ```

2. 激活虚拟环境：
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

3. 安装依赖：
   ```
   pip install -r requirements.txt
   ```

4. 创建 `.env` 文件并添加您的 OpenAI API 密钥：
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

## 使用方法

激活虚拟环境后，您可以使用以下命令运行项目：

```
python main.py 你的书籍文件路径 --output-dir output --model gpt-3.5-turbo
```

参数说明：
- `你的书籍文件路径`：要处理的书籍文件（PDF、EPUB等）
- `--output-dir`：输出目录，默认为"output"
- `--model`：使用的OpenAI模型，默认为"gpt-3.5-turbo"

## 故障排除

如果遇到问题：

1. 确保您已正确安装Python 3.12或更高版本
2. 确保您的OpenAI API密钥有效且已正确设置
3. 检查虚拟环境是否已激活
4. 尝试重新安装依赖：`pip install -r requirements.txt`

如需更多帮助，请参阅项目文档或联系开发者。
