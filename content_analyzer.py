#!/usr/bin/env python3
"""
内容分析系统 - 使用langchain、langgraph、向量数据库和RAG技术分析Markdown文档
功能：生成章节总结，提取重点内容，标记值得阅读的部分
"""

import os
import sys
import argparse
from pathlib import Path
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
import re

# LangChain和LangGraph
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.runnables import RunnablePassthrough
from langchain_community.vectorstores import FAISS
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
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
logger = logging.getLogger('content_analyzer')

class ContentAnalyzer:
    """使用LangChain、LangGraph和向量数据库分析Markdown内容的类"""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        """
        初始化内容分析器
        
        Args:
            model_name: 使用的OpenAI模型名称
        """
        self.model_name = model_name
        self.llm = ChatOpenAI(model=model_name, temperature=0.2)
        self.embeddings = OpenAIEmbeddings()
        logger.info(f"初始化内容分析器，使用模型: {model_name}")
        
        # 创建文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n## ", "\n### ", "\n#### ", "\n\n", "\n", " ", ""]
        )
    
    def _create_vector_store(self, texts: List[str]) -> FAISS:
        """
        创建向量存储
        
        Args:
            texts: 文本列表
            
        Returns:
            FAISS: 向量存储
        """
        # 分割文本
        docs = []
        for i, text in enumerate(texts):
            chunks = self.text_splitter.split_text(text)
            for j, chunk in enumerate(chunks):
                docs.append(Document(
                    page_content=chunk,
                    metadata={"source": f"doc_{i}", "chunk": j}
                ))
        
        # 创建向量存储
        vector_store = FAISS.from_documents(docs, self.embeddings)
        logger.info(f"创建了包含 {len(docs)} 个文档块的向量存储")
        
        return vector_store
    
    def _create_rag_chain(self, vector_store: FAISS, prompt_template: str) -> Any:
        """
        创建RAG链
        
        Args:
            vector_store: 向量存储
            prompt_template: 提示模板
            
        Returns:
            Any: RAG链
        """
        # 创建检索器
        retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5}
        )
        
        # 创建提示模板
        prompt = ChatPromptTemplate.from_template(prompt_template)
        
        # 创建文档链
        document_chain = create_stuff_documents_chain(self.llm, prompt)
        
        # 创建检索链
        rag_chain = create_retrieval_chain(retriever, document_chain)
        
        return rag_chain
    
    def generate_chapter_summary(self, chapter_text: str) -> str:
        """
        生成章节总结
        
        Args:
            chapter_text: 章节文本
            
        Returns:
            str: 章节总结
        """
        logger.info("开始生成章节总结")
        
        # 创建总结提示
        summary_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的文本分析助手，负责生成高质量的章节总结。请执行以下任务：
1. 仔细阅读提供的章节内容
2. 提供一个全面但简洁的总结，捕捉章节的主要观点、论点和结论
3. 总结应该是客观的，不添加个人观点
4. 总结长度应为原文的10-15%
5. 使用清晰、流畅的语言
6. 保持原文的专业术语和关键概念

