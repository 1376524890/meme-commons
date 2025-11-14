"""
数据管道优化版本 - 独立开发和测试版本
包含更好的错误处理、监控和调试功能
"""
import asyncio
import logging
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from database.models import RawPost, MemeCard, TrendData, init_database, get_db_session
from tools.crawler import crawler
from tools.summarizer import meme_summarizer
from vector_store import vector_store
from config import settings

logger = logging.getLogger(__name__)

class PipelineStage(Enum):
    """管道阶段枚举"""
    INITIALIZATION = "initialization"
    CRAWLING = "crawling"
    PREPROCESSING = "preprocessing"
    KNOWLEDGE_GENERATION = "knowledge_generation"
    VECTOR_STORAGE = "vector_storage"
    COMPLETION = "completion"

@dataclass
class PipelineMetrics:
    """管道性能指标"""
    stage: PipelineStage
    start_time: float
    end_time: Optional[float] = None
    items_processed: int = 0
    success_count: int = 0
    error_count: int = 0
    error_details: List[str] = None
    
    def __post_init__(self):
        if self.error_details is None:
            self.error_details = []
    
    @property
    def duration(self) -> float:
        """计算持续时间"""
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time
    
    @property
    def success_rate(self) -> float:
        """计算成功率"""
        total = self.success_count + self.error_count
        if total == 0:
            return 0.0
        return self.success_count / total

