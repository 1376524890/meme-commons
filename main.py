"""
meme-commons 主启动文件
"""
import asyncio
import logging
import signal
import sys
from typing import Optional

from aiohttp import web

from meme_commons.config import settings
from meme_commons.server.mcp_server import mcp_server
from meme_commons.database.models import init_database
from meme_commons.vector_store import vector_store
from meme_commons.tools.crawler import crawler
from meme_commons.tools.embedding import embedding_tool
from meme_commons.tools.query import query_tool
from meme_commons.tools.summarizer import meme_summarizer
from meme_commons.tools.trend_analysis import trend_analysis_tool
from meme_commons.orchestrator import orchestrator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MemeCommonsSystem:
    """meme-commons系统主控制器"""
    
    def __init__(self):
        self.runner: Optional[web.AppRunner] = None
        self.is_running = False
    
    async def initialize(self):
        """初始化系统"""
        try:
            logger.info("Initializing meme-commons system...")
            
            # 1. 初始化数据库
            logger.info("Initializing database...")
            init_database(settings.DATABASE_URL)
            
            # 2. 初始化向量存储
            logger.info("Initializing vector store...")
            # vector_store.initialize() # 向量存储可能不需要异步初始化
            
            # 3. 初始化各个工具
            logger.info("Initializing tools...")
            
            # 爬虫工具
            # crawler.initialize() # 爬虫可能不需要异步初始化
            
            # 嵌入工具
            # embedding_tool.initialize() # 嵌入工具可能不需要异步初始化
            
            # 查询工具
            # query_tool.initialize() # 查询工具可能不需要异步初始化
            
            # 总结工具
            # meme_summarizer.initialize() # 总结工具可能不需要异步初始化
            
            # 趋势分析工具
            # trend_analysis_tool.initialize() # 趋势分析可能不需要异步初始化
            
            # 4. 初始化LLM协调器
            logger.info("Initializing LLM orchestrator...")
            
            # 5. 启动MCP服务器
            logger.info("Starting MCP server...")
            self.runner = await mcp_server.start_server()
            
            self.is_running = True
            logger.info("meme-commons system initialized successfully!")
            
        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            raise
    
    async def shutdown(self):
        """关闭系统"""
        try:
            logger.info("Shutting down meme-commons system...")
            
            self.is_running = False
            
            # 关闭MCP服务器
            if self.runner:
                await mcp_server.stop_server(self.runner)
                self.runner = None
            
            # 清理资源
            logger.info("Cleaning up resources...")
            
            # 可以添加其他清理逻辑
            logger.info("System shutdown completed")
            
        except Exception as e:
            logger.error(f"System shutdown error: {e}")
    
    async def run(self):
        """运行系统"""
        try:
            await self.initialize()
            
            # 设置信号处理
            for sig in [signal.SIGINT, signal.SIGTERM]:
                signal.signal(sig, self._signal_handler)
            
            logger.info("System is running. Press Ctrl+C to stop.")
            
            # 保持运行
            while self.is_running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"System error: {e}")
        finally:
            await self.shutdown()
    
    def _signal_handler(self, signum, frame):
        """处理系统信号"""
        logger.info(f"Received signal {signum}")
        self.is_running = False

async def main():
    """主函数"""
    system = MemeCommonsSystem()
    await system.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program interrupted by user")
    except Exception as e:
        logger.error(f"Program error: {e}")
        sys.exit(1)