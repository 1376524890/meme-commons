"""
梗文化数据清洗模块
实现完整的数据清洗和预处理流程
"""
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib
import jieba
import jieba.analyse
from urllib.parse import urlparse
import json

from database.models import RawPost

logger = logging.getLogger(__name__)

class MemeDataCleaner:
    """梗文化数据清洗器"""
    
    def __init__(self):
        # 初始化jieba分词
        self._init_jieba()
        
        # 梗相关的停用词
        self.stopwords = {
            "的", "是", "了", "在", "有", "和", "就", "都", "而", "及", "与", "或",
            "一个", "这个", "那个", "什么", "怎么", "为什么", "如何", "多少",
            "很", "非常", "太", "真", "确实", "真的", "感觉", "觉得", "看起来",
            "说", "看", "听", "想", "知道", "了解", "明白", "理解",
            "吧", "呢", "啊", "哦", "额", "呃", "嗯", "额", "诶"
        }
        
        # 梗识别关键词
        self.meme_keywords = {
            "流行语": ["梗", "meme", "网络用语", "流行语", "口头禅", "网络梗"],
            "表情包": ["表情包", "表情", "emoji", "滑稽", "狗头", "保命"],
            "视频梗": ["视频", "片段", "剪辑", "鬼畜", "鬼畜视频", "魔性"],
            "文字梗": ["段子", "笑话", "搞笑", "幽默", "沙雕", "有趣"],
            "二次元": ["二次元", "动漫", "番剧", "萌", "可爱", "老婆", "老公"],
            "游戏": ["游戏", "电竞", "队友", "猪队友", "神操作", "菜"],
            "网络文化": ["网络文化", "网络流行", "当代青年", "精神小伙", "社会"]
        }
        
        # 情感词汇
        self.sentiment_words = {
            "positive": ["赞", "好", "棒", "优秀", "厉害", "666", "牛", "爱了", "太棒了"],
            "negative": ["垃圾", "差", "烂", "不行", "讨厌", "恶心", "想吐", "受不了"],
            "neutral": ["一般", "普通", "还行", "凑合", "马马虎虎"]
        }
    
    def _init_jieba(self):
        """初始化jieba分词词典"""
        # 添加网络用语到词典
        jieba.add_word("梗", tag='n')
        jieba.add_word("meme", tag='n')
        jieba.add_word("表情包", tag='n')
        jieba.add_word("沙雕", tag='n')
        jieba.add_word("魔性", tag='adj')
        jieba.add_word("鬼畜", tag='n')
        jieba.add_word("二次元", tag='n')
        jieba.add_word("精神小伙", tag='n')
        jieba.add_word("社会语录", tag='n')
        
        # 加载停用词文件（如果有）
        try:
            with open("data/stopwords.txt", "r", encoding="utf-8") as f:
                custom_stopwords = [line.strip() for line in f if line.strip()]
                self.stopwords.update(custom_stopwords)
        except FileNotFoundError:
            logger.info("Using default stopwords")
    
    def clean_raw_post(self, raw_post: RawPost) -> Dict[str, Any]:
        """清洗单个原始帖子"""
        try:
            cleaned_data = {
                "id": raw_post.id,
                "platform": raw_post.platform,
                "url": raw_post.url,
                "content": self._clean_content(raw_post.content),
                "title": self._clean_title(raw_post.title) if raw_post.title else "",
                "author": self._clean_author(raw_post.author) if raw_post.author else "",
                "timestamp": raw_post.timestamp,
                "engagement": self._calculate_engagement(raw_post),
                "sentiment": self._analyze_sentiment(raw_post.content),
                "keywords": self._extract_keywords(raw_post.content),
                "meme_type": self._identify_meme_type(raw_post.content),
                "quality_score": self._calculate_quality_score(raw_post),
                "processed_at": datetime.now()
            }
            
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Error cleaning raw post {raw_post.id}: {e}")
            return None
    
    def clean_batch_posts(self, raw_posts: List[RawPost]) -> List[Dict[str, Any]]:
        """批量清洗帖子数据"""
        cleaned_posts = []
        
        for post in raw_posts:
            cleaned = self.clean_raw_post(post)
            if cleaned:
                cleaned_posts.append(cleaned)
        
        logger.info(f"Cleaned {len(cleaned_posts)} out of {len(raw_posts)} posts")
        return cleaned_posts
    
    def _clean_content(self, content: str) -> str:
        """清洗内容文本"""
        if not content:
            return ""
        
        # 移除URL
        content = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', content)
        
        # 移除@用户名
        content = re.sub(r'@[\\w]+', '', content)
        
        # 移除话题标签
        content = re.sub(r'#([^#]+)#', r'\\1', content)
        
        # 移除多余的空白字符
        content = re.sub(r'\\s+', ' ', content)
        
        # 移除表情符号的特殊字符（保留基本标点）
        content = re.sub(r'[🎉🎊🎈🎁🎂🎄🎅🎆🎇🌟⭐💫✨🚀🎯🎪🎭🎨🎬🎵🎶🎼🎹🎸🥁🎤🎧]', '', content)
        
        # 移除重复的标点符号
        content = re.sub(r'([!?.。]{2,})', lambda m: m.group(1)[0], content)
        
        return content.strip()
    
    def _clean_title(self, title: str) -> str:
        """清洗标题"""
        if not title:
            return ""
        
        # 移除过长的标题
        if len(title) > 100:
            title = title[:97] + "..."
        
        # 移除特殊符号
        title = re.sub(r'[📌📍🔥💯👑🎯🎊]', '', title)
        
        return title.strip()
    
    def _clean_author(self, author: str) -> str:
        """清洗作者信息"""
        if not author:
            return ""
        
        # 移除特殊前缀
        author = re.sub(r'^(用户|用户|网友|博主|UP主|作者|账号)[::：]?', '', author)
        
        # 移除多余空格
        author = re.sub(r'\\s+', ' ', author)
        
        return author.strip()
    
    def _calculate_engagement(self, raw_post: RawPost) -> Dict[str, Any]:
        """计算参与度指标"""
        # 计算参与率
        total_interactions = (
            raw_post.like_count + 
            raw_post.comment_count + 
            raw_post.share_count +
            raw_post.upvotes - raw_post.downvotes
        )
        
        # 参与度分数（0-1之间）
        engagement_score = min(1.0, total_interactions / 1000.0)
        
        return {
            "like_count": raw_post.like_count,
            "comment_count": raw_post.comment_count,
            "share_count": raw_post.share_count,
            "upvotes": raw_post.upvotes,
            "downvotes": raw_post.downvotes,
            "total_interactions": total_interactions,
            "engagement_score": engagement_score
        }
    
    def _analyze_sentiment(self, content: str) -> Dict[str, Any]:
        """分析情感倾向"""
        if not content:
            return {"sentiment": "neutral", "score": 0.0}
        
        positive_count = 0
        negative_count = 0
        
        # 计算正面和负面词汇数量
        for word in self.sentiment_words["positive"]:
            positive_count += content.count(word)
        
        for word in self.sentiment_words["negative"]:
            negative_count += content.count(word)
        
        # 计算情感分数
        total_sentiment_words = positive_count + negative_count
        if total_sentiment_words == 0:
            sentiment_score = 0.0
            sentiment = "neutral"
        else:
            sentiment_score = (positive_count - negative_count) / total_sentiment_words
            if sentiment_score > 0.1:
                sentiment = "positive"
            elif sentiment_score < -0.1:
                sentiment = "negative"
            else:
                sentiment = "neutral"
        
        return {
            "sentiment": sentiment,
            "score": sentiment_score,
            "positive_indicators": positive_count,
            "negative_indicators": negative_count
        }
    
    def _extract_keywords(self, content: str, top_k: int = 10) -> List[str]:
        """提取关键词"""
        if not content:
            return []
        
        # 使用jieba分词
        words = jieba.cut(content)
        
        # 过滤停用词和短词
        filtered_words = [
            word for word in words 
            if len(word) >= 2 and word not in self.stopwords
        ]
        
        # 计算词频
        word_freq = {}
        for word in filtered_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # 按频率排序并返回前k个
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:top_k]]
    
    def _identify_meme_type(self, content: str) -> Optional[str]:
        """识别梗类型"""
        if not content:
            return None
        
        content_lower = content.lower()
        
        # 计算每种类型的匹配度
        type_scores = {}
        for meme_type, keywords in self.meme_keywords.items():
            score = 0
            for keyword in keywords:
                score += content_lower.count(keyword.lower())
            type_scores[meme_type] = score
        
        # 返回得分最高的类型
        if type_scores and max(type_scores.values()) > 0:
            return max(type_scores.items(), key=lambda x: x[1])[0]
        
        return "general"
    
    def _calculate_quality_score(self, raw_post: RawPost) -> float:
        """计算内容质量分数"""
        score = 0.0
        
        # 内容长度分数（10-500字符为满分）
        content_length = len(raw_post.content)
        if 10 <= content_length <= 500:
            score += 0.3
        elif content_length > 0:
            score += 0.1
        
        # 参与度分数
        total_engagement = (
            raw_post.like_count + 
            raw_post.comment_count + 
            raw_post.share_count
        )
        if total_engagement > 100:
            score += 0.3
        elif total_engagement > 10:
            score += 0.2
        elif total_engagement > 0:
            score += 0.1
        
        # 时间新鲜度分数（24小时内的内容加分）
        if raw_post.timestamp:
            hours_old = (datetime.now() - raw_post.timestamp).total_seconds() / 3600
            if hours_old <= 24:
                score += 0.2
            elif hours_old <= 168:  # 一周内
                score += 0.1
        
        # 平台特定加分
        platform_scores = {
            "bilibili": 0.1,
            "weibo": 0.1,
            "zhihu": 0.1,
            "tieba": 0.1,
            "douyin": 0.1
        }
        score += platform_scores.get(raw_post.platform, 0)
        
        # 内容质量指标
        if raw_post.title and len(raw_post.title) > 5:
            score += 0.1
        
        return min(1.0, score)
    
    def deduplicate_posts(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去除重复内容"""
        seen_content_hashes = set()
        deduplicated_posts = []
        
        for post in posts:
            # 创建内容哈希
            content = f"{post.get('content', '')}{post.get('title', '')}"
            content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            
            if content_hash not in seen_content_hashes:
                seen_content_hashes.add(content_hash)
                deduplicated_posts.append(post)
        
        logger.info(f"Deduplicated {len(posts)} posts to {len(deduplicated_posts)} unique posts")
        return deduplicated_posts
    
    def filter_by_quality(self, posts: List[Dict[str, Any]], min_quality: float = 0.3) -> List[Dict[str, Any]]:
        """按质量过滤内容"""
        filtered_posts = [
            post for post in posts 
            if post.get('quality_score', 0.0) >= min_quality
        ]
        
        logger.info(f"Filtered {len(posts)} posts by quality to {len(filtered_posts)} posts")
        return filtered_posts
    
    def cluster_similar_memes(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """聚类相似的梗内容"""
        if len(posts) < 2:
            return posts
        
        # 简单的基于关键词相似度的聚类
        clusters = {}
        processed_ids = set()
        
        for post in posts:
            if post['id'] in processed_ids:
                continue
            
            # 创建新聚类
            cluster_id = len(clusters)
            clusters[cluster_id] = {
                "cluster_id": cluster_id,
                "posts": [post],
                "representative": post,
                "keywords": post.get('keywords', [])[:5]
            }
            
            processed_ids.add(post['id'])
            
            # 寻找相似内容
            post_keywords = set(post.get('keywords', []))
            
            for other_post in posts:
                if other_post['id'] in processed_ids or other_post['id'] == post['id']:
                    continue
                
                other_keywords = set(other_post.get('keywords', []))
                
                # 计算关键词重叠度
                if post_keywords and other_keywords:
                    overlap = len(post_keywords & other_keywords)
                    similarity = overlap / max(len(post_keywords), len(other_keywords))
                    
                    if similarity > 0.5:  # 50%相似度阈值
                        clusters[cluster_id]["posts"].append(other_post)
                        processed_ids.add(other_post['id'])
        
        # 生成聚类结果
        clustered_posts = []
        for cluster in clusters.values():
            if len(cluster["posts"]) > 1:
                # 多内容聚类，保留最具代表性的
                best_post = max(cluster["posts"], key=lambda x: x.get('quality_score', 0))
                best_post['cluster_info'] = {
                    "cluster_id": cluster["cluster_id"],
                    "similar_posts_count": len(cluster["posts"]) - 1,
                    "representative_keywords": cluster["keywords"]
                }
                clustered_posts.append(best_post)
            else:
                # 单内容，直接添加
                clustered_posts.append(cluster["posts"][0])
        
        logger.info(f"Clustered {len(posts)} posts into {len(clustered_posts)} representative posts")
        return clustered_posts

# 全局实例
data_cleaner = MemeDataCleaner()