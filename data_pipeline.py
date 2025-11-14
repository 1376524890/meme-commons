"""
meme-commons 数据处理管道
完整的数据链路：爬取 → 预处理 → 数据库存储 → LLM知识卡生成
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

from database.models import RawPost, MemeCard, TrendData, init_database, get_db_session
from tools.crawler import crawler
from tools.summarizer import meme_summarizer
from vector_store import vector_store
from config import settings

logger = logging.getLogger(__name__)

class MemeDataPipeline:
    """梗文化数据处理管道"""
    
    def __init__(self):
        self.default_keywords = [
            "梗", "meme", "网络流行语", "段子", "有趣", "幽默",
            "二次元", "游戏", "动漫", "科技", "生活", "流行",
            "笑话", "搞笑", "表情包", "沙雕", "趣味"
        ]
        
        self.target_platforms = [
            "reddit", "tieba", "weibo", "zhihu"
        ]
        
        self.batch_size = 50
        self.max_posts_per_keyword = 100
    
    async def initialize_database(self):
        """初始化数据库"""
        try:
            logger.info("Initializing database for data pipeline...")
            init_database(settings.DATABASE_URL)
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def crawl_meme_data(self) -> List[Dict[str, Any]]:
        """从互联网平台爬取梗相关信息"""
        try:
            logger.info("Starting meme data crawling...")
            all_posts = []
            
            # 清理旧数据（保留最近7天的数据）
            await self._cleanup_old_data(days=7)
            
            # 分批爬取数据
            keywords = self.default_keywords
            batch_size = 10
            
            for i in range(0, len(keywords), batch_size):
                keyword_batch = keywords[i:i+batch_size]
                logger.info(f"Crawling keyword batch {i//batch_size + 1}: {keyword_batch}")
                
                try:
                    # 爬取多个平台的梗数据
                    crawl_results = crawler.crawl_multiple_platforms(
                        platforms=self.target_platforms,
                        keywords=keyword_batch,
                        limit=self.max_posts_per_keyword
                    )
                    
                    # 整理爬取结果
                    for platform, result in crawl_results.items():
                        if "posts" in result:
                            posts = result["posts"]
                            for post in posts:
                                post["platform"] = platform
                                post["crawled_at"] = datetime.now()
                            all_posts.extend(posts)
                    
                    logger.info(f"Crawled {len(posts)} posts from {platform}")
                    
                    # 添加延迟避免被封
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error crawling keyword batch {keyword_batch}: {e}")
                    continue
            
            logger.info(f"Total crawled posts: {len(all_posts)}")
            return all_posts
            
        except Exception as e:
            logger.error(f"Failed to crawl meme data: {e}")
            return []
    
    async def preprocess_and_store_data(self, raw_posts: List[Dict[str, Any]]) -> int:
        """清洗预处理数据并存储到数据库"""
        if not raw_posts:
            logger.warning("No raw posts to preprocess")
            return 0
        
        try:
            logger.info(f"Preprocessing and storing {len(raw_posts)} posts...")
            stored_count = 0
            
            # 批量处理数据
            for i in range(0, len(raw_posts), self.batch_size):
                batch = raw_posts[i:i+self.batch_size]
                
                try:
                    processed_batch = await self._process_batch(batch)
                    
                    # 存储到数据库
                    await self._store_batch_to_db(processed_batch)
                    stored_count += len(processed_batch)
                    
                    logger.info(f"Stored batch {i//self.batch_size + 1}, total: {stored_count}")
                    
                except Exception as e:
                    logger.error(f"Error processing batch {i//self.batch_size + 1}: {e}")
                    continue
            
            logger.info(f"Successfully stored {stored_count} posts to database")
            return stored_count
            
        except Exception as e:
            logger.error(f"Failed to preprocess and store data: {e}")
            return 0
    
    async def generate_knowledge_cards(self, min_posts_threshold: int = 5) -> int:
        """使用LLM生成结构化知识卡"""
        try:
            logger.info("Starting knowledge card generation...")
            
            session = get_db_session()
            
            # 获取需要生成知识卡的梗
            memes_to_process = await self._get_memes_for_processing(session, min_posts_threshold)
            
            if not memes_to_process:
                logger.info("No memes found that need knowledge card generation")
                session.close()
                return 0
            
            logger.info(f"Found {len(memes_to_process)} memes for knowledge card generation")
            
            generated_count = 0
            
            for meme_data in memes_to_process:
                try:
                    meme_id = meme_data["meme_id"]
                    related_posts = meme_data["posts"]
                    
                    # 生成知识卡
                    knowledge_card = await self._generate_single_knowledge_card(
                        meme_id, related_posts
                    )
                    
                    if knowledge_card:
                        # 存储知识卡到数据库
                        await self._store_knowledge_card(session, knowledge_card)
                        generated_count += 1
                        
                        logger.info(f"Generated knowledge card for meme: {meme_id}")
                    
                    # 添加延迟避免API限流
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error generating knowledge card for meme {meme_data['meme_id']}: {e}")
                    continue
            
            session.close()
            logger.info(f"Successfully generated {generated_count} knowledge cards")
            return generated_count
            
        except Exception as e:
            logger.error(f"Failed to generate knowledge cards: {e}")
            return 0
    
    def crawl_platform(self, platform: str, keywords: List[str], limit: int) -> Dict[str, Any]:
        """
        根据指定平台、关键字和限制数量爬取数据
        这个方法是同步的，用于配合AutomationScheduler的线程池执行
        """
        import asyncio
        try:
            # 临时修改默认关键字和平台用于爬取
            original_keywords = self.default_keywords.copy()
            original_platforms = self.target_platforms.copy()
            
            # 设置新的参数
            self.default_keywords = keywords
            self.target_platforms = [platform]
            self.max_posts_per_keyword = limit // len(keywords) if keywords else limit
            
            # 创建新的事件循环来运行异步方法
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # 运行异步爬取方法
                raw_posts = loop.run_until_complete(self.crawl_meme_data())
                
                return {
                    "success": True,
                    "platform": platform,
                    "keywords": keywords,
                    "limit": limit,
                    "crawled_count": len(raw_posts),
                    "crawl_results": raw_posts
                }
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"爬取平台 {platform} 失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "platform": platform,
                "crawled_count": 0,
                "crawl_results": []
            }
        finally:
            # 恢复原始参数
            self.default_keywords = original_keywords
            self.target_platforms = original_platforms

    async def update_vector_storage(self):
        """更新向量存储"""
        try:
            logger.info("Updating vector storage...")
            
            session = get_db_session()
            
            # 获取所有知识卡
            meme_cards = session.query(MemeCard).all()
            
            if not meme_cards:
                logger.info("No meme cards found for vector storage")
                session.close()
                return
            
            # 批量更新向量存储
            card_data = []
            for card in meme_cards:
                card_info = {
                    "id": card.id,
                    "title": card.title,
                    "origin": card.origin,
                    "meaning": card.meaning,
                    "category": card.category,
                    "content": f"{card.title} {card.origin} {card.meaning}"
                }
                card_data.append(card_info)
            
            # 更新向量存储
            vector_store.add_documents(card_data)
            
            session.close()
            logger.info(f"Updated vector storage with {len(card_data)} knowledge cards")
            
        except Exception as e:
            logger.error(f"Failed to update vector storage: {e}")
    
    async def run_full_pipeline(self) -> Dict[str, Any]:
        """运行完整的数据处理管道"""
        try:
            logger.info("Starting full meme data processing pipeline...")
            pipeline_start_time = datetime.now()
            
            pipeline_results = {
                "start_time": pipeline_start_time.isoformat(),
                "steps": {}
            }
            
            # 步骤1: 爬取数据
            logger.info("=== Step 1: Crawling meme data ===")
            step1_start = datetime.now()
            raw_posts = await self.crawl_meme_data()
            pipeline_results["steps"]["crawl"] = {
                "start_time": step1_start.isoformat(),
                "end_time": datetime.now().isoformat(),
                "posts_crawled": len(raw_posts),
                "status": "success"
            }
            
            # 步骤2: 预处理和存储
            logger.info("=== Step 2: Preprocessing and storage ===")
            step2_start = datetime.now()
            stored_count = await self.preprocess_and_store_data(raw_posts)
            pipeline_results["steps"]["preprocess"] = {
                "start_time": step2_start.isoformat(),
                "end_time": datetime.now().isoformat(),
                "posts_stored": stored_count,
                "status": "success"
            }
            
            # 步骤3: 生成知识卡
            logger.info("=== Step 3: Generating knowledge cards ===")
            step3_start = datetime.now()
            cards_generated = await self.generate_knowledge_cards()
            pipeline_results["steps"]["knowledge_cards"] = {
                "start_time": step3_start.isoformat(),
                "end_time": datetime.now().isoformat(),
                "cards_generated": cards_generated,
                "status": "success"
            }
            
            # 步骤4: 更新向量存储
            logger.info("=== Step 4: Updating vector storage ===")
            step4_start = datetime.now()
            await self.update_vector_storage()
            pipeline_results["steps"]["vector_storage"] = {
                "start_time": step4_start.isoformat(),
                "end_time": datetime.now().isoformat(),
                "status": "success"
            }
            
            # 完成统计
            pipeline_end_time = datetime.now()
            pipeline_results["end_time"] = pipeline_end_time.isoformat()
            pipeline_results["total_duration"] = str(pipeline_end_time - pipeline_start_time)
            pipeline_results["summary"] = {
                "posts_crawled": len(raw_posts),
                "posts_stored": stored_count,
                "knowledge_cards_generated": cards_generated,
                "status": "completed"
            }
            
            logger.info(f"Pipeline completed successfully! Duration: {pipeline_results['total_duration']}")
            logger.info(f"Summary: {len(raw_posts)} crawled, {stored_count} stored, {cards_generated} knowledge cards generated")
            
            return pipeline_results
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "start_time": datetime.now().isoformat(),
                "end_time": datetime.now().isoformat()
            }
    
    # 辅助方法
    
    async def _cleanup_old_data(self, days: int = 7):
        """清理旧数据"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            session = get_db_session()
            
            # 删除过期的RawPost
            deleted_raw = session.query(RawPost).filter(
                RawPost.timestamp < cutoff_date
            ).delete()
            
            # 删除没有关联MemeCard的过期数据
            deleted_cards = session.query(MemeCard).filter(
                MemeCard.created_at < cutoff_date
            ).delete()
            
            session.commit()
            session.close()
            
            logger.info(f"Cleaned up old data: {deleted_raw} RawPosts, {deleted_cards} MemeCards")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
    
    async def _process_batch(self, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理一批数据"""
        processed_batch = []
        
        for post in batch:
            try:
                # 清洗文本
                cleaned_content = self._clean_content(post.get("content", ""))
                cleaned_title = self._clean_content(post.get("title", ""))
                
                # 提取关键词
                keywords = self._extract_keywords(f"{cleaned_title} {cleaned_content}")
                
                processed_post = {
                    "platform": post.get("platform", "unknown"),
                    "title": cleaned_title or "无标题",
                    "content": cleaned_content,
                    "author": post.get("author", "匿名用户"),
                    "timestamp": post.get("timestamp", datetime.now()),
                    "comment_count": post.get("comment_count", 0),
                    "source": post.get("source", ""),
                    "url": post.get("url", ""),
                    "post_id": post.get("post_id", ""),
                    "crawled_at": post.get("crawled_at", datetime.now()),
                    "keywords": keywords,
                    "sentiment": self._analyze_sentiment(f"{cleaned_title} {cleaned_content}")
                }
                
                processed_batch.append(processed_post)
                
            except Exception as e:
                logger.warning(f"Error processing post: {e}")
                continue
        
        return processed_batch
    
    def _clean_content(self, content: str) -> str:
        """清洗文本内容"""
        if not content:
            return ""
        
        # 移除多余空白
        content = " ".join(content.split())
        
        # 移除HTML标签
        import re
        content = re.sub(r'<[^>]+>', '', content)
        
        # 限制长度
        return content[:2000]
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        if not text:
            return []
        
        # 简单的关键词提取（可以后续改进）
        import re
        
        # 提取中文词汇
        chinese_words = re.findall(r'[\一-龥]{2,}', text)
        
        # 提取英文单词
        english_words = re.findall(r'\b[a-zA-Z]{3,}\b', text)
        
        # 提取数字
        numbers = re.findall(r'\d+', text)
        
        keywords = list(set(chinese_words + english_words + numbers))
        return keywords[:10]  # 限制关键词数量
    
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
        """将处理后的数据存储到数据库"""
        try:
            session = get_db_session()
            
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
                        keywords=json.dumps(post_data["keywords"]),
                        sentiment=post_data["sentiment"],
                        crawled_at=post_data["crawled_at"]
                    )
                    session.add(raw_post)
            
            session.commit()
            session.close()
            
        except Exception as e:
            logger.error(f"Failed to store batch to database: {e}")
            session.rollback()
            session.close()
            raise
    
    async def _get_memes_for_processing(self, session, min_posts_threshold: int) -> List[Dict[str, Any]]:
        """获取需要生成知识卡的梗"""
        try:
            # 按内容相似度分组帖子
            query = """
            SELECT 
                substr(content, 1, 100) as content_prefix,
                COUNT(*) as post_count,
                GROUP_CONCAT(id) as post_ids
            FROM raw_posts 
            WHERE timestamp > datetime('now', '-7 days')
            GROUP BY content_prefix
            HAVING post_count >= ?
            ORDER BY post_count DESC
            LIMIT 20
            """
            
            result = session.execute(query, (min_posts_threshold,))
            meme_groups = result.fetchall()
            
            memes_to_process = []
            for group in meme_groups:
                # 获取该组的帖子
                posts = session.query(RawPost).filter(
                    RawPost.id.in_(group[2].split(','))
                ).limit(20).all()
                
                if posts:
                    memes_to_process.append({
                        "meme_id": group[0],
                        "posts": [post.__dict__ for post in posts],
                        "post_count": group[1]
                    })
            
            return memes_to_process
            
        except Exception as e:
            logger.error(f"Failed to get memes for processing: {e}")
            return []
    
    async def _generate_single_knowledge_card(self, meme_id: str, posts: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """生成单个知识卡"""
        try:
            # 准备内容用于LLM分析
            content_parts = []
            for post in posts[:10]:  # 限制用于分析的内容数量
                content_parts.append(f"标题: {post.get('title', '')}")
                content_parts.append(f"内容: {post.get('content', '')}")
            
            content_data = "\n\n".join(content_parts)
            
            # 调用LLM生成知识卡
            summary = meme_summarizer.llm_client.generate_text(
                prompt=f"""
                请分析以下梗相关的内容，生成结构化的知识卡：

                {content_data}

                请生成JSON格式的知识卡，包含以下字段：
                - title: 梗的名称
                - origin: 梗的起源和背景
                - meaning: 梗的具体含义和用途
                - examples: 具体使用例子（数组）
                - category: 梗的类别
                - sentiment: 情感倾向
                - popularity: 热度等级(1-10)
                """,
                system_prompt=meme_summarizer.system_prompt
            )
            
            if not summary:
                logger.error("Failed to generate summary for meme")
                return None
            
            # 解析LLM输出
            try:
                # 提取JSON部分
                import re
                json_match = re.search(r'\{.*\}', summary, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    knowledge_card = json.loads(json_str)
                    
                    # 添加元数据
                    knowledge_card["id"] = f"meme_{len(knowledge_card.get('title', ''))}_{hash(knowledge_card.get('title', ''))}"
                    knowledge_card["created_at"] = datetime.now()
                    knowledge_card["related_posts_count"] = len(posts)
                    
                    return knowledge_card
                else:
                    logger.error("No JSON found in LLM output")
                    return None
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from LLM output: {e}")
                return None
            
        except Exception as e:
            logger.error(f"Failed to generate knowledge card: {e}")
            return None
    
    async def _store_knowledge_card(self, session, knowledge_card: Dict[str, Any]):
        """存储知识卡到数据库"""
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
            logger.error(f"Failed to store knowledge card: {e}")
            session.rollback()
            raise


# 全局数据管道实例
data_pipeline = MemeDataPipeline()