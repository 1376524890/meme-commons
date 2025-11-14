"""
meme-commons LLM协调器 - 协调各个工具的调用
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import json

from database.models import get_db_session
from tools.crawler import crawler
from tools.embedding import embedding_tool
from tools.query import query_tool
from tools.summarizer import meme_summarizer
from tools.trend_analysis import trend_analysis_tool

logger = logging.getLogger(__name__)

class LLMOrchestrator:
    """LLM协调器 - 系统的核心控制器"""
    
    def __init__(self):
        self.tools = {
            "crawler": crawler,
            "embedding": embedding_tool,
            "query": query_tool,
            "summarizer": meme_summarizer,
            "trend_analysis": trend_analysis_tool
        }
        
        self.request_handlers = {
            "search_meme": self._handle_search_meme,
            "get_trending": self._handle_get_trending,
            "analyze_trend": self._handle_analyze_trend,
            "summarize_content": self._handle_summarize_content,
            "crawl_platform": self._handle_crawl_platform,
            "get_meme_info": self._handle_get_meme_info,
            "compare_memes": self._handle_compare_memes,
            "get_categories": self._handle_get_categories,
            "get_evolution": self._handle_get_evolution,
            "general_inquiry": self._handle_general_inquiry
        }
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理用户请求的主要入口点"""
        try:
            # 记录请求
            logger.info(f"Processing request: {request.get('type', 'unknown')}")
            
            # 解析请求类型
            request_type = self._extract_request_type(request)
            
            if request_type not in self.request_handlers:
                return self._create_error_response(
                    f"Unsupported request type: {request_type}",
                    request_id=request.get("request_id")
                )
            
            # 调用相应的处理器
            handler = self.request_handlers[request_type]
            result = await handler(request)
            
            return self._create_success_response(result, request_id=request.get("request_id"))
            
        except Exception as e:
            logger.error(f"Failed to process request: {e}")
            return self._create_error_response(
                f"Internal error: {str(e)}",
                request_id=request.get("request_id")
            )
    
    def _extract_request_type(self, request: Dict[str, Any]) -> str:
        """从请求中提取请求类型"""
        # 优先级：明确的type > 基于query的推断 > 基于text的推断
        if "type" in request:
            return request["type"]
        
        query = request.get("query", "").lower()
        text = request.get("text", "").lower()
        content = request.get("content", "").lower()
        
        # 基于关键词推断请求类型
        if any(keyword in query or keyword in text or keyword in content 
               for keyword in ["热门", "趋势", "热度", "trending", "popular"]):
            return "get_trending"
        
        if any(keyword in query or keyword in text or keyword in content 
               for keyword in ["搜索", "查找", "search", "find"]):
            return "search_meme"
        
        if any(keyword in query or keyword in text or keyword in content 
               for keyword in ["总结", "summarize", "摘要"]):
            return "summarize_content"
        
        if any(keyword in query or keyword in text or keyword in content 
               for keyword in ["爬取", "抓取", "crawl"]):
            return "crawl_platform"
        
        if any(keyword in query or keyword in text or keyword in content 
               for keyword in ["分析", "趋势", "analysis", "trend"]):
            return "analyze_trend"
        
        return "general_inquiry"
    
    async def _handle_search_meme(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理梗搜索请求"""
        query = request.get("query", "")
        if not query:
            return {"error": "Missing search query"}
        
        # 执行知识库查询
        search_results = query_tool.query_knowledge(query, limit=request.get("limit", 10))
        
        return {
            "query": query,
            "search_results": search_results,
            "total_found": len(search_results)
        }
    
    async def _handle_get_trending(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取热门梗请求"""
        time_window = request.get("time_window", "24h")
        limit = request.get("limit", 20)
        
        trending_memes = trend_analysis_tool.get_trending_memes(limit=limit, time_window=time_window)
        
        return {
            "time_window": time_window,
            "trending_memes": trending_memes,
            "total_found": len(trending_memes),
            "generated_at": datetime.now().isoformat()
        }
    
    async def _handle_analyze_trend(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理趋势分析请求"""
        meme_id = request.get("meme_id")
        time_window = request.get("time_window", "7d")
        
        if not meme_id:
            return {"error": "Missing meme_id for trend analysis"}
        
        trend_data = trend_analysis_tool.analyze_trend(meme_id, time_window)
        
        if not trend_data:
            return {"error": f"No trend data found for meme {meme_id}"}
        
        # 获取梗演进数据
        evolution = trend_analysis_tool.analyze_meme_evolution(meme_id)
        
        return {
            "meme_id": meme_id,
            "trend_analysis": trend_data,
            "evolution": evolution
        }
    
    async def _handle_summarize_content(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理内容总结请求"""
        content = request.get("content", "")
        posts = request.get("posts", [])
        
        if not content and not posts:
            return {"error": "Missing content or posts for summarization"}
        
        if content:
            # 总结单个内容
            summary = meme_summarizer.summarize_content(content)
            return {"summary": summary}
        elif posts:
            # 总结多个帖子
            summaries = meme_summarizer.batch_summarize(posts)
            return {"summaries": summaries}
        
        return {"error": "No content to summarize"}
    
    async def _handle_crawl_platform(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理平台爬取请求"""
        platform = request.get("platform", "all")
        keywords = request.get("keywords", [])
        limit = request.get("limit", 100)
        
        if not keywords:
            return {"error": "Missing keywords for crawling"}
        
        # 执行爬取
        if platform.lower() == "all":
            crawl_results = crawler.crawl_all_platforms(limit=limit, keywords=keywords)
        else:
            crawl_results = crawler.crawl_source(platform, limit=limit, keywords=keywords)
        
        # 转换datetime对象为字符串，避免JSON序列化错误
        for post in crawl_results:
            if 'timestamp' in post and hasattr(post['timestamp'], 'isoformat'):
                post['timestamp'] = post['timestamp'].isoformat()
        
        return {
            "platform": platform,
            "keywords": keywords,
            "crawl_results": crawl_results,
            "total_posts": len(crawl_results)
        }
    
    async def _handle_get_meme_info(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取梗信息请求"""
        meme_id = request.get("meme_id")
        
        if not meme_id:
            return {"error": "Missing meme_id"}
        
        # 获取梗详细信息
        meme_info = query_tool.get_meme_details(meme_id)
        
        if not meme_info:
            return {"error": f"Meme {meme_id} not found"}
        
        # 获取相关原始帖子
        related_posts = query_tool.get_related_posts(meme_id, limit=10)
        
        # 获取趋势分析
        trend_data = trend_analysis_tool.analyze_trend(meme_id)
        
        return {
            "meme_info": meme_info,
            "related_posts": related_posts,
            "trend_analysis": trend_data
        }
    
    async def _handle_compare_memes(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理梗比较请求"""
        meme_ids = request.get("meme_ids", [])
        
        if len(meme_ids) < 2:
            return {"error": "Need at least 2 meme IDs for comparison"}
        
        comparisons = []
        
        for meme_id in meme_ids:
            # 获取每个梗的详细信息和趋势
            meme_info = query_tool.get_meme_details(meme_id)
            trend_data = trend_analysis_tool.analyze_trend(meme_id)
            
            comparisons.append({
                "meme_id": meme_id,
                "meme_info": meme_info,
                "trend_data": trend_data
            })
        
        return {
            "comparisons": comparisons,
            "comparison_count": len(comparisons)
        }
    
    async def _handle_get_categories(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取分类请求"""
        time_window = request.get("time_window", "7d")
        
        categories = query_tool.get_categories()
        trend_categories = trend_analysis_tool.get_trend_categories(time_window)
        
        return {
            "categories": categories,
            "trend_categories": trend_categories
        }
    
    async def _handle_get_evolution(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取演进信息请求"""
        meme_id = request.get("meme_id")
        
        if not meme_id:
            return {"error": "Missing meme_id for evolution analysis"}
        
        evolution_data = trend_analysis_tool.analyze_meme_evolution(meme_id)
        
        return {
            "meme_id": meme_id,
            "evolution_data": evolution_data
        }
    
    async def _handle_general_inquiry(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理通用查询请求"""
        query = request.get("query", "") + " " + request.get("text", "") + " " + request.get("content", "")
        
        if not query.strip():
            return {"error": "Empty query text"}
        
        # 首先尝试搜索梗知识
        search_results = query_tool.search_knowledge(query, limit=5)
        
        # 如果找到相关梗，返回信息
        if search_results:
            result = {
                "response_type": "knowledge_search",
                "query": query,
                "found_memes": search_results[:3],  # 返回前3个最相关的结果
                "message": "找到相关的梗知识信息"
            }
        else:
            # 如果没有找到梗知识，返回通用回复
            result = {
                "response_type": "general_response",
                "query": query,
                "message": "抱歉，我没有找到相关的信息。您可以尝试使用更具体的关键词，或者让我为您爬取最新内容。"
            }
        
        return result
    
    def _create_success_response(self, data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """创建成功响应"""
        return {
            "success": True,
            "data": data,
            "request_id": request_id,
            "timestamp": datetime.now().isoformat()
        }
    
    def _create_error_response(self, error_message: str, request_id: Optional[str] = None) -> Dict[str, Any]:
        """创建错误响应"""
        return {
            "success": False,
            "error": error_message,
            "request_id": request_id,
            "timestamp": datetime.now().isoformat()
        }
    
    async def execute_workflow(self, workflow_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """执行工作流程"""
        results = []
        current_data = {}
        
        try:
            for step in workflow_steps:
                step_name = step.get("step", "")
                tool_name = step.get("tool", "")
                params = step.get("params", {})
                
                # 如果步骤引用前一步的结果
                if "data_from_previous" in step:
                    data_key = step["data_from_previous"]
                    if data_key in current_data:
                        params.update(current_data[data_key])
                
                logger.info(f"Executing workflow step: {step_name} using {tool_name}")
                
                # 执行工具调用
                tool = self.tools.get(tool_name)
                if not tool:
                    raise ValueError(f"Tool {tool_name} not found")
                
                # 根据工具类型调用相应的方法
                if hasattr(tool, "execute"):
                    result = await tool.execute(**params)
                else:
                    # 对于同步工具，使用asyncio.run_in_executor
                    loop = asyncio.get_event_loop()
                    if hasattr(tool, "search_knowledge"):
                        result = await loop.run_in_executor(None, tool.search_knowledge, **params)
                    elif hasattr(tool, "get_trending_memes"):
                        result = await loop.run_in_executor(None, tool.get_trending_memes, **params)
                    else:
                        result = tool
                
                results.append({
                    "step": step_name,
                    "tool": tool_name,
                    "result": result
                })
                
                # 保存结果以便后续步骤使用
                current_data[step_name] = result
            
            return {
                "success": True,
                "workflow_results": results,
                "final_data": current_data
            }
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "completed_steps": results
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        status = {
            "orchestrator_status": "active",
            "available_tools": list(self.tools.keys()),
            "handlers_available": len(self.request_handlers),
            "timestamp": datetime.now().isoformat()
        }
        
        # 检查数据库连接
        try:
            session = get_db_session()
            # 执行简单查询测试连接
            session.execute("SELECT 1")
            status["database_status"] = "connected"
            session.close()
        except Exception as e:
            status["database_status"] = f"error: {str(e)}"
        
        return status

# 全局LLM协调器实例
orchestrator = LLMOrchestrator()