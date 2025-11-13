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
    REDDIT_CLIENT_ID: str = os.getenv("REDDIT_CLIENT_ID", "")
    REDDIT_CLIENT_SECRET: str = os.getenv("REDDIT_CLIENT_SECRET", "")
    REDDIT_USER_AGENT: str = os.getenv("REDDIT_USER_AGENT", "meme-commons/1.0")
    
    # 嵌入维度
    EMBEDDING_DIMENSION: int = 768
    
    # 其他配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    MAX_CRAWL_ITEMS: int = int(os.getenv("MAX_CRAWL_ITEMS", "100"))
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))  # 1小时

# 全局配置实例
settings = Config()