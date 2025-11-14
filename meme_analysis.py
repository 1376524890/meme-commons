"""
AI分析总结引擎
使用LLM从清洗后的数据中提取关键信息，生成结构化知识卡
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from config import settings
from database.models import get_db_session, MemeCard
from data_cleaner import data_cleaner

logger = logging.getLogger(__name__)

class MemeAnalysisEngine:
    """梗文化AI分析总结引擎"""
    
    def __init__(self):
        self.analysis_prompt_template = self._load_analysis_prompt()
        self.summary_prompt_template = self._load_summary_prompt()
        self.knowledge_card_template = self._load_knowledge_card_template()
    
    def _load_analysis_prompt(self) -> str:
        """加载分析提示模板"""
        return """
你是一个专业的梗文化分析专家。请分析以下梗相关的内容，并提供结构化的分析结果。

内容类型：{meme_type}
分析内容：
{content}

请从以下维度进行分析：
1. **梗的起源和背景**：这个梗是什么时候出现的？起源平台是什么？
2. **核心含义**：这个梗的主要意思是什么？
3. **使用场景**：在什么情况下会使用这个梗？
4. **情感色彩**：正面、负面还是中性？
5. **流行程度**：从1-10评分，这个梗的流行程度如何？
6. **目标群体**：主要在什么人群中流行？
7. **传播途径**：主要通过什么方式传播？
8. **相关变体**：这个梗是否有其他变体或衍生形式？

请以JSON格式返回分析结果，格式如下：
{{
    "origin": "梗的起源描述",
    "core_meaning": "核心含义描述", 
    "usage_scenarios": ["场景1", "场景2"],
    "sentiment": "positive/negative/neutral",
    "popularity_score": 8,
    "target_demographics": ["群体1", "群体2"],
    "transmission_channels": ["渠道1", "渠道2"],
    "variants": ["变体1", "变体2"],
    "analysis_confidence": 0.8,
    "key_insights": ["洞察1", "洞察2"]
}}
"""

    def _load_summary_prompt(self) -> str:
        """加载总结提示模板"""
        return """
你是一个梗文化专家。请基于以下多个相关内容，为梗"{meme_title}"生成一个简洁而全面的总结。

相关内容：
{content_samples}

要求：
1. 提供梗的准确定义（1-2句话）
2. 列出3-5个典型使用场景
3. 说明情感色彩和受众群体
4. 提供1-2个经典例句或使用方式
5. 评估当前流行程度（1-10分）

