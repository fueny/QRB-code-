#!/usr/bin/env python3
"""
内容清理模块 - 使用langchain和langgraph审查和修复Markdown文档中的问题
功能：删除乱码，修复段落格式，确保内容正常可读
"""

import os
import sys
import argparse
from pathlib import Path
import logging
import re
from typing import List, Dict, Any, Optional, Tuple

# LangChain和LangGraph
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langgraph.graph import StateGraph, END
from langgraph.checkpoint import MemorySaver

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('content_cleaner')

class ContentCleaner:
    """使用LangChain和LangGraph清理Markdown内容的类"""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        """
        初始化内容清理器
        
        Args:
            model_name: 使用的OpenAI模型名称
        """
        self.model_name = model_name
        self.llm = ChatOpenAI(model=model_name, temperature=0)
        logger.info(f"初始化内容清理器，使用模型: {model_name}")
        
        # 创建文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=4000,
            chunk_overlap=200,
            separators=["\n## ", "\n### ", "\n#### ", "\n\n", "\n", " ", ""]
        )
    
    def _detect_garbled_text(self, text: str) -> bool:
        """
        检测文本中是否包含乱码
        
        Args:
            text: 输入文本
            
        Returns:
            bool: 是否包含乱码
        """
        # 检测常见的乱码模式
        patterns = [
            r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]',  # 控制字符
            r'�',  # 替换字符
            r'[\uFFFD\uFFFE\uFFFF]',  # Unicode替换字符
            r'[\u200B-\u200F\u2028-\u202E]',  # 零宽字符和方向控制字符
        ]
        
        for pattern in patterns:
            if re.search(pattern, text):
                return True
        
        # 检测不常见字符的密度
        unusual_chars = re.findall(r'[^\x00-\x7F\u4E00-\u9FFF\u3040-\u30FF\uAC00-\uD7AF]', text)
        if len(unusual_chars) > len(text) * 0.1:  # 如果不常见字符超过10%
            return True
        
        return False
    
    def _detect_formatting_issues(self, text: str) -> bool:
        """
        检测文本中是否存在格式问题
        
        Args:
            text: 输入文本
            
        Returns:
            bool: 是否存在格式问题
        """
        # 检测常见的格式问题
        issues = [
            # 检测连续的空行超过2个
            len(re.findall(r'\n\s*\n\s*\n', text)) > 0,
            
            # 检测没有适当分段的长文本
            len(re.findall(r'[.!?。！？][^\n]{100,}', text)) > 0,
            
            # 检测不完整的Markdown标记
            len(re.findall(r'\*[^\*\n]{1,100}$', text)) > 0 or len(re.findall(r'_[^_\n]{1,100}$', text)) > 0,
            
            # 检测错误的标题格式
            len(re.findall(r'(?<!\n)#{1,6}\s', text)) > 0,
            
            # 检测错误的列表格式
            len(re.findall(r'(?<!\n)-\s', text)) > 0,
        ]
        
        return any(issues)
    
    def _clean_chunk(self, chunk: str) -> str:
        """
        清理文本块
        
        Args:
            chunk: 输入文本块
            
        Returns:
            str: 清理后的文本块
        """
        # 检测是否需要清理
        needs_cleaning = (
            self._detect_garbled_text(chunk) or 
            self._detect_formatting_issues(chunk)
        )
        
        if not needs_cleaning:
            logger.info("文本块不需要清理")
            return chunk
        
        logger.info("检测到文本问题，开始清理")
        
        # 创建清理提示
        clean_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的文本清理助手，负责修复Markdown文档中的问题。请执行以下任务：
1. 删除所有乱码字符和无意义的符号序列
2. 修复段落格式，确保适当的换行和分段
3. 修复Markdown语法错误
4. 保留原始内容的意义和结构
5. 不要添加新内容或解释
6. 保留原始的标题结构和层级
7. 如果文本完全无法理解，用[内容无法恢复]替换

