"""
知识卡存储和管理系统
提供完整的知识卡CRUD操作、搜索、分析和监控功能
"""
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from database.models import MemeCard, TrendData, RawPost, get_db_session
import uuid

class KnowledgeCardManager:
    """知识卡管理器 - 提供完整的知识卡生命周期管理"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session: Session = get_db_session()
    
    def create_knowledge_card(self, title: str, origin: str, meaning: str, 
                            examples: List[str] = None, trend_score: float = 0.0,
                            tags: List[str] = None, source_posts: List[str] = None) -> str:
        """
        创建知识卡
        
        Args:
            title: 知识卡标题
            origin: 梗的起源
            meaning: 梗的含义
            examples: 例子列表
            trend_score: 趋势分数
            tags: 标签列表
            source_posts: 源帖子ID列表
            
        Returns:
            知识卡ID
        """
        try:
            # 生成知识卡ID
            card_id = str(uuid.uuid4())
            
            # 构建例子数据
            examples_data = {
                "examples": examples or [],
                "tags": tags or [],
                "source_posts": source_posts or [],
                "created_method": "automated_analysis",
                "version": "1.0"
            }
            
            # 创建知识卡
            card = MemeCard(
                id=card_id,
                title=title,
                origin=origin,
                meaning=meaning,
                examples=json.dumps(examples_data, ensure_ascii=False),
                trend_score=trend_score,
                created_at=datetime.now(),
                last_updated=datetime.now()
            )
            
            self.session.add(card)
            self.session.commit()
            
            self.logger.info(f"成功创建知识卡: {title} (ID: {card_id})")
            return card_id
            
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"创建知识卡失败: {e}")
            raise
    
    def get_knowledge_card(self, card_id: str) -> Optional[Dict[str, Any]]:
        """获取知识卡详情"""
        try:
            card = self.session.query(MemeCard).filter(MemeCard.id == card_id).first()
            if not card:
                return None
            
            card_data = card.to_dict()
            
            # 添加趋势数据
            trend_data = self.session.query(TrendData).filter(
                TrendData.meme_id == card_id
            ).order_by(desc(TrendData.date)).limit(30).all()
            
            card_data["trend_history"] = [t.to_dict() for t in trend_data]
            
            # 添加相关帖子统计
            total_posts = self.session.query(RawPost).filter(
                RawPost.content.like(f"%{card.title}%")
            ).count()
            
            card_data["related_posts_count"] = total_posts
            
            return card_data
            
        except Exception as e:
            self.logger.error(f"获取知识卡失败: {e}")
            return None
    
    def search_knowledge_cards(self, keyword: str = None, tags: List[str] = None,
                             min_trend_score: float = 0.0, limit: int = 20,
                             sort_by: str = "last_updated") -> List[Dict[str, Any]]:
        """搜索知识卡"""
        try:
            query = self.session.query(MemeCard)
            
            # 关键词搜索
            if keyword:
                query = query.filter(
                    or_(
                        MemeCard.title.like(f"%{keyword}%"),
                        MemeCard.meaning.like(f"%{keyword}%"),
                        MemeCard.origin.like(f"%{keyword}%")
                    )
                )
            
            # 趋势分数过滤
            query = query.filter(MemeCard.trend_score >= min_trend_score)
            
            # 标签过滤
            if tags:
                for tag in tags:
                    query = query.filter(MemeCard.examples.like(f'%"tags":%"{tag}"%'))
            
            # 排序
            if sort_by == "trend_score":
                query = query.order_by(desc(MemeCard.trend_score))
            elif sort_by == "title":
                query = query.order_by(asc(MemeCard.title))
            else:  # last_updated
                query = query.order_by(desc(MemeCard.last_updated))
            
            cards = query.limit(limit).all()
            
            return [card.to_dict() for card in cards]
            
        except Exception as e:
            self.logger.error(f"搜索知识卡失败: {e}")
            return []
    
    def update_knowledge_card(self, card_id: str, **kwargs) -> bool:
        """更新知识卡"""
        try:
            card = self.session.query(MemeCard).filter(MemeCard.id == card_id).first()
            if not card:
                return False
            
            # 更新字段
            for field, value in kwargs.items():
                if hasattr(card, field):
                    if field == "examples" and isinstance(value, (list, dict)):
                        # 合并现有的例子数据
                        current_examples = json.loads(card.examples) if card.examples else {}
                        if isinstance(value, list):
                            current_examples["examples"].extend(value)
                        else:
                            current_examples.update(value)
                        card.examples = json.dumps(current_examples, ensure_ascii=False)
                    else:
                        setattr(card, field, value)
            
            card.last_updated = datetime.now()
            self.session.commit()
            
            self.logger.info(f"成功更新知识卡: {card_id}")
            return True
            
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"更新知识卡失败: {e}")
            return False
    
    def delete_knowledge_card(self, card_id: str) -> bool:
        """删除知识卡"""
        try:
            # 删除相关的趋势数据
            self.session.query(TrendData).filter(TrendData.meme_id == card_id).delete()
            
            # 删除知识卡
            card = self.session.query(MemeCard).filter(MemeCard.id == card_id).first()
            if card:
                self.session.delete(card)
                self.session.commit()
                self.logger.info(f"成功删除知识卡: {card_id}")
                return True
            
            return False
            
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"删除知识卡失败: {e}")
            return False
    
    def get_trending_knowledge_cards(self, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """获取热门知识卡"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # 获取近期活跃的知识卡
            cards = self.session.query(MemeCard).filter(
                MemeCard.last_updated >= cutoff_date
            ).order_by(desc(MemeCard.trend_score)).limit(limit).all()
            
            return [card.to_dict() for card in cards]
            
        except Exception as e:
            self.logger.error(f"获取热门知识卡失败: {e}")
            return []
    
    def get_knowledge_card_statistics(self) -> Dict[str, Any]:
        """获取知识卡统计信息"""
        try:
            total_cards = self.session.query(MemeCard).count()
            
            # 平均趋势分数
            avg_trend_score = self.session.query(func.avg(MemeCard.trend_score)).scalar() or 0
            
            # 近期创建的知识卡数量
            recent_cards = self.session.query(MemeCard).filter(
                MemeCard.created_at >= datetime.now() - timedelta(days=7)
            ).count()
            
            # 高趋势分数的知识卡数量
            high_trend_cards = self.session.query(MemeCard).filter(
                MemeCard.trend_score >= 7.0
            ).count()
            
            # 标签统计
            all_cards = self.session.query(MemeCard.examples).all()
            tag_counts = {}
            for examples_json in all_cards:
                try:
                    examples = json.loads(examples_json[0]) if examples_json[0] else {}
                    tags = examples.get("tags", [])
                    for tag in tags:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
                except:
                    continue
            
            return {
                "total_cards": total_cards,
                "avg_trend_score": round(float(avg_trend_score), 2),
                "recent_cards": recent_cards,
                "high_trend_cards": high_trend_cards,
                "popular_tags": sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            }
            
        except Exception as e:
            self.logger.error(f"获取统计信息失败: {e}")
            return {}
    
    def batch_create_from_analysis(self, analysis_results: List[Dict[str, Any]]) -> List[str]:
        """批量从分析结果创建知识卡"""
        created_ids = []
        
        for analysis in analysis_results:
            try:
                # 从分析结果中提取信息
                title = analysis.get("title", analysis.get("meme_name", "未知梗"))
                meaning = analysis.get("meaning", analysis.get("summary", ""))
                origin = analysis.get("origin", analysis.get("platform", "未知平台"))
                examples = analysis.get("examples", [])
                trend_score = analysis.get("trend_score", 5.0)
                tags = analysis.get("tags", [])
                
                # 检查是否已存在相似的知识卡
                existing = self.search_knowledge_cards(keyword=title, limit=1)
                if existing and existing[0]["title"] == title:
                    # 更新现有知识卡
                    self.update_knowledge_card(existing[0]["id"], 
                                             trend_score=max(existing[0]["trend_score"], trend_score))
                    created_ids.append(existing[0]["id"])
                else:
                    # 创建新知识卡
                    card_id = self.create_knowledge_card(
                        title=title,
                        origin=origin,
                        meaning=meaning,
                        examples=examples,
                        trend_score=trend_score,
                        tags=tags,
                        source_posts=analysis.get("source_post_ids", [])
                    )
                    created_ids.append(card_id)
                    
            except Exception as e:
                self.logger.error(f"批量创建知识卡时处理分析结果失败: {e}")
                continue
        
        self.logger.info(f"批量创建知识卡完成，成功创建 {len(created_ids)} 个")
        return created_ids
    
    def update_trend_data(self, card_id: str, mentions_count: int, 
                         sentiment_score: float, platform_breakdown: Dict[str, int]):
        """更新知识卡的趋势数据"""
        try:
            trend_data = TrendData(
                id=str(uuid.uuid4()),
                meme_id=card_id,
                date=datetime.now(),
                mentions_count=mentions_count,
                sentiment_score=sentiment_score,
                platform_breakdown=json.dumps(platform_breakdown, ensure_ascii=False)
            )
            
            self.session.add(trend_data)
            
            # 更新知识卡的趋势分数
            card = self.session.query(MemeCard).filter(MemeCard.id == card_id).first()
            if card:
                # 计算新的趋势分数（基于历史数据）
                card.trend_score = max(card.trend_score, sentiment_score * 10 + mentions_count / 100)
                card.last_updated = datetime.now()
            
            self.session.commit()
            
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"更新趋势数据失败: {e}")
    
    def get_related_cards(self, card_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """获取相关知识卡"""
        try:
            card = self.session.query(MemeCard).filter(MemeCard.id == card_id).first()
            if not card:
                return []
            
            # 基于标题相似性查找相关卡片
            related_cards = self.session.query(MemeCard).filter(
                and_(
                    MemeCard.id != card_id,
                    or_(
                        MemeCard.title.like(f"%{card.title[:5]}%"),
                        MemeCard.examples.like(f'%"tags":%"{card.title}"%')
                    )
                )
            ).limit(limit).all()
            
            return [c.to_dict() for c in related_cards]
            
        except Exception as e:
            self.logger.error(f"获取相关知识卡失败: {e}")
            return []
    
    def close(self):
        """关闭数据库连接"""
        if self.session:
            self.session.close()

class KnowledgeCardMonitor:
    """知识卡监控器 - 实时监控系统状态和知识卡变化"""
    
    def __init__(self):
        self.manager = KnowledgeCardManager()
        self.logger = logging.getLogger(__name__)
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        try:
            stats = self.manager.get_knowledge_card_statistics()
            
            # 添加系统健康状态
            system_status = {
                "database_connection": "healthy",
                "total_cards": stats.get("total_cards", 0),
                "avg_trend_score": stats.get("avg_trend_score", 0),
                "recent_activity": stats.get("recent_cards", 0),
                "high_trend_cards": stats.get("high_trend_cards", 0),
                "last_updated": datetime.now().isoformat()
            }
            
            return system_status
            
        except Exception as e:
            self.logger.error(f"获取系统状态失败: {e}")
            return {"database_connection": "error", "error": str(e)}
    
    def get_recent_changes(self, hours: int = 24) -> List[Dict[str, Any]]:
        """获取最近的变更记录"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            recent_cards = self.manager.session.query(MemeCard).filter(
                MemeCard.last_updated >= cutoff_time
            ).order_by(desc(MemeCard.last_updated)).all()
            
            changes = []
            for card in recent_cards:
                changes.append({
                    "action": "updated",
                    "card_id": card.id,
                    "title": card.title,
                    "timestamp": card.last_updated.isoformat(),
                    "trend_score": card.trend_score
                })
            
            return changes
            
        except Exception as e:
            self.logger.error(f"获取变更记录失败: {e}")
            return []
    
    def cleanup_old_data(self, days: int = 30):
        """清理旧数据"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # 删除旧的趋势数据
            old_trends = self.manager.session.query(TrendData).filter(
                TrendData.date < cutoff_date
            ).delete()
            
            self.manager.session.commit()
            
            self.logger.info(f"清理完成，删除 {old_trends} 条旧趋势数据")
            return old_trends
            
        except Exception as e:
            self.manager.session.rollback()
            self.logger.error(f"清理旧数据失败: {e}")
            return 0
    
    def close(self):
        """关闭连接"""
        self.manager.close()