"""
meme-commons 项目配置文件
"""
import os
from typing import Optional

class Config:
    """系统配置类"""
    
    # 数据库配置
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./meme_commons.db")
    
    # 向量数据库配置
    VECTOR_DB_URL: str = os.getenv("VECTOR_DB_URL", "http://localhost:19530")
    
    # Redis缓存配置
    CACHE_URL: str = os.getenv("CACHE_URL", "redis://localhost:6379/0")
    
    # Dashscope API配置
    DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")
    DASHSCOPE_EMBEDDING_MODEL: str = os.getenv("DASHSCOPE_EMBEDDING_MODEL", "text-embedding-v1")
    DASHSCOPE_LLM_MODEL: str = os.getenv("DASHSCOPE_LLM_MODEL", "qwen-plus")
    
    # MCP服务器配置
    MCP_HOST: str = os.getenv("MCP_HOST", "0.0.0.0")
    MCP_PORT: int = int(os.getenv("MCP_PORT", "8002"))
    
    # 爬虫配置
    # 斗音配置
    DOUYIN_USER_AGENT: str = os.getenv("DOUYIN_USER_AGENT", "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36")
    DOUYIN_DELAY: float = float(os.getenv("DOUYIN_DELAY", "3.0"))
    
    # 百度贴吧配置
    TIEBA_USER_AGENT: str = os.getenv("TIEBA_USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    TIEBA_DELAY: float = float(os.getenv("TIEBA_DELAY", "1.0"))
    
    # 小红书配置  
    XIAOHONGSHU_USER_AGENT: str = os.getenv("XIAOHONGSHU_USER_AGENT", "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)")
    XIAOHONGSHU_DELAY: float = float(os.getenv("XIAOHONGSHU_DELAY", "2.0"))
    
    # bilibili配置
    BILIBILI_USER_AGENT: str = os.getenv("BILIBILI_USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    BILIBILI_DELAY: float = float(os.getenv("BILIBILI_DELAY", "1.5"))
    
    # 知乎配置
    ZHIHU_USER_AGENT: str = os.getenv("ZHIHU_USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    ZHIHU_DELAY: float = float(os.getenv("ZHIHU_DELAY", "1.0"))
    
    # 微博配置
    WEIBO_USER_AGENT: str = os.getenv("WEIBO_USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    WEIBO_DELAY: float = float(os.getenv("WEIBO_DELAY", "1.5"))
    
    # Cookie配置 (用于模拟登录)
    DOUYIN_COOKIE: str = os.getenv("DOUYIN_COOKIE", "")
    BILIBILI_COOKIE: str = os.getenv("BILIBILI_COOKIE", "")
    WEIBO_COOKIE: str = os.getenv("WEIBO_COOKIE", "")
    ZHIHU_COOKIE: str = os.getenv("ZHIHU_COOKIE", "")
    XIAOHONGSHU_COOKIE: str = os.getenv("XIAOHONGSHU_COOKIE", "")
    TIEBA_COOKIE: str = os.getenv("TIEBA_COOKIE", "")
    
    # 爬虫通用配置
    MAX_CRAWL_PAGES: int = int(os.getenv("MAX_CRAWL_PAGES", "10"))
    CRAWL_TIMEOUT: int = int(os.getenv("CRAWL_TIMEOUT", "30"))
    
    # 嵌入维度
    EMBEDDING_DIMENSION: int = 768
    
    # 其他配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    MAX_CRAWL_ITEMS: int = int(os.getenv("MAX_CRAWL_ITEMS", "100"))
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))  # 1小时

# 全局配置实例
settings = Config()