输出格式要求简洁明了，适合制作知识卡片。
"""

    def _load_knowledge_card_template(self) -> str:
        """加载知识卡模板"""
        return {
            "title": "",           # 梗的名称
            "origin": "",          # 梗的起源
            "meaning": "",         # 梗的含义
            "examples": [],        # 使用示例
            "trend_score": 0.0,    # 趋势分数
            "categories": [],      # 分类标签
            "platforms": [],       # 主要平台
            "demographics": [],    # 目标群体
            "sentiment": "",       # 情感色彩
            "popularity": 0,       # 流行程度
            "first_seen": None,    # 首次出现时间
            "last_updated": None,  # 最后更新时间
            "confidence": 0.0,     # 分析置信度
            "metadata": {}         # 其他元数据
        }
    
    async def analyze_single_meme(self, cleaned_post: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """分析单个梗内容"""
        try:
            content = cleaned_post.get('content', '')
            meme_type = cleaned_post.get('meme_type', 'general')
            
            if not content:
                return None
            
            # 构建分析提示
            prompt = self.analysis_prompt_template.format(
                meme_type=meme_type,
                content=content[:1000]  # 限制内容长度
            )
            
            # 这里应该调用实际的LLM API
            # 为了演示，我们使用模拟的分析结果
            analysis_result = await self._simulate_llm_analysis(content, meme_type)
            
            if analysis_result:
                # 合并原始数据和LLM分析结果
                combined_result = {
                    **cleaned_post,
                    'llm_analysis': analysis_result,
                    'analyzed_at': datetime.now()
                }
                
                return combined_result
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing meme content: {e}")
            return None
    
    async def batch_analyze_memes(self, cleaned_posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量分析梗内容"""
        analyzed_results = []
        
        logger.info(f"Starting batch analysis of {len(cleaned_posts)} posts")
        
        for i, post in enumerate(cleaned_posts):
            try:
                analyzed = await self.analyze_single_meme(post)
                if analyzed:
                    analyzed_results.append(analyzed)
                
                # 添加进度日志
                if (i + 1) % 10 == 0:
                    logger.info(f"Processed {i + 1}/{len(cleaned_posts)} posts")
                
                # 添加延迟避免API限流
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error analyzing post {post.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Completed analysis of {len(analyzed_results)} posts")
        return analyzed_results
    
    async def generate_knowledge_card(self, analyzed_posts: List[Dict[str, Any]], 
                                    min_posts_threshold: int = 3) -> Optional[Dict[str, Any]]:
        """生成结构化知识卡"""
        if len(analyzed_posts) < min_posts_threshold:
            logger.warning(f"Not enough posts ({len(analyzed_posts)}) for knowledge card generation")
            return None
        
        try:
            # 基于关键词聚类确定梗的标题
            all_keywords = []
            for post in analyzed_posts:
                all_keywords.extend(post.get('keywords', []))
            
            # 获取最频繁的关键词作为梗标题
            keyword_freq = {}
            for keyword in all_keywords:
                keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
            
            top_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)
            meme_title = top_keywords[0][0] if top_keywords else "未知梗"
            
            # 收集使用示例
            examples = []
            for post in analyzed_posts[:5]:  # 取前5个作为示例
                content = post.get('content', '')[:100]
                if content:
                    examples.append(content)
            
            # 计算趋势分数
            trend_score = self._calculate_trend_score(analyzed_posts)
            
            # 统计情感分布
            sentiment_distribution = {}
            for post in analyzed_posts:
                sentiment = post.get('sentiment', {}).get('sentiment', 'neutral')
                sentiment_distribution[sentiment] = sentiment_distribution.get(sentiment, 0) + 1
            
            # 确定主要情感
            main_sentiment = max(sentiment_distribution.items(), key=lambda x: x[1])[0]
            
            # 统计平台分布
            platforms = list(set(post.get('platform', '') for post in analyzed_posts))
            
            # 计算平均质量分数
            quality_scores = [post.get('quality_score', 0) for post in analyzed_posts]
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
            
            # 计算置信度
            confidence = min(1.0, len(analyzed_posts) / 10)  # 基于样本数量
            
            # 生成知识卡
            knowledge_card = {
                "title": meme_title,
                "origin": self._extract_origin_info(analyzed_posts),
                "meaning": self._generate_meaning_description(analyzed_posts, meme_title),
                "examples": examples,
                "trend_score": trend_score,
                "categories": self._extract_categories(analyzed_posts),
                "platforms": platforms,
                "demographics": self._infer_demographics(analyzed_posts),
                "sentiment": main_sentiment,
                "popularity": int(trend_score * 10),  # 1-10评分
                "first_seen": min(post.get('timestamp') for post in analyzed_posts if post.get('timestamp')),
                "last_updated": max(post.get('timestamp') for post in analyzed_posts if post.get('timestamp')),
                "confidence": confidence,
                "metadata": {
                    "sample_size": len(analyzed_posts),
                    "avg_quality_score": avg_quality,
                    "sentiment_distribution": sentiment_distribution,
                    "platforms_count": len(platforms),
                    "generated_at": datetime.now().isoformat()
                }
            }
            
            return knowledge_card
            
        except Exception as e:
            logger.error(f"Error generating knowledge card: {e}")
            return None
    
    async def generate_batch_knowledge_cards(self, analyzed_posts_list: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """批量生成知识卡"""
        knowledge_cards = []
        
        for i, analyzed_posts in enumerate(analyzed_posts_list):
            try:
                card = await self.generate_knowledge_card(analyzed_posts)
                if card:
                    knowledge_cards.append(card)
                
                logger.info(f"Generated knowledge card {i + 1}/{len(analyzed_posts_list)}")
                
            except Exception as e:
                logger.error(f"Error generating knowledge card for batch {i}: {e}")
                continue
        
        logger.info(f"Successfully generated {len(knowledge_cards)} knowledge cards")
        return knowledge_cards
    
    async def _simulate_llm_analysis(self, content: str, meme_type: str) -> Optional[Dict[str, Any]]:
        """模拟LLM分析（实际应该调用LLM API）"""
        # 这里模拟基于规则的简单分析
        # 实际应用中应该调用LLM API（如GPT、Claude等）
        
        # 简单的关键词匹配分析
        if "梗" in content or "meme" in content.lower():
            return {
                "origin": "网络平台起源，具体时间不详",
                "core_meaning": f"这是一个{meme_type}类型的梗",
                "usage_scenarios": ["日常聊天", "社交媒体", "评论区"],
                "sentiment": "neutral",
                "popularity_score": 7,
                "target_demographics": ["年轻网民", "网络原住民"],
                "transmission_channels": ["社交媒体", "即时通讯", "论坛"],
                "variants": ["原始形式", "变体形式"],
                "analysis_confidence": 0.6,
                "key_insights": ["在年轻人中流行", "传播性强"]
            }
        
        return None
    
    def _calculate_trend_score(self, analyzed_posts: List[Dict[str, Any]]) -> float:
        """计算趋势分数"""
        if not analyzed_posts:
            return 0.0
        
        # 基于多个因素计算趋势分数
        total_engagement = 0
        total_quality = 0
        recency_factor = 0
        platform_bonus = 0
        
        for post in analyzed_posts:
            # 参与度分数
            engagement = post.get('engagement', {}).get('engagement_score', 0)
            total_engagement += engagement
            
            # 质量分数
            quality = post.get('quality_score', 0)
            total_quality += quality
            
            # 时间新鲜度
            timestamp = post.get('timestamp')
            if timestamp:
                hours_old = (datetime.now() - timestamp).total_seconds() / 3600
                if hours_old <= 24:
                    recency_factor += 1.0
                elif hours_old <= 168:  # 一周内
                    recency_factor += 0.5
                else:
                    recency_factor += 0.1
            
            # 平台加成
            platform = post.get('platform', '')
            if platform in ['bilibili', 'weibo', 'douyin']:
                platform_bonus += 0.2
        
        # 综合计算趋势分数
        avg_engagement = total_engagement / len(analyzed_posts)
        avg_quality = total_quality / len(analyzed_posts)
        recency_score = recency_factor / len(analyzed_posts)
        platform_score = min(1.0, platform_bonus / len(analyzed_posts))
        
        trend_score = (avg_engagement * 0.4 + avg_quality * 0.3 + recency_score * 0.2 + platform_score * 0.1)
        
        return min(1.0, trend_score)
    
    def _extract_origin_info(self, analyzed_posts: List[Dict[str, Any]]) -> str:
        """提取起源信息"""
        # 统计平台出现频率
        platform_count = {}
        for post in analyzed_posts:
            platform = post.get('platform', '')
            if platform:
                platform_count[platform] = platform_count.get(platform, 0) + 1
        
        if platform_count:
            main_platform = max(platform_count.items(), key=lambda x: x[1])[0]
            return f"主要起源于{main_platform}平台"
        
        return "网络平台起源，具体来源不详"
    
    def _generate_meaning_description(self, analyzed_posts: List[Dict[str, Any]], title: str) -> str:
        """生成含义描述"""
        # 基于内容分析生成描述
        content_samples = [post.get('content', '')[:50] for post in analyzed_posts[:3]]
        
        if content_samples:
            return f"'{title}'是一个流行的网络梗，主要用于{', '.join(content_samples[:2])}等场景的表达。"
        
        return f"'{title}'是一个网络流行梗，具体含义需要结合具体使用场景来理解。"
    
    def _extract_categories(self, analyzed_posts: List[Dict[str, Any]]) -> List[str]:
        """提取分类标签"""
        categories = set()
        
        for post in analyzed_posts:
            meme_type = post.get('meme_type', 'general')
            if meme_type != 'general':
                categories.add(meme_type)
            
            # 基于关键词提取更多分类
            keywords = post.get('keywords', [])
            for keyword in keywords:
                if keyword in ['搞笑', '幽默', '段子']:
                    categories.add('搞笑娱乐')
                elif keyword in ['二次元', '动漫']:
                    categories.add('二次元文化')
                elif keyword in ['游戏', '电竞']:
                    categories.add('游戏相关')
        
        return list(categories)
    
    def _infer_demographics(self, analyzed_posts: List[Dict[str, Any]]) -> List[str]:
        """推断目标群体"""
        demographics = set()
        
        # 基于内容分析目标群体
        for post in analyzed_posts:
            content = post.get('content', '').lower()
            
            if any(word in content for word in ['学生', '校园', '考试']):
                demographics.add('学生群体')
            
            if any(word in content for word in ['工作', '职场', '老板']):
                demographics.add('职场人群')
            
            if any(word in content for word in ['游戏', '电竞', '队友']):
                demographics.add('游戏玩家')
            
            if any(word in content for word in ['二次元', '动漫', '番剧']):
                demographics.add('二次元爱好者')
        
        # 默认群体
        if not demographics:
            demographics.add('年轻网民')
        
        return list(demographics)
    
    async def save_knowledge_card_to_db(self, knowledge_card: Dict[str, Any]) -> bool:
        """保存知识卡到数据库"""
        try:
            session = get_db_session()
            
            # 检查是否已存在相同标题的知识卡
            existing_card = session.query(MemeCard).filter(
                MemeCard.title == knowledge_card['title']
            ).first()
            
            if existing_card:
                # 更新现有知识卡
                existing_card.origin = knowledge_card['origin']
                existing_card.meaning = knowledge_card['meaning']
                existing_card.examples = json.dumps(knowledge_card['examples'], ensure_ascii=False)
                existing_card.trend_score = knowledge_card['trend_score']
                existing_card.last_updated = datetime.now()
            else:
                # 创建新的知识卡
                new_card = MemeCard(
                    title=knowledge_card['title'],
                    origin=knowledge_card['origin'],
                    meaning=knowledge_card['meaning'],
                    examples=json.dumps(knowledge_card['examples'], ensure_ascii=False),
                    trend_score=knowledge_card['trend_score']
                )
                session.add(new_card)
            
            session.commit()
            session.close()
            
            logger.info(f"Successfully saved knowledge card: {knowledge_card['title']}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving knowledge card to database: {e}")
            return False
    
    async def batch_save_knowledge_cards(self, knowledge_cards: List[Dict[str, Any]]) -> int:
        """批量保存知识卡"""
        saved_count = 0
        
        for card in knowledge_cards:
            try:
                if await self.save_knowledge_card_to_db(card):
                    saved_count += 1
                
                await asyncio.sleep(0.1)  # 添加延迟
                
            except Exception as e:
                logger.error(f"Error saving knowledge card: {e}")
                continue
        
        logger.info(f"Successfully saved {saved_count}/{len(knowledge_cards)} knowledge cards")
        return saved_count

# 全局实例
meme_analysis_engine = MemeAnalysisEngine()