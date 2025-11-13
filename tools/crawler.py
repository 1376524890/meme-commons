"""
meme-commons 爬虫工具 - 从Reddit等平台抓取梗内容
"""
import requests
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from meme_commons.config import settings
from meme_commons.database.models import RawPost, get_db_session
import re

logger = logging.getLogger(__name__)

class RedditCrawler:
    """Reddit爬虫"""
    
    def __init__(self):
        self.base_url = "https://oauth.reddit.com"
        self.access_token = None
        self.token_expires = 0
        self.user_agent = settings.REDDIT_USER_AGENT
        
    def _get_access_token(self) -> str:
        """获取Reddit API访问令牌"""
        if self.access_token and time.time() < self.token_expires:
            return self.access_token
        
        try:
            # 使用客户端凭证模式获取访问令牌
            auth = (settings.REDDIT_CLIENT_ID, settings.REDDIT_CLIENT_SECRET)
            data = {
                "grant_type": "client_credentials"
            }
            headers = {
                "User-Agent": self.user_agent
            }
            
            response = requests.post(
                "https://www.reddit.com/api/v1/access_token",
                auth=auth,
                data=data,
                headers=headers
            )
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data["access_token"]
            self.token_expires = time.time() + token_data["expires_in"] - 60  # 提前1分钟过期
            
            logger.info("Successfully obtained Reddit access token")
            return self.access_token
            
        except Exception as e:
            logger.error(f"Failed to get Reddit access token: {e}")
            raise
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """发送Reddit API请求"""
        access_token = self._get_access_token()
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": self.user_agent
        }
        
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def crawl_subreddit(self, subreddit: str, sort: str = "hot", limit: int = 50) -> List[Dict[str, Any]]:
        """爬取子版块内容"""
        try:
            endpoint = f"/r/{subreddit}/{sort}"
            params = {
                "limit": min(limit, 100),  # Reddit API限制
                "t": "week"  # 获取本周内容
            }
            
            data = self._make_request(endpoint, params)
            posts = []
            
            for post in data["data"]["children"]:
                post_data = post["data"]
                
                # 过滤掉非文本内容
                if post_data.get("is_self", False) and post_data.get("selftext"):
                    posts.append({
                        "platform": "reddit",
                        "url": f"https://reddit.com{post_data['permalink']}",
                        "content": post_data["title"] + "\n" + post_data["selftext"],
                        "author": post_data["author"],
                        "timestamp": datetime.fromtimestamp(post_data["created_utc"]),
                        "upvotes": post_data.get("ups", 0),
                        "downvotes": post_data.get("downs", 0),
                        "comment_count": post_data.get("num_comments", 0),
                        "subreddit": subreddit,
                        "post_id": post_data["id"]
                    })
            
            logger.info(f"Successfully crawled {len(posts)} posts from r/{subreddit}")
            return posts
            
        except Exception as e:
            logger.error(f"Failed to crawl r/{subreddit}: {e}")
            return []
    
    def search_meme_keywords(self, keywords: List[str], limit: int = 50) -> List[Dict[str, Any]]:
        """搜索梗相关关键词"""
        all_posts = []
        
        # 搜索相关的子版块
        meme_subreddits = [
            "memes", "dankmemes", "meme", "funny", "comedy", 
            "AdviceAnimals", "fffffffuuuuuuuuuuuu", "PrequelMemes"
        ]
        
        for subreddit in meme_subreddits:
            try:
                posts = self.crawl_subreddit(subreddit, limit=limit // len(meme_subreddits))
                
                # 过滤包含关键词的帖子
                filtered_posts = []
                for post in posts:
                    content_lower = post["content"].lower()
                    if any(keyword.lower() in content_lower for keyword in keywords):
                        filtered_posts.append(post)
                
                all_posts.extend(filtered_posts)
                
                # 如果已经收集到足够的帖子，停止搜索
                if len(all_posts) >= limit:
                    break
                    
            except Exception as e:
                logger.error(f"Error searching in r/{subreddit}: {e}")
                continue
        
        logger.info(f"Found {len(all_posts)} posts matching keywords: {keywords}")
        return all_posts[:limit]

class MemeCrawler:
    """梗文化爬虫主类"""
    
    def __init__(self):
        self.reddit_crawler = RedditCrawler()
        self.supported_platforms = ["reddit", "twitter", "weibo"]
        
    def crawl_source(self, source: str, limit: int = 50, keywords: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """从指定来源爬取内容"""
        
        if source.lower() == "reddit":
            if keywords:
                return self.reddit_crawler.search_meme_keywords(keywords, limit)
            else:
                # 爬取热门梗内容
                return self.reddit_crawler.search_meme_keywords(["meme", "梗", "网络热词"], limit)
        
        elif source.lower() == "twitter":
            # 这里可以实现Twitter API爬虫
            logger.warning("Twitter crawler not implemented yet")
            return []
        
        elif source.lower() == "weibo":
            # 这里可以实现微博爬虫
            logger.warning("Weibo crawler not implemented yet")
            return []
        
        else:
            logger.error(f"Unsupported source: {source}")
            return []
    
    def extract_meme_patterns(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从帖子中提取梗模式"""
        meme_patterns = []
        
        for post in posts:
            content = post["content"]
            
            # 简单的梗模式识别
            # 这里可以添加更复杂的NLP分析
            patterns = {
                "hashtags": re.findall(r'#\w+', content),
                "mentions": re.findall(r'@\w+', content),
                "emojis": re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', content),
                "repeated_phrases": self._find_repeated_phrases(content),
                "viral_words": self._find_viral_words(content)
            }
            
            meme_patterns.append({
                "post_id": post.get("post_id"),
                "patterns": patterns,
                "engagement_score": self._calculate_engagement_score(post)
            })
        
        return meme_patterns
    
    def _find_repeated_phrases(self, text: str, min_length: int = 3) -> List[str]:
        """查找重复的短语"""
        words = text.split()
        phrases = []
        
        for length in range(min_length, min(len(words), 8)):
            for i in range(len(words) - length + 1):
                phrase = " ".join(words[i:i+length])
                if text.lower().count(phrase.lower()) > 1:
                    phrases.append(phrase)
        
        return list(set(phrases))
    
    def _find_viral_words(self, text: str) -> List[str]:
        """查找可能的热门词汇"""
        viral_words = []
        
        # 常见的热门词汇模式
        patterns = [
            r'\b\w*爆了\b',
            r'\b\w*火了\b',
            r'\b\w*出圈\b',
            r'\b\w*热搜\b',
            r'\b\w*刷屏\b',
            r'\b\w*梗\b',
            r'\b\w*神评\b',
            r'\b\w*神回复\b'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            viral_words.extend(matches)
        
        return list(set(viral_words))
    
    def _calculate_engagement_score(self, post: Dict[str, Any]) -> float:
        """计算帖子参与度分数"""
        upvotes = post.get("upvotes", 0)
        downvotes = post.get("downvotes", 0)
        comments = post.get("comment_count", 0)
        
        # 简单的参与度计算公式
        engagement = (upvotes - downvotes) + (comments * 2)
        
        # 时间衰减因子
        if post.get("timestamp"):
            days_old = (datetime.now() - post["timestamp"]).days
            time_factor = max(0.1, 1.0 - (days_old / 30))  # 30天后衰减到0.1
            engagement *= time_factor
        
        return float(engagement)

# 全局爬虫实例
crawler = MemeCrawler()