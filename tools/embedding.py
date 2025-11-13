"""
meme-commons 文本嵌入工具 - 调用Dashscope embedding API
"""
import requests
import json
import numpy as np
from typing import List, Dict, Any, Optional
import logging
from meme_commons.config import settings
from meme_commons.vector_store import vector_store
from meme_commons.database.models import RawPost, get_db_session
import time

logger = logging.getLogger(__name__)

class DashscopeEmbeddingClient:
    """Dashscope嵌入API客户端"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.DASHSCOPE_API_KEY
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-embedding/text-embedding"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.model = settings.DASHSCOPE_EMBEDDING_MODEL
        self.max_batch_size = 10  # API限制每次最多10条文本
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """批量嵌入文本"""
        if not self.api_key:
            logger.error("Dashscope API key not configured")
            return []
        
        if not texts:
            return []
        
        embeddings = []
        
        # 批量处理（API限制）
        for i in range(0, len(texts), self.max_batch_size):
            batch = texts[i:i + self.max_batch_size]
            batch_embeddings = self._embed_batch(batch)
            
            if batch_embeddings:
                embeddings.extend(batch_embeddings)
            else:
                # 如果批次失败，尝试逐个处理
                logger.warning(f"Batch {i//self.max_batch_size} failed, trying individual texts")
                for text in batch:
                    single_embedding = self._embed_single_text(text)
                    if single_embedding:
                        embeddings.append(single_embedding)
                    else:
                        # 如果单个文本也失败，使用零向量
                        logger.warning(f"Failed to embed text: {text[:50]}...")
                        embeddings.append([0.0] * settings.EMBEDDING_DIMENSION)
            
            # API速率限制
            time.sleep(0.1)
        
        return embeddings
    
    def _embed_batch(self, texts: List[str]) -> Optional[List[List[float]]]:
        """批量嵌入文本（内部方法）"""
        try:
            payload = {
                "model": self.model,
                "input": {
                    "texts": texts
                },
                "parameters": {
                    "text_type": "document"
                }
            }
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") == "200":
                embeddings = result["data"]["embeddings"]
                return [emb["embedding"] for emb in embeddings]
            else:
                logger.error(f"Dashscope API error: {result}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to embed batch: {e}")
            return None
    
    def _embed_single_text(self, text: str) -> Optional[List[float]]:
        """嵌入单个文本"""
        try:
            payload = {
                "model": self.model,
                "input": {
                    "texts": [text]
                },
                "parameters": {
                    "text_type": "document"
                }
            }
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") == "200":
                return result["data"]["embeddings"][0]["embedding"]
            else:
                logger.error(f"Dashscope API error: {result}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to embed single text: {e}")
            return None
    
    def embed_query(self, query: str) -> Optional[List[float]]:
        """嵌入查询文本"""
        return self._embed_single_text(query)

class EmbeddingTool:
    """嵌入工具"""
    
    def __init__(self):
        self.client = DashscopeEmbeddingClient()
        
    def embed_and_store_posts(self, posts: List[Dict[str, Any]]) -> bool:
        """嵌入帖子内容并存储"""
        if not posts:
            logger.warning("No posts to embed")
            return False
        
        try:
            # 提取文本内容
            texts = [post["content"] for post in posts]
            
            # 批量嵌入
            embeddings = self.client.embed_texts(texts)
            
            if not embeddings:
                logger.error("Failed to generate embeddings")
                return False
            
            # 存储到数据库和缓存
            session = get_db_session()
            try:
                for i, (post, embedding) in enumerate(zip(posts, embeddings)):
                    # 更新数据库中的原始帖子
                    db_post = session.query(RawPost).filter_by(
                        url=post["url"]
                    ).first()
                    
                    if db_post:
                        db_post.embedding = embedding
                        db_post.processed = True
                    else:
                        # 如果数据库中不存在，创建新记录
                        new_post = RawPost(
                            platform=post["platform"],
                            url=post["url"],
                            content=post["content"],
                            author=post.get("author"),
                            timestamp=post.get("timestamp"),
                            upvotes=post.get("upvotes", 0),
                            downvotes=post.get("downvotes", 0),
                            comment_count=post.get("comment_count", 0),
                            embedding=embedding,
                            processed=True
                        )
                        session.add(new_post)
                    
                    # 缓存嵌入向量
                    post_id = db_post.id if db_post else f"temp_{i}"
                    vector_store.cache_embedding(str(post_id), embedding)
                
                session.commit()
                logger.info(f"Successfully embedded and stored {len(posts)} posts")
                return True
                
            except Exception as e:
                session.rollback()
                logger.error(f"Failed to store embeddings: {e}")
                return False
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Failed to embed posts: {e}")
            return False
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """嵌入文本列表"""
        return self.client.embed_texts(texts)
    
    def get_text_embedding(self, text: str) -> Optional[List[float]]:
        """获取单个文本的嵌入向量"""
        return self.client._embed_single_text(text)
    
    def search_similar_content(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """基于嵌入向量搜索相似内容"""
        try:
            # 嵌入查询文本
            query_embedding = self.client.embed_query(query)
            if not query_embedding:
                logger.error("Failed to embed query")
                return []
            
            # 使用向量存储进行相似度搜索
            similar_results = vector_store.search_similar_memes(query_embedding, limit)
            
            # 补充详细信息
            detailed_results = []
            session = get_db_session()
            try:
                for result in similar_results:
                    # 从数据库获取完整信息
                    db_post = session.query(RawPost).filter_by(
                        id=result["post_id"]
                    ).first()
                    
                    if db_post:
                        detailed_results.append({
                            "post_id": result["post_id"],
                            "content": db_post.content,
                            "platform": db_post.platform,
                            "url": db_post.url,
                            "author": db_post.author,
                            "timestamp": db_post.timestamp,
                            "upvotes": db_post.upvotes,
                            "downvotes": db_post.downvotes,
                            "comment_count": db_post.comment_count,
                            "similarity": result["similarity"]
                        })
            finally:
                session.close()
            
            return detailed_results
            
        except Exception as e:
            logger.error(f"Failed to search similar content: {e}")
            return []

# 全局嵌入工具实例
embedding_tool = EmbeddingTool()