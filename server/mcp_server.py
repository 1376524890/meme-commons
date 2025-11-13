"""
meme-commons MCP服务器 - 对外提供API接口
"""
import logging
import asyncio
import json
from typing import Dict, Any, Optional
from datetime import datetime

from aiohttp import web, ClientSession
from aiohttp.web_request import Request
from aiohttp.web_response import Response
import aiohttp_cors

from meme_commons.config import settings
from meme_commons.orchestrator import orchestrator
from meme_commons.database.models import get_db_session

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPServer:
    """MCP服务器 - 对外提供API接口"""
    
    def __init__(self):
        self.app = web.Application(client_max_size=100*1024*1024)  # 100MB
        self.setup_routes()
        self.setup_cors()
        self.orchestrator = orchestrator
    
    def setup_routes(self):
        """设置API路由"""
        
        # 健康检查
        self.app.router.add_get('/health', self.health_check)
        
        # 梗知识查询 (文档中提到的接口)
        self.app.router.add_get('/mcp/knowledge', self.get_knowledge)
        
        # 搜索接口
        self.app.router.add_post('/mcp/search', self.search_meme)
        
        # 趋势分析接口
        self.app.router.add_get('/mcp/trending', self.get_trending)
        self.app.router.add_post('/mcp/trend/analyze', self.analyze_trend)
        
        # 内容总结接口
        self.app.router.add_post('/mcp/summarize', self.summarize_content)
        
        # 爬取接口
        self.app.router.add_post('/mcp/crawl', self.crawl_platform)
        
        # 梗详细信息接口
        self.app.router.add_get('/mcp/meme/{meme_id}', self.get_meme_info)
        
        # 比较接口
        self.app.router.add_post('/mcp/compare', self.compare_memes)
        
        # 分类接口
        self.app.router.add_get('/mcp/categories', self.get_categories)
        
        # 演进分析接口
        self.app.router.add_get('/mcp/evolution/{meme_id}', self.get_evolution)
        
        # 系统状态接口
        self.app.router.add_get('/mcp/status', self.get_system_status)
        
        # 通用查询接口
        self.app.router.add_post('/mcp/query', self.handle_general_query)
    
    def setup_cors(self):
        """设置CORS支持"""
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        # 为所有路由添加CORS
        for route in list(self.app.router.routes()):
            cors.add(route)
    
    async def health_check(self, request: Request) -> Response:
        """健康检查接口"""
        try:
            # 检查数据库连接
            session = get_db_session()
            session.execute("SELECT 1")
            session.close()
            
            db_status = "ok"
        except Exception as e:
            db_status = f"error: {str(e)}"
        
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": db_status,
            "version": "1.0.0"
        }
        
        return web.json_response(health_data)
    
    async def get_knowledge(self, request: Request) -> Response:
        """梗知识查询接口 - 符合项目文档要求"""
        try:
            # 解析查询参数
            query = request.query.get('q', '')
            
            if not query:
                return web.json_response({
                    "error": "Missing query parameter 'q'",
                    "usage": "/mcp/knowledge?q=your_query"
                }, status=400)
            
            # 直接从数据库查询梗知识卡
            session = get_db_session()
            try:
                from meme_commons.database.models import MemeCard
                from sqlalchemy import or_
                
                # 搜索梗知识卡
                meme_cards = session.query(MemeCard).filter(
                    or_(
                        MemeCard.title.contains(query),
                        MemeCard.origin.contains(query),
                        MemeCard.meaning.contains(query)
                    )
                ).order_by(MemeCard.trend_score.desc()).limit(1).all()
                
                if meme_cards:
                    meme_card = meme_cards[0]
                    # 返回符合文档格式的结构化知识卡
                    response = meme_card.to_dict()
                else:
                    # 如果没有找到匹配的梗，返回空的结构化知识卡
                    response = {
                        "title": query,
                        "origin": "",
                        "meaning": "",
                        "examples": [],
                        "trend_score": 0.0,
                        "last_updated": datetime.now().isoformat()
                    }
                
                return web.json_response(response)
                
            finally:
                session.close()
            
        except Exception as e:
            logger.error(f"Knowledge query failed: {e}")
            return web.json_response({
                "error": str(e),
                "query": request.query.get('q', '')
            }, status=500)
    
    async def search_meme(self, request: Request) -> Response:
        """梗搜索接口"""
        try:
            data = await request.json()
            
            query = data.get('query', '')
            limit = data.get('limit', 10)
            
            if not query:
                return web.json_response({
                    "error": "Missing required field: query"
                }, status=400)
            
            orchestrator_request = {
                "type": "search_meme",
                "query": query,
                "limit": limit,
                "request_id": f"search_{datetime.now().timestamp()}"
            }
            
            result = await self.orchestrator.process_request(orchestrator_request)
            return web.json_response(result)
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def get_trending(self, request: Request) -> Response:
        """获取热门梗接口"""
        try:
            time_window = request.query.get('time_window', '24h')
            limit = int(request.query.get('limit', '20'))
            
            orchestrator_request = {
                "type": "get_trending",
                "time_window": time_window,
                "limit": limit,
                "request_id": f"trending_{datetime.now().timestamp()}"
            }
            
            result = await self.orchestrator.process_request(orchestrator_request)
            return web.json_response(result)
            
        except Exception as e:
            logger.error(f"Get trending failed: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def analyze_trend(self, request: Request) -> Response:
        """分析趋势接口"""
        try:
            data = await request.json()
            
            meme_id = data.get('meme_id')
            time_window = data.get('time_window', '7d')
            
            if not meme_id:
                return web.json_response({
                    "error": "Missing required field: meme_id"
                }, status=400)
            
            orchestrator_request = {
                "type": "analyze_trend",
                "meme_id": meme_id,
                "time_window": time_window,
                "request_id": f"trend_{datetime.now().timestamp()}"
            }
            
            result = await self.orchestrator.process_request(orchestrator_request)
            return web.json_response(result)
            
        except Exception as e:
            logger.error(f"Trend analysis failed: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def summarize_content(self, request: Request) -> Response:
        """内容总结接口"""
        try:
            data = await request.json()
            
            content = data.get('content')
            posts = data.get('posts')
            
            if not content and not posts:
                return web.json_response({
                    "error": "Provide either 'content' or 'posts' for summarization"
                }, status=400)
            
            orchestrator_request = {
                "type": "summarize_content",
                "content": content,
                "posts": posts,
                "request_id": f"summary_{datetime.now().timestamp()}"
            }
            
            result = await self.orchestrator.process_request(orchestrator_request)
            return web.json_response(result)
            
        except Exception as e:
            logger.error(f"Content summarization failed: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def crawl_platform(self, request: Request) -> Response:
        """平台爬取接口"""
        try:
            data = await request.json()
            
            platforms = data.get('platforms', ['reddit'])
            keywords = data.get('keywords', [])
            limit = data.get('limit', 100)
            
            if not keywords:
                return web.json_response({
                    "error": "Missing required field: keywords"
                }, status=400)
            
            orchestrator_request = {
                "type": "crawl_platform",
                "platforms": platforms,
                "keywords": keywords,
                "limit": limit,
                "request_id": f"crawl_{datetime.now().timestamp()}"
            }
            
            result = await self.orchestrator.process_request(orchestrator_request)
            return web.json_response(result)
            
        except Exception as e:
            logger.error(f"Platform crawling failed: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def get_meme_info(self, request: Request) -> Response:
        """获取梗详细信息接口"""
        try:
            meme_id = request.match_info['meme_id']
            
            orchestrator_request = {
                "type": "get_meme_info",
                "meme_id": meme_id,
                "request_id": f"info_{datetime.now().timestamp()}"
            }
            
            result = await self.orchestrator.process_request(orchestrator_request)
            return web.json_response(result)
            
        except Exception as e:
            logger.error(f"Get meme info failed: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def compare_memes(self, request: Request) -> Response:
        """比较梗接口"""
        try:
            data = await request.json()
            
            meme_ids = data.get('meme_ids', [])
            
            if len(meme_ids) < 2:
                return web.json_response({
                    "error": "Need at least 2 meme IDs for comparison"
                }, status=400)
            
            orchestrator_request = {
                "type": "compare_memes",
                "meme_ids": meme_ids,
                "request_id": f"compare_{datetime.now().timestamp()}"
            }
            
            result = await self.orchestrator.process_request(orchestrator_request)
            return web.json_response(result)
            
        except Exception as e:
            logger.error(f"Meme comparison failed: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def get_categories(self, request: Request) -> Response:
        """获取分类接口"""
        try:
            time_window = request.query.get('time_window', '7d')
            
            orchestrator_request = {
                "type": "get_categories",
                "time_window": time_window,
                "request_id": f"categories_{datetime.now().timestamp()}"
            }
            
            result = await self.orchestrator.process_request(orchestrator_request)
            return web.json_response(result)
            
        except Exception as e:
            logger.error(f"Get categories failed: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def get_evolution(self, request: Request) -> Response:
        """获取梗演进信息接口"""
        try:
            meme_id = request.match_info['meme_id']
            
            orchestrator_request = {
                "type": "get_evolution",
                "meme_id": meme_id,
                "request_id": f"evolution_{datetime.now().timestamp()}"
            }
            
            result = await self.orchestrator.process_request(orchestrator_request)
            return web.json_response(result)
            
        except Exception as e:
            logger.error(f"Get evolution failed: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def get_system_status(self, request: Request) -> Response:
        """获取系统状态接口"""
        try:
            status = self.orchestrator.get_system_status()
            return web.json_response({
                "success": True,
                "status": status,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Get system status failed: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def handle_general_query(self, request: Request) -> Response:
        """处理通用查询接口"""
        try:
            data = await request.json()
            
            query = data.get('query', '')
            text = data.get('text', '')
            content = data.get('content', '')
            
            if not any([query, text, content]):
                return web.json_response({
                    "error": "Provide at least one of: query, text, or content"
                }, status=400)
            
            orchestrator_request = {
                "type": "general_inquiry",
                "query": query,
                "text": text,
                "content": content,
                "request_id": f"query_{datetime.now().timestamp()}"
            }
            
            result = await self.orchestrator.process_request(orchestrator_request)
            return web.json_response(result)
            
        except Exception as e:
            logger.error(f"General query failed: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def start_server(self, host: str = None, port: int = None):
        """启动MCP服务器"""
        host = host or settings.MCP_HOST
        port = port or settings.MCP_PORT
        
        logger.info(f"Starting MCP Server on {host}:{port}")
        
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, host, port)
        await site.start()
        
        logger.info(f"MCP Server is running at http://{host}:{port}")
        logger.info(f"API Documentation:")
        logger.info(f"  GET  /health - Health check")
        logger.info(f"  GET  /mcp/knowledge?q=<query> - Search meme knowledge")
        logger.info(f"  POST /mcp/search - Search memes")
        logger.info(f"  GET  /mcp/trending - Get trending memes")
        logger.info(f"  POST /mcp/trend/analyze - Analyze trend")
        logger.info(f"  POST /mcp/summarize - Summarize content")
        logger.info(f"  POST /mcp/crawl - Crawl platforms")
        logger.info(f"  GET  /mcp/meme/<id> - Get meme info")
        logger.info(f"  POST /mcp/compare - Compare memes")
        logger.info(f"  GET  /mcp/categories - Get categories")
        logger.info(f"  GET  /mcp/evolution/<id> - Get evolution")
        logger.info(f"  GET  /mcp/status - System status")
        logger.info(f"  POST /mcp/query - General query")
        
        return runner
    
    async def stop_server(self, runner):
        """停止MCP服务器"""
        logger.info("Stopping MCP Server...")
        await runner.cleanup()
        logger.info("MCP Server stopped")

# 全局MCP服务器实例
mcp_server = MCPServer()