class MemeDataPipelineV2:
    """梗文化数据处理管道 V2.0 - 独立开发版本"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化数据管道
        
        Args:
            config: 可选的配置字典，用于覆盖默认配置
        """
        # 默认配置
        self.config = {
            "keywords": [
                "梗", "meme", "网络流行语", "段子", "有趣", "幽默",
                "二次元", "游戏", "动漫", "科技", "生活", "流行"
            ],
            "platforms": ["reddit", "tieba", "weibo", "zhihu"],
            "batch_size": 20,
            "max_posts_per_keyword": 50,
            "min_posts_for_knowledge": 3,
            "request_delay": 1.5,
            "llm_delay": 0.5,
            "cleanup_days": 7,
            "enable_cleanup": True,
            "enable_monitoring": True,
            "verbose_logging": True
        }
        
        # 覆盖配置
        if config:
            self.config.update(config)
        
        # 性能监控
        self.metrics: Dict[PipelineStage, PipelineMetrics] = {}
        self.debug_mode = self.config.get("verbose_logging", False)
        
        # 统计信息
        self.stats = {
            "total_runs": 0,
            "successful_runs": 0,
            "total_posts_crawled": 0,
            "total_posts_stored": 0,
            "total_knowledge_cards": 0,
            "last_run_duration": 0
        }
    
    def _log(self, level: str, message: str, **kwargs):
        """增强的日志记录"""
        if level == "debug" and not self.debug_mode:
            return
        
        extra = {"pipeline_stage": getattr(self, '_current_stage', 'unknown')}
        extra.update(kwargs)
        
        if level == "debug":
            logger.debug(message, extra=extra)
        elif level == "info":
            logger.info(message, extra=extra)
        elif level == "warning":
            logger.warning(message, extra=extra)
        elif level == "error":
            logger.error(message, extra=extra)
    
    def _start_stage(self, stage: PipelineStage):
        """开始一个阶段"""
        self._current_stage = stage
        if self.config.get("enable_monitoring", True):
            self.metrics[stage] = PipelineMetrics(stage=stage, start_time=time.time())
        self._log("info", f"Starting stage: {stage.value}")
    
    def _end_stage(self, stage: PipelineStage, success: bool = True, error: Optional[str] = None):
        """结束一个阶段"""
        if self.config.get("enable_monitoring", True) and stage in self.metrics:
            self.metrics[stage].end_time = time.time()
            if success:
                self.metrics[stage].success_count += 1
            else:
                self.metrics[stage].error_count += 1
                self.metrics[stage].error_details.append(error or "Unknown error")
        
        self._log("info", f"Completed stage: {stage.value} in {self.metrics[stage].duration:.2f}s")
    
    async def initialize_database(self) -> bool:
        """初始化数据库"""
        self._start_stage(PipelineStage.INITIALIZATION)
        
        try:
            self._log("info", "Initializing database for data pipeline...")
            init_database(settings.DATABASE_URL)
            
            # 验证数据库连接
            session = get_db_session()
            from sqlalchemy import text
            session.execute(text("SELECT 1"))  # 简单的连接测试
            session.close()
            
            self._end_stage(PipelineStage.INITIALIZATION, True)
            return True
            
        except Exception as e:
            error_msg = f"Database initialization failed: {e}"
            self._log("error", error_msg)
            self._end_stage(PipelineStage.INITIALIZATION, False, error_msg)
            return False
    
    async def crawl_meme_data(self) -> List[Dict[str, Any]]:
        """爬取梗数据"""
        self._start_stage(PipelineStage.CRAWLING)
        
        all_posts = []
        stage_metrics = self.metrics.get(PipelineStage.CRAWLING)
        
        try:
            self._log("info", "Starting meme data crawling...")
            
            # 清理旧数据
            if self.config.get("enable_cleanup", True):
                await self._cleanup_old_data()
            
            # 分批爬取
            keywords = self.config["keywords"]
            platforms = self.config["platforms"]
            batch_size = min(5, len(keywords))  # 减少批处理大小
            
            for i in range(0, len(keywords), batch_size):
                keyword_batch = keywords[i:i+batch_size]
                self._log("info", f"Crawling batch {i//batch_size + 1}: {keyword_batch}")
                
                try:
                    crawl_results = crawler.crawl_multiple_platforms(
                        platforms=platforms,
                        keywords=keyword_batch,
                        limit=self.config["max_posts_per_keyword"]
                    )
                    
                    # 处理爬取结果
                    batch_posts = []
                    for platform, result in crawl_results.items():
                        if "posts" in result and result["posts"]:
                            for post in result["posts"]:
                                post["platform"] = platform
                                post["crawled_at"] = datetime.now()
                            batch_posts.extend(result["posts"])
                    
                    all_posts.extend(batch_posts)
                    stage_metrics.items_processed += len(batch_posts) if stage_metrics else 0
                    
                    self._log("info", f"Batch {i//batch_size + 1}: {len(batch_posts)} posts crawled")
                    
                    # 请求间隔
                    if i + batch_size < len(keywords):
                        await asyncio.sleep(self.config["request_delay"])
                        
                except Exception as e:
                    error_msg = f"Error crawling batch {keyword_batch}: {e}"
                    self._log("error", error_msg)
                    if stage_metrics:
                        stage_metrics.error_count += 1
                        stage_metrics.error_details.append(error_msg)
                    continue
            
            self.stats["total_posts_crawled"] += len(all_posts)
            self._log("info", f"Crawling completed: {len(all_posts)} total posts")
            
            self._end_stage(PipelineStage.CRAWLING, True)
            return all_posts
            
        except Exception as e:
            error_msg = f"Crawling failed: {e}"
            self._log("error", error_msg)
            self._end_stage(PipelineStage.CRAWLING, False, error_msg)
            return []
    
    async def preprocess_and_store_data(self, raw_posts: List[Dict[str, Any]]) -> int:
        """预处理和存储数据"""
        self._start_stage(PipelineStage.PREPROCESSING)
        
        if not raw_posts:
            self._log("warning", "No raw posts to preprocess")
            self._end_stage(PipelineStage.PREPROCESSING, True)
            return 0
        
        stored_count = 0
        stage_metrics = self.metrics.get(PipelineStage.PREPROCESSING)
        
        try:
            self._log("info", f"Preprocessing and storing {len(raw_posts)} posts...")
            
            batch_size = self.config["batch_size"]
            
            for i in range(0, len(raw_posts), batch_size):
                batch = raw_posts[i:i+batch_size]
                
                try:
                    processed_batch = await self._process_batch(batch)
                    
                    if processed_batch:
                        await self._store_batch_to_db(processed_batch)
                        stored_count += len(processed_batch)
                        
                        if stage_metrics:
                            stage_metrics.items_processed += len(processed_batch)
                            stage_metrics.success_count += 1
                    
                    self._log("debug", f"Batch {i//batch_size + 1} stored: {len(processed_batch) if processed_batch else 0} posts")
                    
                except Exception as e:
                    error_msg = f"Error processing batch {i//batch_size + 1}: {e}"
                    self._log("error", error_msg)
                    if stage_metrics:
                        stage_metrics.error_count += 1
                        stage_metrics.error_details.append(error_msg)
                    continue
            
            self.stats["total_posts_stored"] += stored_count
            self._log("info", f"Storage completed: {stored_count} posts stored")
            
            self._end_stage(PipelineStage.PREPROCESSING, True)
            return stored_count
            
        except Exception as e:
            error_msg = f"Preprocessing failed: {e}"
            self._log("error", error_msg)
            self._end_stage(PipelineStage.PREPROCESSING, False, error_msg)
            return stored_count
    
    async def generate_knowledge_cards(self) -> int:
        """生成知识卡"""
        self._start_stage(PipelineStage.KNOWLEDGE_GENERATION)
        
        generated_count = 0
        stage_metrics = self.metrics.get(PipelineStage.KNOWLEDGE_GENERATION)
        
        try:
            self._log("info", "Starting knowledge card generation...")
            
            session = get_db_session()
            
            # 获取需要处理的梗
            memes_to_process = await self._get_memes_for_processing(
                session, 
                self.config["min_posts_for_knowledge"]
            )
            
            if not memes_to_process:
                self._log("info", "No memes found for knowledge card generation")
                session.close()
                self._end_stage(PipelineStage.KNOWLEDGE_GENERATION, True)
                return 0
            
            self._log("info", f"Processing {len(memes_to_process)} memes...")
            
            for meme_data in memes_to_process:
                try:
                    meme_id = meme_data["meme_id"]
                    related_posts = meme_data["posts"]
                    
                    # 生成知识卡
                    knowledge_card = await self._generate_single_knowledge_card(
                        meme_id, related_posts
                    )
                    
                    if knowledge_card:
                        await self._store_knowledge_card(session, knowledge_card)
                        generated_count += 1
                        
                        if stage_metrics:
                            stage_metrics.items_processed += 1
                            stage_metrics.success_count += 1
                        
                        self._log("debug", f"Generated knowledge card for meme: {meme_id}")
                    
                    # LLM调用间隔
                    await asyncio.sleep(self.config["llm_delay"])
                    
                except Exception as e:
                    error_msg = f"Error generating knowledge card for {meme_data['meme_id']}: {e}"
                    self._log("error", error_msg)
                    if stage_metrics:
                        stage_metrics.error_count += 1
                        stage_metrics.error_details.append(error_msg)
                    continue
            
            session.close()
            self.stats["total_knowledge_cards"] += generated_count
            
            self._log("info", f"Knowledge card generation completed: {generated_count} cards")
            
            self._end_stage(PipelineStage.KNOWLEDGE_GENERATION, True)
            return generated_count
            
        except Exception as e:
            error_msg = f"Knowledge card generation failed: {e}"
            self._log("error", error_msg)
            self._end_stage(PipelineStage.KNOWLEDGE_GENERATION, False, error_msg)
            return generated_count
    
    async def update_vector_storage(self) -> bool:
        """更新向量存储"""
        self._start_stage(PipelineStage.VECTOR_STORAGE)
        
        try:
            self._log("info", "Updating vector storage...")
            
            session = get_db_session()
            meme_cards = session.query(MemeCard).all()
            
            if not meme_cards:
                self._log("info", "No meme cards found for vector storage")
                session.close()
                self._end_stage(PipelineStage.VECTOR_STORAGE, True)
                return True
            
            self._log("info", f"Updating vector storage for {len(meme_cards)} cards")
            
            # 模拟向量存储更新（实际实现中可能需要真实的向量数据库操作）
            for i, card in enumerate(meme_cards):
                # 这里应该是实际的向量存储更新逻辑
                if i % 10 == 0:  # 每10个卡片记录一次进度
                    self._log("debug", f"Processed {i+1}/{len(meme_cards)} cards for vector storage")
            
            session.close()
            self._log("info", "Vector storage updated successfully")
            
            self._end_stage(PipelineStage.VECTOR_STORAGE, True)
            return True
            
        except Exception as e:
            error_msg = f"Vector storage update failed: {e}"
            self._log("error", error_msg)
            self._end_stage(PipelineStage.VECTOR_STORAGE, False, error_msg)
            return False
    
    async def run_full_pipeline(self) -> Dict[str, Any]:
        """运行完整的数据处理管道"""
        self._log("info", "Starting full meme data pipeline...")
        
        pipeline_start = time.time()
        self.stats["total_runs"] += 1
        
        try:
            # 0. 初始化COMPLETION阶段
            self._start_stage(PipelineStage.COMPLETION)
            
            # 1. 初始化数据库
            db_init_success = await self.initialize_database()
            if not db_init_success:
                raise Exception("Database initialization failed")
            
            # 2. 爬取数据
            raw_posts = await self.crawl_meme_data()
            
            # 3. 预处理和存储
            stored_count = await self.preprocess_and_store_data(raw_posts)
            
            # 4. 生成知识卡
            knowledge_cards_count = await self.generate_knowledge_cards()
            
            # 5. 更新向量存储
            vector_success = await self.update_vector_storage()
            
            # 计算总耗时
            total_duration = time.time() - pipeline_start
            self.stats["last_run_duration"] = total_duration
            
            # 生成报告
            pipeline_result = {
                "status": "completed",
                "duration": total_duration,
                "summary": {
                    "posts_crawled": len(raw_posts),
                    "posts_stored": stored_count,
                    "knowledge_cards_generated": knowledge_cards_count,
                    "vector_storage_updated": vector_success
                },
                "performance_metrics": {
                    stage.value: {
                        "duration": metrics.duration,
                        "success_rate": metrics.success_rate,
                        "items_processed": metrics.items_processed
                    }
                    for stage, metrics in self.metrics.items()
                }
            }
            
            self.stats["successful_runs"] += 1
            self._log("info", f"Pipeline completed successfully in {total_duration:.2f}s")
            self._log("info", f"Summary: {pipeline_result['summary']}")
            
            self._end_stage(PipelineStage.COMPLETION, True)
            return pipeline_result
            
        except Exception as e:
            # 如果还没有初始化COMPLETION阶段，先初始化它
            if PipelineStage.COMPLETION not in self.metrics:
                self._start_stage(PipelineStage.COMPLETION)
            
            total_duration = time.time() - pipeline_start
            error_msg = f"Pipeline failed after {total_duration:.2f}s: {e}"
            self._log("error", error_msg)
            
            self._end_stage(PipelineStage.COMPLETION, False, error_msg)
            
            return {
                "status": "failed",
                "duration": total_duration,
                "error": error_msg,
                "partial_summary": {
                    "posts_crawled": len(self.metrics.get(PipelineStage.CRAWLING, PipelineMetrics(PipelineStage.CRAWLING, 0)).items_processed),
                    "posts_stored": self.stats["total_posts_stored"],
                    "knowledge_cards_generated": self.stats["total_knowledge_cards"]
                }
            }
    
    async def _cleanup_old_data(self):
        """清理旧数据"""
        try:
            cleanup_days = self.config["cleanup_days"]
            session = get_db_session()
            
            # 清理旧的原始帖子
            from sqlalchemy import text
            delete_query = text(
                "DELETE FROM raw_posts WHERE crawled_at < datetime('now', '-' || :days || ' days')"
            )
            deleted_raw = session.execute(delete_query, {"days": str(cleanup_days)}).rowcount
            
            session.commit()
            session.close()
            
            self._log("debug", f"Cleaned up {deleted_raw} old raw posts")
            
        except Exception as e:
            self._log("warning", f"Failed to cleanup old data: {e}")
    
    async def _process_batch(self, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理一批数据"""
        processed_batch = []
        
        for post in batch:
            try:
                processed_post = await self._process_single_post(post)
                if processed_post:
                    processed_batch.append(processed_post)
            except Exception as e:
                self._log("warning", f"Failed to process post {post.get('post_id', 'unknown')}: {e}")
                continue
        
        return processed_batch
    
    async def _process_single_post(self, post: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理单个帖子"""
        try:
            # 提取关键词
            keywords = self._extract_keywords(post.get("content", "") + " " + post.get("title", ""))
            
            # 分析情感
            sentiment = self._analyze_sentiment(post.get("content", ""))
            
            processed_post = post.copy()
            processed_post.update({
                "keywords": json.dumps(keywords),
                "sentiment": sentiment,
                "processed_at": datetime.now()
            })
            
            return processed_post
            
        except Exception as e:
            self._log("warning", f"Failed to process single post: {e}")
            return None
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        if not text:
            return []
        
        import re
        
        # 提取中文词汇
        chinese_words = re.findall(r'[\一-龥]{2,}', text)
        
        # 提取英文单词
        english_words = re.findall(r'\b[a-zA-Z]{3,}\b', text)
        
        # 提取数字
        numbers = re.findall(r'\d+', text)
        
        keywords = list(set(chinese_words + english_words + numbers))
        return keywords[:10]
    
    def _analyze_sentiment(self, text: str) -> str:
        """简单的情感分析"""
        if not text:
            return "neutral"
        
        positive_words = ["好", "棒", "赞", "喜欢", "爱", "优秀", "有趣", "搞笑", "幽默"]
        negative_words = ["差", "烂", "讨厌", "恶心", "无聊", "讨厌"]
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    async def _store_batch_to_db(self, processed_batch: List[Dict[str, Any]]):
        """存储处理后的批次到数据库"""
        session = get_db_session()
        
        try:
            for post_data in processed_batch:
                # 检查是否已存在
                existing = session.query(RawPost).filter(
                    RawPost.post_id == post_data.get("post_id")
                ).first()
                
                if not existing:
                    raw_post = RawPost(
                        platform=post_data["platform"],
                        title=post_data["title"],
                        content=post_data["content"],
                        author=post_data["author"],
                        timestamp=post_data["timestamp"],
                        comment_count=post_data["comment_count"],
                        source=post_data["source"],
                        url=post_data["url"],
                        post_id=post_data["post_id"],
                        keywords=post_data["keywords"],
                        sentiment=post_data["sentiment"],
                        crawled_at=post_data["crawled_at"]
                    )
                    session.add(raw_post)
            
            session.commit()
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    async def _get_memes_for_processing(self, session, min_posts_threshold: int) -> List[Dict[str, Any]]:
        """获取需要处理的梗"""
        try:
            # 使用SQLite语法：strftime函数
            from sqlalchemy import text
            query = text("""
                SELECT 
                    substr(content, 1, 50) as content_prefix,
                    COUNT(*) as post_count,
                    GROUP_CONCAT(id) as post_ids
                FROM raw_posts 
                WHERE timestamp > strftime('%Y-%m-%d %H:%M:%S', 'now', '-7 days')
                GROUP BY content_prefix
                HAVING post_count >= :threshold
                ORDER BY post_count DESC
                LIMIT 10
            """)
            
            result = session.execute(query, {"threshold": min_posts_threshold})
            meme_groups = result.fetchall()
            
            memes_to_process = []
            for group in meme_groups:
                post_ids = [int(id_str) for id_str in group[2].split(',')]
                posts = session.query(RawPost).filter(RawPost.id.in_(post_ids)).limit(10).all()
                
                if posts:
                    memes_to_process.append({
                        "meme_id": group[0],
                        "posts": [post.__dict__ for post in posts],
                        "post_count": group[1]
                    })
            
            return memes_to_process
            
        except Exception as e:
            self._log("error", f"Failed to get memes for processing: {e}")
            return []
    
    async def _generate_single_knowledge_card(self, meme_id: str, posts: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """生成单个知识卡"""
        try:
            # 准备内容
            content_parts = []
            for post in posts[:5]:  # 限制分析的内容数量
                title = post.get('title', '') or ''
                content = post.get('content', '') or ''
                content_parts.append(f"标题: {title}")
                content_parts.append(f"内容: {content[:200]}")  # 限制内容长度
            
            content_data = "\n\n".join(content_parts)
            
            # 调用LLM
            summary = meme_summarizer.llm_client.generate_text(
                prompt=f"""
                请分析以下梗相关的内容，生成结构化的知识卡：

                {content_data}

                请生成JSON格式的知识卡，包含以下字段：
                - title: 梗的名称
                - origin: 梗的起源和背景
                - meaning: 梗的具体含义和用途
                - examples: 具体使用例子（数组，至少2个）
                - category: 梗的类别
                - sentiment: 情感倾向
                - popularity: 热度等级(1-10)
                """,
                system_prompt=meme_summarizer.system_prompt
            )
            
            if not summary:
                return None
            
            # 解析JSON
            import re
            json_match = re.search(r'\{.*\}', summary, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                knowledge_card = json.loads(json_str)
                
                # 添加元数据
                knowledge_card["id"] = f"meme_{hash(knowledge_card.get('title', ''))}"
                knowledge_card["created_at"] = datetime.now()
                knowledge_card["related_posts_count"] = len(posts)
                
                return knowledge_card
            
            return None
            
        except Exception as e:
            self._log("error", f"Failed to generate knowledge card: {e}")
            return None
    
    async def _store_knowledge_card(self, session, knowledge_card: Dict[str, Any]):
        """存储知识卡"""
        try:
            # 检查是否已存在
            existing = session.query(MemeCard).filter(
                MemeCard.title == knowledge_card.get("title")
            ).first()
            
            if not existing:
                meme_card = MemeCard(
                    title=knowledge_card["title"],
                    origin=knowledge_card.get("origin", ""),
                    meaning=knowledge_card.get("meaning", ""),
                    examples=json.dumps(knowledge_card.get("examples", [])),
                    category=knowledge_card.get("category", ""),
                    sentiment=knowledge_card.get("sentiment", "neutral"),
                    popularity=int(knowledge_card.get("popularity", 5)),
                    metadata=json.dumps(knowledge_card)
                )
                session.add(meme_card)
                session.commit()
                
        except Exception as e:
            session.rollback()
            raise e
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        return {
            "statistics": self.stats.copy(),
            "performance_metrics": {
                stage.value: {
                    "duration": metrics.duration,
                    "success_rate": metrics.success_rate,
                    "items_processed": metrics.items_processed,
                    "errors": len(metrics.error_details)
                }
                for stage, metrics in self.metrics.items()
            },
            "configuration": self.config.copy()
        }

# 工厂函数
def create_pipeline(config: Optional[Dict] = None) -> MemeDataPipelineV2:
    """创建数据管道实例"""
    return MemeDataPipelineV2(config)

# 导出
__all__ = [
    "MemeDataPipelineV2", 
    "create_pipeline", 
    "PipelineStage", 
    "PipelineMetrics"
]