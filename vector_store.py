"""
meme-commons 向量数据库管理
"""
import redis
import json
import numpy as np
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from meme_commons.database.models import RawPost, MemeCard, TrendData, get_db_session
from meme_commons.config import settings
import logging

logger = logging.getLogger(__name__)

class VectorStoreManager:
    """向量数据库管理器"""
    
    def __init__(self):
        self.redis_client = redis.from_url(settings.CACHE_URL)
        self.collection_name = "meme_embeddings"
    
    def cache_embedding(self, post_id: str, embedding: List[float]):
        """缓存文本嵌入向量"""
        try:
            key = f"embedding:{post_id}"
            self.redis_client.setex(key, settings.CACHE_TTL, json.dumps(embedding))
        except Exception as e:
            logger.error(f"Failed to cache embedding for {post_id}: {e}")
    
    def get_cached_embedding(self, post_id: str) -> Optional[List[float]]:
        """获取缓存的嵌入向量"""
        try:
            key = f"embedding:{post_id}"
            result = self.redis_client.get(key)
            if result:
                return json.loads(result)
        except Exception as e:
            logger.error(f"Failed to get cached embedding for {post_id}: {e}")
        return None
    
    def cache_knowledge_card(self, title: str, card_data: Dict[str, Any]):
        """缓存梗知识卡"""
        try:
            key = f"meme_card:{title}"
            self.redis_client.setex(key, settings.CACHE_TTL, json.dumps(card_data))
        except Exception as e:
            logger.error(f"Failed to cache knowledge card for {title}: {e}")
    
    def get_cached_knowledge_card(self, title: str) -> Optional[Dict[str, Any]]:
        """获取缓存的梗知识卡"""
        try:
            key = f"meme_card:{title}"
            result = self.redis_client.get(key)
            if result:
                return json.loads(result)
        except Exception as e:
            logger.error(f"Failed to get cached knowledge card for {title}: {e}")
        return None
    
    def search_similar_memes(self, query_embedding: List[float], limit: int = 10) -> List[Dict[str, Any]]:
        """搜索相似的梗（简化的向量相似度搜索）"""
        # 这里实现简化的相似度搜索逻辑
        # 实际生产环境中应该使用Milvus等专业向量数据库
        results = []
        
        try:
            # 获取所有缓存的嵌入向量
            pattern = "embedding:*"
            keys = self.redis_client.keys(pattern)
            
            similarities = []
            for key in keys:
                try:
                    cached_embedding = json.loads(self.redis_client.get(key))
                    # 计算余弦相似度
                    similarity = self._cosine_similarity(query_embedding, cached_embedding)
                    post_id = key.decode().split(":")[1]
                    similarities.append((post_id, similarity))
                except Exception as e:
                    logger.error(f"Error processing embedding {key}: {e}")
                    continue
            
            # 按相似度排序
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # 获取前N个结果
            for post_id, similarity in similarities[:limit]:
                # 这里应该根据post_id从数据库获取更多信息
                results.append({
                    "post_id": post_id,
                    "similarity": similarity
                })
                
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
        
        return results
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        try:
            v1 = np.array(vec1)
            v2 = np.array(vec2)
            
            # 避免除零错误
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return np.dot(v1, v2) / (norm1 * norm2)
        except Exception:
            return 0.0
    
    def close(self):
        """关闭Redis连接"""
        self.redis_client.close()

class CacheManager:
    """缓存管理器"""
    
    def __init__(self):
        self.redis_client = redis.from_url(settings.CACHE_URL)
    
    def set(self, key: str, value: Any, ttl: int = None):
        """设置缓存"""
        try:
            ttl = ttl or settings.CACHE_TTL
            self.redis_client.setex(key, ttl, json.dumps(value))
        except Exception as e:
            logger.error(f"Failed to cache {key}: {e}")
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            result = self.redis_client.get(key)
            if result:
                return json.loads(result)
        except Exception as e:
            logger.error(f"Failed to get cache {key}: {e}")
        return None
    
    def delete(self, key: str):
        """删除缓存"""
        try:
            self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Failed to delete cache {key}: {e}")
    
    def clear_pattern(self, pattern: str):
        """清除匹配模式的缓存"""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
        except Exception as e:
            logger.error(f"Failed to clear pattern {pattern}: {e}")
    
    def close(self):
        """关闭Redis连接"""
        self.redis_client.close()

# 全局实例
vector_store = VectorStoreManager()
cache_manager = CacheManager()