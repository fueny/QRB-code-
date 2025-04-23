#!/bin/bash
# 安装脚本 - 自动设置读书项目环境

echo "===== 读书项目安装脚本 ====="
echo "此脚本将安装所有必要的依赖并设置项目环境"
echo

# 检查Python版本
if command -v python3.12 &>/dev/null; then
    echo "✓ Python 3.12 已安装"
    PYTHON_CMD=python3.12
else
    echo "! Python 3.12 未找到，尝试使用 python3"
    if command -v python3 &>/dev/null; then
        PYTHON_CMD=python3
        PY_VERSION=$(python3 --version)
        echo "  使用 $PY_VERSION"
    else
        echo "✗ 未找到 Python 3，请安装 Python 3.12 或更高版本"
        exit 1
    fi
fi

# 创建虚拟环境
echo
echo "正在创建虚拟环境..."
$PYTHON_CMD -m venv venv
if [ $? -ne 0 ]; then
    echo "✗ 创建虚拟环境失败"
    exit 1
fi
echo "✓ 虚拟环境创建成功"

# 激活虚拟环境
echo
echo "正在激活虚拟环境..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "✗ 激活虚拟环境失败"
    exit 1
fi
echo "✓ 虚拟环境已激活"

# 安装依赖
echo
echo "正在安装依赖..."
pip install langchain langchain-openai langgraph python-dotenv pypdf ebooklib beautifulsoup4 markdown faiss-cpu sentence-transformers chromadb pdfplumber
if [ $? -ne 0 ]; then
    echo "✗ 安装依赖失败"
    exit 1
fi
echo "✓ 依赖安装成功"

# 检查OpenAI API密钥
echo
if [ ! -f .env ]; then
    echo "创建 .env 文件..."
    echo "OPENAI_API_KEY=your-api-key-here" > .env
    echo "✓ .env 文件已创建，请编辑此文件并添加您的 OpenAI API 密钥"
else
    echo "✓ .env 文件已存在"
fi

# 创建输出目录
echo
echo "创建输出目录..."
mkdir -p output/converted output/chapters output/cleaned output/summary
echo "✓ 输出目录已创建"

echo
echo "===== 安装完成 ====="
echo "要使用读书项目，请执行以下步骤："
echo "1. 编辑 .env 文件并添加您的 OpenAI API 密钥"
echo "2. 激活虚拟环境: source venv/bin/activate"
echo "3. 运行主程序: python main.py 您的书籍文件路径"
echo "或运行演示: python demo.py 您的书籍文件路径"
echo
echo "详细说明请参阅 README.md 文件"
echo "===== 祝您使用愉快 ====="