请直接返回清理后的文本，不要添加任何解释或评论。"""),
            ("user", "请清理以下Markdown文本：\n\n{text}")
        ])
        
        # 创建清理链
        clean_chain = clean_prompt | self.llm | StrOutputParser()
        
        # 执行清理
        try:
            cleaned_text = clean_chain.invoke({"text": chunk})
            logger.info("文本块清理完成")
            return cleaned_text
        except Exception as e:
            logger.error(f"清理文本块时出错: {e}")
            # 如果清理失败，尝试基本清理
            return self._basic_clean(chunk)
    
    def _basic_clean(self, text: str) -> str:
        """
        基本的文本清理（当LLM清理失败时使用）
        
        Args:
            text: 输入文本
            
        Returns:
            str: 基本清理后的文本
        """
        logger.info("执行基本文本清理")
        
        # 删除控制字符
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', text)
        
        # 替换Unicode替换字符
        text = re.sub(r'�|[\uFFFD\uFFFE\uFFFF]', '', text)
        
        # 修复连续空行
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # 确保标题前有空行
        text = re.sub(r'([^\n])(\n#{1,6}\s)', r'\1\n\2', text)
        
        # 确保列表项前有空行
        text = re.sub(r'([^\n])(\n-\s)', r'\1\n\2', text)
        
        return text
    
    def build_cleaning_graph(self) -> StateGraph:
        """
        构建内容清理工作流图
        
        Returns:
            StateGraph: LangGraph状态图
        """
        # 定义状态
        class State(dict):
            """工作流状态"""
            text: str
            chunks: List[str]
            cleaned_chunks: List[str]
            current_index: int
            
        # 节点函数
        def split_text(state: State) -> State:
            """将文本分割为块"""
            text = state["text"]
            chunks = self.text_splitter.split_text(text)
            return {
                **state,
                "chunks": chunks,
                "cleaned_chunks": [],
                "current_index": 0
            }
        
        def process_chunk(state: State) -> State:
            """处理当前块"""
            chunks = state["chunks"]
            current_index = state["current_index"]
            cleaned_chunks = state["cleaned_chunks"]
            
            if current_index >= len(chunks):
                return {**state}
            
            current_chunk = chunks[current_index]
            cleaned_chunk = self._clean_chunk(current_chunk)
            
            return {
                **state,
                "cleaned_chunks": cleaned_chunks + [cleaned_chunk],
                "current_index": current_index + 1
            }
        
        def check_completion(state: State) -> str:
            """检查是否完成所有块的处理"""
            if state["current_index"] >= len(state["chunks"]):
                return "complete"
            return "continue"
        
        def merge_chunks(state: State) -> State:
            """合并清理后的块"""
            cleaned_chunks = state["cleaned_chunks"]
            merged_text = "\n\n".join(cleaned_chunks)
            
            # 修复可能的合并问题
            # 修复标题之间的多余空行
            merged_text = re.sub(r'(#{1,6}\s.*?\n)\n+(?=#{1,6}\s)', r'\1\n', merged_text)
            
            # 确保段落之间只有一个空行
            merged_text = re.sub(r'\n{3,}', '\n\n', merged_text)
            
            return {
                **state,
                "result": merged_text
            }
        
        # 创建工作流图
        workflow = StateGraph(State)
        
        # 添加节点
        workflow.add_node("split_text", split_text)
        workflow.add_node("process_chunk", process_chunk)
        workflow.add_node("merge_chunks", merge_chunks)
        
        # 添加边
        workflow.set_entry_point("split_text")
        workflow.add_edge("split_text", "process_chunk")
        workflow.add_conditional_edges(
            "process_chunk",
            check_completion,
            {
                "continue": "process_chunk",
                "complete": "merge_chunks"
            }
        )
        workflow.add_edge("merge_chunks", END)
        
        return workflow.compile()
    
    def clean_text(self, text: str) -> str:
        """
        清理文本内容
        
        Args:
            text: 输入文本
            
        Returns:
            str: 清理后的文本
        """
        logger.info("开始清理文本内容")
        
        # 构建工作流图
        graph = self.build_cleaning_graph()
        
        # 创建内存保存器
        memory_saver = MemorySaver()
        
        # 执行工作流
        try:
            result = graph.invoke(
                {"text": text},
                config={"checkpointer": memory_saver}
            )
            logger.info("文本内容清理完成")
            return result["result"]
        except Exception as e:
            logger.error(f"清理文本内容时出错: {e}")
            # 如果工作流执行失败，尝试基本清理
            return self._basic_clean(text)
    
    def clean_file(self, input_file: str, output_file: str) -> str:
        """
        清理文件内容
        
        Args:
            input_file: 输入文件路径
            output_file: 输出文件路径
            
        Returns:
            str: 输出文件路径
        """
        logger.info(f"开始清理文件: {input_file}")
        
        # 读取文件内容
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            raise
        
        # 清理内容
        cleaned_content = self.clean_text(content)
        
        # 写入输出文件
        try:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            logger.info(f"清理后的内容已保存到: {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"写入输出文件失败: {e}")
            raise

def clean_directory(input_dir: str, output_dir: str, model_name: str = "gpt-3.5-turbo") -> List[str]:
    """
    清理目录中的所有Markdown文件
    
    Args:
        input_dir: 输入目录
        output_dir: 输出目录
        model_name: 使用的OpenAI模型名称
        
    Returns:
        List[str]: 清理后的文件路径列表
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 创建内容清理器
    cleaner = ContentCleaner(model_name)
    
    # 获取所有Markdown文件
    input_files = list(Path(input_dir).glob('*.md'))
    output_files = []
    
    # 清理每个文件
    for input_file in input_files:
        output_file = os.path.join(output_dir, input_file.name)
        try:
            cleaned_file = cleaner.clean_file(str(input_file), output_file)
            output_files.append(cleaned_file)
            logger.info(f"成功清理文件: {input_file.name}")
        except Exception as e:
            logger.error(f"清理文件失败: {input_file.name}, 错误: {e}")
    
    return output_files

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='清理Markdown文档中的问题')
    parser.add_argument('--input', '-i', required=True, help='输入文件或目录')
    parser.add_argument('--output', '-o', required=True, help='输出文件或目录')
    parser.add_argument('--model', '-m', default="gpt-3.5-turbo", help='使用的OpenAI模型名称')
    args = parser.parse_args()
    
    try:
        # 检查输入是文件还是目录
        input_path = Path(args.input)
        if input_path.is_file():
            # 清理单个文件
            cleaner = ContentCleaner(args.model)
            output_file = cleaner.clean_file(str(input_path), args.output)
            print(f"清理完成，输出文件: {output_file}")
        elif input_path.is_dir():
            # 清理目录中的所有文件
            output_files = clean_directory(str(input_path), args.output, args.model)
            print(f"清理完成，共处理 {len(output_files)} 个文件")
            for file in output_files:
                print(f"- {file}")
        else:
            logger.error(f"输入路径不存在: {args.input}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"清理失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
