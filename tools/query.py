"""
meme-commons 知识库查询工具
"""
from typing import List, Dict, Any, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from sqlalchemy.sql import func
import logging
from database.models import MemeCard, RawPost, TrendData, get_db_session
from vector_store import vector_store, cache_manager
from tools.embedding import embedding_tool

logger = logging.getLogger(__name__)

class QueryTool:
    """知识库查询工具"""
    
    def __init__(self):
        pass
    
    def query_knowledge(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """查询梗知识"""
        if not query:
            return []
        
        # 首先尝试从缓存获取
        cache_key = f"meme_query:{query}:{limit}"
        cached_result = cache_manager.get(cache_key)
        if cached_result:
            logger.info(f"Returning cached result for query: {query}")
            return cached_result
        
        results = []
        
        try:
            session = get_db_session()
            
            # 1. 直接在梗知识卡中搜索
            direct_results = self._search_meme_cards(session, query, limit // 2)
            results.extend(direct_results)
            
            # 2. 如果知识卡搜索结果不够，使用向量搜索
            if len(results) < limit:
                vector_results = self._vector_search(session, query, limit - len(results))
                results.extend(vector_results)
            
            # 3. 搜索原始帖子中的相关信息
            if len(results) < limit:
                post_results = self._search_raw_posts(session, query, limit - len(results))
                results.extend(post_results)
            
            session.close()
            
            # 缓存结果
            cache_manager.set(cache_key, results, ttl=1800)  # 30分钟缓存
            
            logger.info(f"Found {len(results)} results for query: {query}")
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Failed to query knowledge for '{query}': {e}")
            return []
    
    def _search_meme_cards(self, session: Session, query: str, limit: int) -> List[Dict[str, Any]]:
        """在梗知识卡中搜索"""
        try:
            # 全文搜索（标题、含义、出处）
            results = session.query(MemeCard).filter(
                and_(
                    MemeCard.is_active == True,
                    or_(
                        MemeCard.title.ilike(f"%{query}%"),
                        MemeCard.meaning.ilike(f"%{query}%"),
                        MemeCard.origin.ilike(f"%{query}%"),
                        MemeCard.category.ilike(f"%{query}%")
                    )
                )
            ).order_by(
                desc(MemeCard.trend_score),
                desc(MemeCard.popularity_score)
            ).limit(limit).all()
            
            meme_results = []
            for meme in results:
                result = meme.to_dict()
                
                # 获取最新的趋势数据
                trend_data = session.query(TrendData).filter(
                    TrendData.meme_id == meme.id
                ).order_by(desc(TrendData.date)).first()
                
                if trend_data:
                    result["latest_trend"] = trend_data.to_dict()
                
                meme_results.append(result)
            
            return meme_results
            
        except Exception as e:
            logger.error(f"Failed to search meme cards: {e}")
            return []
    
    def _vector_search(self, session: Session, query: str, limit: int) -> List[Dict[str, Any]]:
        """向量搜索相似内容"""
        try:
            # 使用嵌入工具进行向量搜索
            similar_posts = embedding_tool.search_similar_content(query, limit)
            
            post_results = []
            for post in similar_posts:
                # 检查这个帖子是否已经被关联到某个梗知识卡
                # 这里简化处理，实际中可能需要更复杂的关联逻辑
                meme_card = self._find_related_meme_card(session, post["content"])
                
                if meme_card:
                    result = meme_card.to_dict()
                    result["related_post"] = post
                    post_results.append(result)
                else:
                    # 如果没有找到相关的梗知识卡，直接返回帖子信息
                    post_results.append({
                        "title": "Related Content",
                        "meaning": "相关但未分类的梗内容",
                        "origin": f"来自{post['platform']}",
                        "examples": [post["content"][:100] + "..." if len(post["content"]) > 100 else post["content"]],
                        "trend_score": 0.5,
                        "related_post": post
                    })
            
            return post_results
            
        except Exception as e:
            logger.error(f"Failed to perform vector search: {e}")
            return []
    
    def _search_raw_posts(self, session: Session, query: str, limit: int) -> List[Dict[str, Any]]:
        """在原始帖子中搜索"""
        try:
            results = session.query(RawPost).filter(
                and_(
                    RawPost.processed == True,
                    RawPost.content.ilike(f"%{query}%")
                )
            ).order_by(
                desc(RawPost.upvotes),
                desc(RawPost.created_at)
            ).limit(limit).all()
            
            post_results = []
            for post in results:
                post_results.append({
                    "title": "Raw Content",
                    "meaning": "原始梗内容",
                    "origin": f"来自{post.platform}平台",
                    "examples": [post.content[:200] + "..." if len(post.content) > 200 else post.content],
                    "trend_score": min(post.upvotes / 100.0, 1.0),
                    "raw_post": post.to_dict()
                })
            
            return post_results
            
        except Exception as e:
            logger.error(f"Failed to search raw posts: {e}")
            return []
    
    def _find_related_meme_card(self, session: Session, content: str) -> Optional[MemeCard]:
        """查找与内容相关的梗知识卡（简化实现）"""
        # 这里实现一个简化的关联逻辑
        # 实际中可以使用更复杂的NLP技术
        
        # 从内容中提取关键词
        keywords = self._extract_keywords(content)
        
        if not keywords:
            return None
        
        # 搜索包含这些关键词的梗知识卡
        meme_card = session.query(MemeCard).filter(
            and_(
                MemeCard.is_active == True,
                or_(
                    MemeCard.title.ilike(f"%{keywords[0]}%"),
                    MemeCard.meaning.ilike(f"%{keywords[0]}%"),
                    MemeCard.origin.ilike(f"%{keywords[0]}%"),
                    MemeCard.category.ilike(f"%{keywords[0]}%")
                )
            )
        ).order_by(desc(MemeCard.trend_score)).first()
        
        return meme_card
    
    def _extract_keywords(self, text: str, max_keywords: int = 3) -> List[str]:
        """提取文本中的关键词（简化实现）"""
        import re
        
        # 移除标点符号和特殊字符
        cleaned_text = re.sub(r'[^\w\s]', ' ', text.lower())
        
        # 分词并过滤停用词
        words = cleaned_text.split()
        stop_words = {'的', '了', '是', '在', '有', '和', '与', '或', '但', '不', '很', '也', '都', '要', '会', '可以'}
        keywords = [word for word in words if len(word) > 1 and word not in stop_words]
        
        # 按长度和频率排序，取前几个
        keyword_freq = {}
        for word in keywords:
            keyword_freq[word] = keyword_freq.get(word, 0) + 1
        
        sorted_keywords = sorted(keyword_freq.keys(), key=lambda x: (keyword_freq[x], len(x)), reverse=True)
        
        return sorted_keywords[:max_keywords]
    
    def get_trending_memes(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取热门梗"""
        try:
            session = get_db_session()
            
            # 按趋势分数排序的活跃梗
            memes = session.query(MemeCard).filter(
                MemeCard.is_active == True
            ).order_by(
                desc(MemeCard.trend_score),
                desc(MemeCard.popularity_score),
                desc(MemeCard.last_updated)
            ).limit(limit).all()
            
            results = [meme.to_dict() for meme in memes]
            
            # 补充趋势数据
            for result in results:
                trend_data = session.query(TrendData).filter(
                    TrendData.meme_id == result["id"]
                ).order_by(desc(TrendData.date)).limit(7).all()
                
                result["trend_history"] = [trend.to_dict() for trend in trend_data]
            
            session.close()
            
            logger.info(f"Retrieved {len(results)} trending memes")
            return results
            
        except Exception as e:
            logger.error(f"Failed to get trending memes: {e}")
            return []
    
    def get_memes_by_category(self, category: str, limit: int = 10) -> List[Dict[str, Any]]:
        """按类别获取梗"""
        try:
            session = get_db_session()
            
            memes = session.query(MemeCard).filter(
                and_(
                    MemeCard.is_active == True,
                    MemeCard.category == category
                )
            ).order_by(
                desc(MemeCard.trend_score),
                desc(MemeCard.popularity_score)
            ).limit(limit).all()
            
            results = [meme.to_dict() for meme in memes]
            session.close()
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get memes by category '{category}': {e}")
            return []
    
    def advanced_search(self, filters: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """高级搜索"""
        try:
            session = get_db_session()
            
            query = session.query(MemeCard).filter(MemeCard.is_active == True)
            
            # 应用各种过滤条件
            if filters.get("query"):
                query = query.filter(
                    or_(
                        MemeCard.title.ilike(f"%{filters['query']}%"),
                        MemeCard.meaning.ilike(f"%{filters['query']}%"),
                        MemeCard.origin.ilike(f"%{filters['query']}%")
                    )
                )
            
            if filters.get("category"):
                query = query.filter(MemeCard.category == filters["category"])
            
            if filters.get("min_trend_score"):
                query = query.filter(MemeCard.trend_score >= filters["min_trend_score"])
            
            if filters.get("language"):
                query = query.filter(MemeCard.language == filters["language"])
            
            # 排序
            sort_by = filters.get("sort_by", "trend_score")
            sort_order = filters.get("sort_order", "desc")
            
            if sort_order.lower() == "desc":
                query = query.order_by(desc(getattr(MemeCard, sort_by)))
            else:
                query = query.order_by(asc(getattr(MemeCard, sort_by)))
            
            results = query.limit(limit).all()
            
            final_results = [meme.to_dict() for meme in results]
            session.close()
            
            return final_results
            
        except Exception as e:
            logger.error(f"Failed to perform advanced search: {e}")
            return []

# 全局查询工具实例
query_tool = QueryTool()