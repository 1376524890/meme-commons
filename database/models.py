"""
meme-commons 数据库模型
"""
from sqlalchemy import Column, String, Text, Float, DateTime, Integer, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import json

Base = declarative_base()

class MemeCard(Base):
    """梗知识卡模型 - 符合项目文档要求"""
    __tablename__ = "meme_cards"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False, index=True)
    origin = Column(Text)  # 梗的起源
    meaning = Column(Text)  # 梗的含义
    examples = Column(Text)  # JSON string for SQLite
    trend_score = Column(Float, default=0.0)  # 趋势分数
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, default=func.now())
    
    def to_dict(self):
        """转换为字典格式 - 符合项目文档结构"""
        return {
            "id": str(self.id),
            "title": self.title,
            "origin": self.origin,
            "meaning": self.meaning,
            "examples": json.loads(self.examples) if self.examples else [],
            "trend_score": self.trend_score,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }

class RawPost(Base):
    """原始帖子表 - 支持多平台扩展"""
    __tablename__ = "posts_raw"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    platform = Column(String(50), nullable=False, index=True)
    url = Column(Text, unique=True)
    content = Column(Text, nullable=False)
    title = Column(String(500))  # 标题字段
    author = Column(String(100))
    timestamp = Column(DateTime, index=True)
    
    # 通用互动数据
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)  # 点赞数
    view_count = Column(Integer, default=0)  # 浏览数
    share_count = Column(Integer, default=0)  # 分享数
    
    # 平台特定数据 (JSON格式存储)
    platform_specific = Column(Text)  # 存储平台特定字段，如微博排名、知乎关注数等
    
    # 嵌入和处理状态
    embedding = Column(Text)  # JSON string for SQLite
    processed = Column(Boolean, default=False)
    source = Column(String(100))  # 内容来源，如"热搜"、"热门视频"等
    
    created_at = Column(DateTime, default=func.now())
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": str(self.id),
            "platform": self.platform,
            "url": self.url,
            "title": self.title,
            "content": self.content,
            "author": self.author,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "upvotes": self.upvotes,
            "downvotes": self.downvotes,
            "comment_count": self.comment_count,
            "like_count": self.like_count,
            "view_count": self.view_count,
            "share_count": self.share_count,
            "platform_specific": json.loads(self.platform_specific) if self.platform_specific else {},
            "embedding": json.loads(self.embedding) if self.embedding else None,
            "processed": self.processed,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    def update_platform_specific(self, **kwargs):
        """更新平台特定数据"""
        current_data = json.loads(self.platform_specific) if self.platform_specific else {}
        current_data.update(kwargs)
        self.platform_specific = json.dumps(current_data, ensure_ascii=False)

class TrendData(Base):
    """趋势数据表"""
    __tablename__ = "trend_data"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    meme_id = Column(String(36), nullable=False, index=True)
    date = Column(DateTime, default=func.now(), index=True)
    mentions_count = Column(Integer, default=0)
    sentiment_score = Column(Float, default=0.0)
    platform_breakdown = Column(Text)  # JSON string
    created_at = Column(DateTime, default=func.now())
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": str(self.id),
            "meme_id": str(self.meme_id),
            "date": self.date.isoformat() if self.date else None,
            "mentions_count": self.mentions_count,
            "sentiment_score": self.sentiment_score,
            "platform_breakdown": self.platform_breakdown,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self):
        """创建所有数据表"""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()
    
    def close(self):
        """关闭数据库连接"""
        self.engine.dispose()

# 数据库实例
db_manager = None

def init_database(database_url: str):
    """初始化数据库"""
    global db_manager
    db_manager = DatabaseManager(database_url)
    db_manager.create_tables()
    return db_manager

def get_db_session() -> Session:
    """获取数据库会话"""
    if db_manager is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return db_manager.get_session()