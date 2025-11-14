"""
meme-commons 趋势分析工具 - 统计热点和热度
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, text
import logging
import json
from collections import defaultdict, Counter
import statistics
import math
from database.models import MemeCard, RawPost, TrendData, get_db_session
from tools.summarizer import meme_summarizer

logger = logging.getLogger(__name__)

class TrendAnalysisTool:
    """趋势分析工具"""
    
    def __init__(self):
        self.platform_weights = {
            "reddit": 1.0,
            "twitter": 1.2,
            "weibo": 1.1,
            "tiktok": 1.3,
            "bilibili": 1.0
        }
        
        self.time_decay_factor = 0.95  # 时间衰减因子
    
    def analyze_trend(self, meme_id: str, time_window: str = "7d") -> Optional[Dict[str, Any]]:
        """分析指定梗的趋势"""
        try:
            session = get_db_session()
            
            # 解析时间窗口
            days = self._parse_time_window(time_window)
            start_date = datetime.now() - timedelta(days=days)
            
            # 获取该梗的所有相关数据
            trend_data = self._get_meme_trend_data(session, meme_id, start_date)
            
            if not trend_data:
                session.close()
                return None
            
            # 计算趋势指标
            trend_analysis = {
                "meme_id": meme_id,
                "time_window": time_window,
                "total_mentions": len(trend_data["mentions"]),
                "sentiment_analysis": self._analyze_sentiment(trend_data["mentions"]),
                "platform_distribution": self._analyze_platform_distribution(trend_data["mentions"]),
                "temporal_pattern": self._analyze_temporal_pattern(trend_data["mentions"], days),
                "engagement_metrics": self._analyze_engagement_metrics(trend_data["mentions"]),
                "trend_score": self._calculate_trend_score(trend_data),
                "prediction": self._predict_trend_direction(trend_data),
                "last_updated": datetime.now().isoformat()
            }
            
            # 保存趋势数据到数据库
            self._save_trend_data(session, meme_id, trend_analysis)
            
            session.close()
            
            logger.info(f"Trend analysis completed for meme {meme_id}")
            return trend_analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze trend for meme {meme_id}: {e}")
            return None
    
    def get_trending_memes(self, limit: int = 20, time_window: str = "24h") -> List[Dict[str, Any]]:
        """获取热门梗列表"""
        try:
            session = get_db_session()
            
            days = self._parse_time_window(time_window)
            start_date = datetime.now() - timedelta(days=days)
            
            # 获取热门梗
            trending_memes = session.query(MemeCard).filter(
                and_(
                    MemeCard.is_active == True,
                    MemeCard.last_updated >= start_date
                )
            ).order_by(
                desc(MemeCard.trend_score),
                desc(MemeCard.popularity_score)
            ).limit(limit).all()
            
            results = []
            for meme in trending_memes:
                # 为每个梗计算实时趋势数据
                trend_data = self._get_meme_trend_data(session, str(meme.id), start_date)
                
                meme_result = meme.to_dict()
                meme_result["current_trend"] = {
                    "mentions_count": len(trend_data["mentions"]) if trend_data else 0,
                    "trend_score": meme.trend_score,
                    "sentiment_score": self._calculate_sentiment_score(trend_data["mentions"]) if trend_data else 0.0
                }
                
                results.append(meme_result)
            
            session.close()
            
            # 按当前热度排序
            results.sort(key=lambda x: (
                x["current_trend"]["mentions_count"],
                x["current_trend"]["trend_score"]
            ), reverse=True)
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get trending memes: {e}")
            return []
    
    def analyze_meme_evolution(self, meme_id: str, time_spans: List[str] = ["7d", "30d", "90d"]) -> Dict[str, Any]:
        """分析梗的演进趋势"""
        try:
            session = get_db_session()
            
            evolution_data = {}
            
            for span in time_spans:
                days = self._parse_time_window(span)
                start_date = datetime.now() - timedelta(days=days)
                
                trend_data = self._get_meme_trend_data(session, meme_id, start_date)
                
                if trend_data:
                    evolution_data[span] = {
                        "mentions_count": len(trend_data["mentions"]),
                        "avg_engagement": self._calculate_avg_engagement(trend_data["mentions"]),
                        "sentiment_trend": self._analyze_sentiment_trend(trend_data["mentions"]),
                        "platform_shift": self._analyze_platform_shift(trend_data["mentions"])
                    }
            
            session.close()
            
            return {
                "meme_id": meme_id,
                "evolution": evolution_data,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze meme evolution for {meme_id}: {e}")
            return {}
    
    def get_trend_categories(self, time_window: str = "7d") -> Dict[str, str]:
        """获取趋势分类统计"""
        try:
            session = get_db_session()
            
            days = self._parse_time_window(time_window)
            start_date = datetime.now() - timedelta(days=days)
            
            # 按类别统计梗的活跃度
            category_stats = session.query(
                MemeCard.category,
                func.count(MemeCard.id).label('meme_count'),
                func.avg(MemeCard.trend_score).label('avg_trend_score')
            ).filter(
                and_(
                    MemeCard.is_active == True,
                    MemeCard.last_updated >= start_date
                )
            ).group_by(MemeCard.category).all()
            
            results = {}
            for category, count, avg_score in category_stats:
                results[category] = {
                    "meme_count": count,
                    "avg_trend_score": float(avg_score or 0),
                    "popularity": "high" if avg_score > 0.7 else "medium" if avg_score > 0.4 else "low"
                }
            
            session.close()
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get trend categories: {e}")
            return {}
    
    def _get_meme_trend_data(self, session: Session, meme_id: str, start_date: datetime) -> Optional[Dict[str, Any]]:
        """获取梗的趋势数据"""
        try:
            # 获取相关原始帖子
            mentions = session.query(RawPost).filter(
                and_(
                    RawPost.timestamp >= start_date,
                    or_(
                        RawPost.content.contains(meme_id),
                        RawPost.url.contains(meme_id)
                    )
                )
            ).order_by(desc(RawPost.timestamp)).all()
            
            if not mentions:
                return None
            
            return {
                "mentions": [post.to_dict() for post in mentions],
                "meme_id": meme_id,
                "start_date": start_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get trend data for meme {meme_id}: {e}")
            return None
    
    def _analyze_sentiment(self, mentions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析情感倾向"""
        # 简化的情感分析
        # 实际中可以使用更复杂的NLP模型
        
        positive_keywords = ["好", "棒", "赞", "喜欢", "爱", "厉害", "强", "优秀", "顶", "支持"]
        negative_keywords = ["差", "烂", "垃圾", "讨厌", "恶心", "讨厌", "不行", "弱", "失败"]
        
        sentiment_scores = []
        
        for mention in mentions:
            content = mention.get("content", "").lower()
            upvotes = mention.get("upvotes", 0)
            downvotes = mention.get("downvotes", 0)
            
            # 简单的关键词情感分析
            positive_count = sum(1 for word in positive_keywords if word in content)
            negative_count = sum(1 for word in negative_keywords if word in content)
            
            # 结合点赞数据进行情感分析
            vote_ratio = upvotes / max(upvotes + downvotes, 1) if upvotes + downvotes > 0 else 0.5
            
            # 综合情感分数
            keyword_sentiment = (positive_count - negative_count) / max(positive_count + negative_count, 1)
            final_sentiment = (keyword_sentiment + vote_ratio) / 2
            
            sentiment_scores.append(final_sentiment)
        
        if not sentiment_scores:
            return {"overall_sentiment": "neutral", "sentiment_score": 0.0}
        
        avg_sentiment = statistics.mean(sentiment_scores)
        
        return {
            "overall_sentiment": "positive" if avg_sentiment > 0.1 else "negative" if avg_sentiment < -0.1 else "neutral",
            "sentiment_score": avg_sentiment,
            "positive_ratio": len([s for s in sentiment_scores if s > 0.1]) / len(sentiment_scores),
            "negative_ratio": len([s for s in sentiment_scores if s < -0.1]) / len(sentiment_scores)
        }
    
    def _analyze_platform_distribution(self, mentions: List[Dict[str, Any]]) -> Dict[str, float]:
        """分析平台分布"""
        platform_counts = Counter(mention.get("platform", "unknown") for mention in mentions)
        total = len(mentions)
        
        return {
            platform: count / total
            for platform, count in platform_counts.items()
        }
    
    def _analyze_temporal_pattern(self, mentions: List[Dict[str, Any]], days: int) -> Dict[str, Any]:
        """分析时间模式"""
        # 按小时统计提及量
        hourly_counts = defaultdict(int)
        
        for mention in mentions:
            timestamp = mention.get("timestamp")
            if timestamp and isinstance(timestamp, datetime):
                hour = timestamp.hour
                hourly_counts[hour] += 1
        
        # 找出高峰时间
        peak_hours = sorted(hourly_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # 计算日增长趋势
        daily_counts = defaultdict(int)
        for mention in mentions:
            timestamp = mention.get("timestamp")
            if timestamp and isinstance(timestamp, datetime):
                date_key = timestamp.date()
                daily_counts[date_key] += 1
        
        # 计算增长率
        dates = sorted(daily_counts.keys())
        growth_rates = []
        if len(dates) > 1:
            for i in range(1, len(dates)):
                prev_count = daily_counts[dates[i-1]]
                curr_count = daily_counts[dates[i]]
                if prev_count > 0:
                    growth_rate = (curr_count - prev_count) / prev_count
                    growth_rates.append(growth_rate)
        
        return {
            "peak_hours": [hour for hour, count in peak_hours],
            "daily_growth_rate": statistics.mean(growth_rates) if growth_rates else 0.0,
            "mention_distribution": dict(hourly_counts),
            "total_days_active": len(daily_counts)
        }
    
    def _analyze_engagement_metrics(self, mentions: List[Dict[str, Any]]) -> Dict[str, float]:
        """分析参与度指标"""
        if not mentions:
            return {"avg_upvotes": 0, "avg_comments": 0, "engagement_score": 0}
        
        total_upvotes = sum(mention.get("upvotes", 0) for mention in mentions)
        total_comments = sum(mention.get("comment_count", 0) for mention in mentions)
        
        avg_upvotes = total_upvotes / len(mentions)
        avg_comments = total_comments / len(mentions)
        
        # 计算综合参与度分数
        engagement_score = (avg_upvotes + avg_comments * 2) / 100  # 标准化到0-1
        
        return {
            "avg_upvotes": avg_upvotes,
            "avg_comments": avg_comments,
            "engagement_score": min(1.0, engagement_score)
        }
    
    def _calculate_trend_score(self, trend_data: Dict[str, Any]) -> float:
        """计算趋势分数"""
        mentions = trend_data["mentions"]
        if not mentions:
            return 0.0
        
        # 基础分数：提及次数
        base_score = min(len(mentions) / 100.0, 1.0)  # 标准化到0-1
        
        # 时间衰减：越新的内容权重越大
        time_weighted_score = 0.0
        current_time = datetime.now()
        
        for mention in mentions:
            timestamp = mention.get("timestamp")
            if timestamp and isinstance(timestamp, datetime):
                days_old = (current_time - timestamp).days
                time_weight = math.pow(self.time_decay_factor, days_old)
                
                # 结合参与度
                engagement = mention.get("upvotes", 0) + mention.get("comment_count", 0)
                weighted_engagement = engagement * time_weight
                
                time_weighted_score += weighted_engagement
        
        # 平台权重
        platform_weight = sum(
            self.platform_weights.get(mention.get("platform", "unknown"), 1.0)
            for mention in mentions
        ) / len(mentions)
        
        final_score = (base_score + time_weighted_score / 1000) * platform_weight
        
        return min(1.0, final_score)
    
    def _predict_trend_direction(self, trend_data: Dict[str, Any]) -> Dict[str, Any]:
        """预测趋势方向"""
        mentions = trend_data["mentions"]
        if len(mentions) < 5:
            return {"direction": "insufficient_data", "confidence": 0.0}
        
        # 分析最近几天的增长趋势
        daily_counts = defaultdict(int)
        for mention in mentions:
            timestamp = mention.get("timestamp")
            if timestamp and isinstance(timestamp, datetime):
                date_key = timestamp.date()
                daily_counts[date_key] += 1
        
        sorted_dates = sorted(daily_counts.keys())
        
        if len(sorted_dates) < 3:
            return {"direction": "insufficient_data", "confidence": 0.0}
        
        # 计算最近几天的增长率
        recent_days = sorted_dates[-3:]
        recent_counts = [daily_counts[date] for date in recent_days]
        
        # 简单线性趋势分析
        if len(recent_counts) >= 3:
            x = list(range(len(recent_counts)))
            slope = self._calculate_slope(x, recent_counts)
            
            if slope > 0.1:
                direction = "rising"
                confidence = min(0.9, slope)
            elif slope < -0.1:
                direction = "declining"
                confidence = min(0.9, abs(slope))
            else:
                direction = "stable"
                confidence = 0.5
        else:
            direction = "unknown"
            confidence = 0.0
        
        return {
            "direction": direction,
            "confidence": confidence,
            "recent_slope": slope if len(recent_counts) >= 3 else 0.0,
            "daily_counts": recent_counts
        }
    
    def _calculate_slope(self, x: List[int], y: List[float]) -> float:
        """计算线性趋势的斜率"""
        n = len(x)
        if n < 2:
            return 0.0
        
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi * xi for xi in x)
        
        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return 0.0
        
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        return slope
    
    def _calculate_sentiment_score(self, mentions: List[Dict[str, Any]]) -> float:
        """计算情感分数"""
        if not mentions:
            return 0.0
        
        sentiment_data = self._analyze_sentiment(mentions)
        return sentiment_data.get("sentiment_score", 0.0)
    
    def _save_trend_data(self, session: Session, meme_id: str, trend_analysis: Dict[str, Any]):
        """保存趋势数据到数据库"""
        try:
            # 保存当前趋势数据
            new_trend = TrendData(
                meme_id=meme_id,
                mentions_count=trend_analysis["total_mentions"],
                sentiment_score=trend_analysis["sentiment_analysis"]["sentiment_score"],
                platform_breakdown=json.dumps(trend_analysis["platform_distribution"])
            )
            
            session.add(new_trend)
            session.commit()
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save trend data: {e}")
    
    def _parse_time_window(self, time_window: str) -> int:
        """解析时间窗口字符串"""
        if time_window.endswith("h"):
            return int(time_window[:-1]) // 24
        elif time_window.endswith("d"):
            return int(time_window[:-1])
        elif time_window.endswith("w"):
            return int(time_window[:-1]) * 7
        else:
            # 默认返回7天
            return 7
    
    def _calculate_avg_engagement(self, mentions: List[Dict[str, Any]]) -> float:
        """计算平均参与度"""
        if not mentions:
            return 0.0
        
        engagements = [mention.get("upvotes", 0) + mention.get("comment_count", 0) for mention in mentions]
        return statistics.mean(engagements)
    
    def _analyze_sentiment_trend(self, mentions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析情感趋势"""
        # 这里可以实现更详细的情感趋势分析
        return self._analyze_sentiment(mentions)
    
    def _analyze_platform_shift(self, mentions: List[Dict[str, Any]]) -> Dict[str, float]:
        """分析平台迁移"""
        return self._analyze_platform_distribution(mentions)

# 全局趋势分析工具实例
trend_analysis_tool = TrendAnalysisTool()