请直接返回总结内容，不要添加标题或额外的格式。"""),
            ("user", "请为以下章节内容生成总结：\n\n{text}")
        ])
        
        # 创建总结链
        summary_chain = summary_prompt | self.llm | StrOutputParser()
        
        # 执行总结
        try:
            summary = summary_chain.invoke({"text": chapter_text})
            logger.info("章节总结生成完成")
            return summary
        except Exception as e:
            logger.error(f"生成章节总结时出错: {e}")
            return "无法生成章节总结。"
    
    def extract_key_points(self, chapter_text: str) -> List[str]:
        """
        提取章节重点内容
        
        Args:
            chapter_text: 章节文本
            
        Returns:
            List[str]: 重点内容列表
        """
        logger.info("开始提取章节重点内容")
        
        # 创建重点提取提示
        key_points_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的文本分析助手，负责提取章节中的重点内容。请执行以下任务：
1. 仔细阅读提供的章节内容
2. 识别并提取5-10个关键点或重要概念
3. 每个关键点应该是完整的句子或段落
4. 关键点应该代表章节中最重要的信息、论点或见解
5. 按重要性排序，最重要的放在前面
6. 尽量使用原文的表述，但可以适当精简

请以JSON格式返回结果，格式为：
```json
{
  "key_points": [
    "第一个关键点",
    "第二个关键点",
    "更多关键点..."
  ]
}
```"""),
            ("user", "请提取以下章节内容的重点：\n\n{text}")
        ])
        
        # 创建JSON解析器
        class KeyPointsParser(JsonOutputParser):
            def parse(self, text):
                try:
                    # 尝试解析JSON
                    return super().parse(text)
                except Exception:
                    # 如果解析失败，尝试提取JSON部分
                    json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
                    if json_match:
                        try:
                            return super().parse(json_match.group(1))
                        except:
                            pass
                    
                    # 如果仍然失败，尝试从文本中提取列表
                    points = []
                    for line in text.split('\n'):
                        line = line.strip()
                        if line and (line.startswith('- ') or line.startswith('* ') or re.match(r'^\d+\.', line)):
                            points.append(line.lstrip('- *0123456789. '))
                    
                    if points:
                        return {"key_points": points}
                    
                    # 最后的后备方案
                    return {"key_points": ["无法提取重点内容"]}
        
        # 创建重点提取链
        key_points_chain = key_points_prompt | self.llm | KeyPointsParser()
        
        # 执行重点提取
        try:
            result = key_points_chain.invoke({"text": chapter_text})
            key_points = result.get("key_points", [])
            logger.info(f"提取了 {len(key_points)} 个重点内容")
            return key_points
        except Exception as e:
            logger.error(f"提取章节重点内容时出错: {e}")
            return ["无法提取重点内容"]
    
    def identify_notable_sections(self, chapter_text: str) -> List[Dict[str, Any]]:
        """
        标记值得阅读的部分
        
        Args:
            chapter_text: 章节文本
            
        Returns:
            List[Dict[str, Any]]: 值得阅读的部分列表，每项包含 {'content': 内容, 'reason': 原因}
        """
        logger.info("开始标记值得阅读的部分")
        
        # 创建向量存储
        vector_store = self._create_vector_store([chapter_text])
        
        # 创建RAG提示
        notable_sections_prompt = """你是一个专业的文本分析助手，负责标记值得阅读的部分。
请基于以下上下文和检索到的内容，识别最值得阅读的3-5个段落或部分。

上下文信息:
{context}

请考虑以下因素：
1. 包含关键见解或重要概念的段落
2. 包含独特观点或创新思想的部分
3. 包含实用建议或可操作信息的部分
4. 包含引人深思的问题或挑战的部分
5. 包含精彩表述或生动例子的部分

请以JSON格式返回结果，格式为：
```json
{
  "notable_sections": [
    {
      "content": "第一个值得阅读的部分的完整内容",
      "reason": "为什么这部分值得阅读的简短解释"
    },
    {
      "content": "第二个值得阅读的部分...",
      "reason": "原因..."
    }
  ]
}
```

请确保返回的是有效的JSON格式。"""
        
        # 创建RAG链
        rag_chain = self._create_rag_chain(vector_store, notable_sections_prompt)
        
        # 创建JSON解析器
        class NotableSectionsParser(JsonOutputParser):
            def parse(self, text):
                try:
                    # 尝试解析JSON
                    return super().parse(text)
                except Exception:
                    # 如果解析失败，尝试提取JSON部分
                    json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
                    if json_match:
                        try:
                            return super().parse(json_match.group(1))
                        except:
                            pass
                    
                    # 如果仍然失败，返回空列表
                    return {"notable_sections": []}
        
        # 执行RAG查询
        try:
            result = rag_chain.invoke({"query": "识别值得阅读的部分"})
            
            # 解析结果
            parser = NotableSectionsParser()
            parsed_result = parser.parse(result["answer"])
            
            notable_sections = parsed_result.get("notable_sections", [])
            logger.info(f"标记了 {len(notable_sections)} 个值得阅读的部分")
            return notable_sections
        except Exception as e:
            logger.error(f"标记值得阅读的部分时出错: {e}")
            return []
    
    def analyze_chapter(self, chapter_file: str) -> Dict[str, Any]:
        """
        分析章节文件
        
        Args:
            chapter_file: 章节文件路径
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        logger.info(f"开始分析章节文件: {chapter_file}")
        
        # 读取章节内容
        try:
            with open(chapter_file, 'r', encoding='utf-8') as f:
                chapter_text = f.read()
        except Exception as e:
            logger.error(f"读取章节文件失败: {e}")
            raise
        
        # 提取章节标题
        title = "未知章节"
        title_match = re.search(r'^#\s+(.+)$', chapter_text, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip()
        
        # 生成章节总结
        summary = self.generate_chapter_summary(chapter_text)
        
        # 提取重点内容
        key_points = self.extract_key_points(chapter_text)
        
        # 标记值得阅读的部分
        notable_sections = self.identify_notable_sections(chapter_text)
        
        # 组合分析结果
        analysis = {
            "title": title,
            "file": chapter_file,
            "summary": summary,
            "key_points": key_points,
            "notable_sections": notable_sections
        }
        
        logger.info(f"章节 '{title}' 分析完成")
        return analysis
    
    def analyze_directory(self, input_dir: str) -> List[Dict[str, Any]]:
        """
        分析目录中的所有章节文件
        
        Args:
            input_dir: 输入目录
            
        Returns:
            List[Dict[str, Any]]: 所有章节的分析结果
        """
        logger.info(f"开始分析目录: {input_dir}")
        
        # 获取所有Markdown文件
        chapter_files = sorted(list(Path(input_dir).glob('*.md')))
        analyses = []
        
        # 分析每个章节
        for chapter_file in chapter_files:
            try:
                analysis = self.analyze_chapter(str(chapter_file))
                analyses.append(analysis)
                logger.info(f"成功分析章节: {chapter_file.name}")
            except Exception as e:
                logger.error(f"分析章节失败: {chapter_file.name}, 错误: {e}")
        
        return analyses
    
    def generate_summary_document(self, analyses: List[Dict[str, Any]], output_file: str) -> str:
        """
        生成总结文档
        
        Args:
            analyses: 所有章节的分析结果
            output_file: 输出文件路径
            
        Returns:
            str: 输出文件路径
        """
        logger.info(f"开始生成总结文档: {output_file}")
        
        # 创建总结文档内容
        content = []
        
        # 添加标题
        content.append("# 书籍总结\n")
        
        # 添加总体概述
        if analyses:
            # 创建总体概述提示
            overview_prompt = ChatPromptTemplate.from_messages([
                ("system", """你是一个专业的文本分析助手，负责生成书籍的总体概述。
请基于提供的所有章节总结，生成一个全面的书籍概述。概述应该：
1. 捕捉书籍的主要主题和核心信息
2. 概括书籍的整体结构和逻辑流程
3. 突出书籍的主要论点和结论
4. 使用清晰、专业的语言
5. 长度约为500-800字

请直接返回概述内容，不要添加标题或额外的格式。"""),
                ("user", "以下是书籍各章节的总结，请生成一个全面的书籍概述：\n\n{summaries}")
            ])
            
            # 创建总体概述链
            overview_chain = overview_prompt | self.llm | StrOutputParser()
            
            # 准备章节总结
            chapter_summaries = []
            for analysis in analyses:
                chapter_summaries.append(f"章节: {analysis['title']}\n{analysis['summary']}\n")
            
            # 执行总体概述生成
            try:
                overview = overview_chain.invoke({"summaries": "\n\n".join(chapter_summaries)})
                content.append("## 总体概述\n")
                content.append(overview)
                content.append("\n")
            except Exception as e:
                logger.error(f"生成总体概述时出错: {e}")
                content.append("## 总体概述\n")
                content.append("无法生成总体概述。\n")
        
        # 添加每个章节的分析
        for analysis in analyses:
            content.append(f"## {analysis['title']}\n")
            
            # 添加章节总结
            content.append("### 章节总结\n")
            content.append(analysis['summary'])
            content.append("\n")
            
            # 添加重点内容
            content.append("### 重点内容\n")
            for point in analysis['key_points']:
                content.append(f"- {point}\n")
            content.append("\n")
            
            # 添加值得阅读的部分
            content.append("### 值得阅读的部分\n")
            for section in analysis['notable_sections']:
                content.append(f"#### {section.get('reason', '值得阅读的部分')}\n")
                content.append(f"{section.get('content', '')}\n\n")
            content.append("\n")
        
        # 写入输出文件
        try:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(content))
            logger.info(f"总结文档已保存到: {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"写入输出文件失败: {e}")
            raise

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='分析Markdown章节并生成总结')
    parser.add_argument('--input-dir', '-i', required=True, help='输入目录，包含章节文件')
    parser.add_argument('--output-file', '-o', default='output/summary/sum.md', help='输出总结文件路径')
    parser.add_argument('--model', '-m', default="gpt-3.5-turbo", help='使用的OpenAI模型名称')
    args = parser.parse_args()
    
    try:
        # 创建内容分析器
        analyzer = ContentAnalyzer(args.model)
        
        # 分析章节
        analyses = analyzer.analyze_directory(args.input_dir)
        
        if analyses:
            # 生成总结文档
            output_file = analyzer.generate_summary_document(analyses, args.output_file)
            print(f"分析完成，总结文档已保存到: {output_file}")
        else:
            logger.error(f"没有找到可分析的章节文件: {args.input_dir}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"分析失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
