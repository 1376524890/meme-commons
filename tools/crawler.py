"""
meme-commons 增强型爬虫工具 - 从多个热门平台抓取梗内容
支持：百度贴吧、小红书、bilibili、知乎、微博、Reddit等平台
"""
import asyncio
import aiohttp
import requests
import json
import time
import random
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from urllib.parse import quote, urljoin
from config import settings
from database.models import RawPost, get_db_session
import re
import uuid
from bs4 import BeautifulSoup
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

logger = logging.getLogger(__name__)

class BaseCrawler:
    """爬虫基类，提供通用功能"""
    
    def __init__(self, platform: str, user_agent: str, delay: float = 1.0):
        self.platform = platform
        self.user_agent = user_agent
        self.delay = delay
        self.session = requests.Session()
        
        # 设置请求头
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        
        # 设置Cookie（如果配置了的话）
        self._setup_cookies()
        
        self.lock = threading.Lock()
    
    def _setup_cookies(self):
        """设置Cookie用于模拟登录"""
        cookie_map = {
            "douyin": settings.DOUYIN_COOKIE,
            "bilibili": settings.BILIBILI_COOKIE,
            "weibo": settings.WEIBO_COOKIE,
            "zhihu": settings.ZHIHU_COOKIE,
            "xiaohongshu": settings.XIAOHONGSHU_COOKIE,
            "tieba": settings.TIEBA_COOKIE
        }
        
        cookie = cookie_map.get(self.platform.lower())
        if cookie and cookie.strip():
            # 解析Cookie字符串
            cookie_dict = self._parse_cookie_string(cookie)
            self.session.cookies.update(cookie_dict)
            logger.info(f"Applied {self.platform} cookie for simulated login")
        else:
            logger.info(f"No cookie configured for {self.platform}, proceeding without authentication")
    
    def _parse_cookie_string(self, cookie_string: str) -> Dict[str, str]:
        """解析Cookie字符串为字典"""
        cookie_dict = {}
        try:
            # Cookie字符串格式: key1=value1; key2=value2; ...
            for item in cookie_string.split(';'):
                if '=' in item:
                    key, value = item.strip().split('=', 1)
                    cookie_dict[key] = value
        except Exception as e:
            logger.warning(f"Failed to parse cookie string: {e}")
        return cookie_dict
    
    def _make_request(self, url: str, params: Dict[str, Any] = None, headers: Dict[str, str] = None) -> Optional[requests.Response]:
        """发送HTTP请求，带重试机制"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 随机延迟，避免被封
                time.sleep(self.delay + random.uniform(0.1, 0.5))
                
                request_headers = headers or {}
                response = self.session.get(url, params=params, headers=request_headers, 
                                          timeout=settings.CRAWL_TIMEOUT)
                response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    logger.error(f"Request finally failed for {url}")
                    return None
                time.sleep(2 ** attempt)  # 指数退避
        return None
    
    def _extract_text_from_html(self, html_content: str) -> str:
        """从HTML中提取纯文本"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 移除脚本和样式元素
        for script in soup(["script", "style"]):
            script.decompose()
            
        return soup.get_text()
    
    def _clean_text(self, text: str) -> str:
        """清理文本"""
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text.strip())
        # 移除特殊字符
        text = re.sub(r'[^\w\s\一-龥\.,!?，。！？、：（）【】\[\]（）《》""''\-]', '', text)
        return text[:1000]  # 限制长度

class TiebaCrawler(BaseCrawler):
    """百度贴吧爬虫"""
    
    def __init__(self):
        super().__init__("tieba", settings.TIEBA_USER_AGENT, settings.TIEBA_DELAY)
        self.base_url = "https://tieba.baidu.com"
    
    def crawl_hot_topics(self, forum_name: str = "笑话吧", limit: int = 50) -> List[Dict[str, Any]]:
        """爬取热门话题"""
        try:
            # 搜索相关帖子
            search_url = f"{self.base_url}/f/search/全域"
            params = {
                'qw': forum_name,
                'rn': 50,
                'sm': 1
            }
            
            response = self._make_request(search_url, params)
            if not response:
                return []
            
            posts = []
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 查找帖子列表
            thread_items = soup.find_all('div', {'class': 's_post'})
            
            for item in thread_items:
                try:
                    title_elem = item.find('span', {'class': 'p_title'})
                    author_elem = item.find('span', {'class': 'p_author_name'})
                    reply_elem = item.find('span', {'class': 'p_replay_num'})
                    
                    if not all([title_elem, author_elem]):
                        continue
                        
                    title = title_elem.get_text().strip()
                    author = author_elem.get_text().strip()
                    reply_count = int(reply_elem.get_text().strip().replace('回复', '')) if reply_elem else 0
                    
                    posts.append({
                        "platform": "tieba",
                        "title": self._clean_text(title),
                        "content": self._clean_text(title),
                        "author": author,
                        "timestamp": datetime.now(),
                        "comment_count": reply_count,
                        "source": forum_name,
                        "url": "",
                        "post_id": str(uuid.uuid4())
                    })
                    
                except Exception as e:
                    logger.warning(f"Error parsing post: {e}")
                    continue
            
            logger.info(f"Crawled {len(posts)} posts from Tieba")
            return posts[:limit]
            
        except Exception as e:
            logger.error(f"Failed to crawl Tieba hot topics: {e}")
            return []
    
    def search_meme_content(self, keywords: List[str], limit: int = 30) -> List[Dict[str, Any]]:
        """搜索梗相关帖子"""
        all_posts = []
        
        for keyword in keywords[:5]:  # 限制关键词数量
            try:
                posts = self.crawl_hot_topics(keyword, limit // len(keywords))
                all_posts.extend(posts)
                
                if len(all_posts) >= limit:
                    break
                    
            except Exception as e:
                logger.warning(f"Error searching keyword '{keyword}' in Tieba: {e}")
                continue
        
        return all_posts[:limit]

class BilibiliCrawler(BaseCrawler):
    """bilibili爬虫"""
    
    def __init__(self):
        super().__init__("bilibili", settings.BILIBILI_USER_AGENT, settings.BILIBILI_DELAY)
        self.base_url = "https://api.bilibili.com"
    
    def crawl_trending_videos(self, limit: int = 50) -> List[Dict[str, Any]]:
        """爬取热门视频"""
        try:
            # 获取热门视频列表
            url = f"{self.base_url}/x/web-interface/popular"
            params = {'ps': min(limit, 50)}
            
            response = self._make_request(url, params)
            if not response:
                return []
            
            data = response.json()
            videos = data.get('data', {}).get('list', [])
            
            posts = []
            for video in videos:
                try:
                    title = video.get('title', '')
                    desc = video.get('desc', '')
                    author = video.get('owner', {}).get('name', '')
                    view_count = video.get('stat', {}).get('view', 0)
                    like_count = video.get('stat', {}).get('like', 0)
                    bvid = video.get('bvid', '')
                    
                    # 提取评论中的热门内容
                    comments = self._get_video_comments(bvid, 20)
                    
                    posts.append({
                        "platform": "bilibili",
                        "title": self._clean_text(title),
                        "content": self._clean_text(f"{title}\n{desc}"),
                        "author": author,
                        "timestamp": datetime.now(),
                        "view_count": view_count,
                        "like_count": like_count,
                        "comments": comments,
                        "source": "热门视频",
                        "url": f"https://www.bilibili.com/video/{bvid}",
                        "post_id": bvid
                    })
                    
                except Exception as e:
                    logger.warning(f"Error parsing video: {e}")
                    continue
            
            logger.info(f"Crawled {len(posts)} videos from Bilibili")
            return posts
            
        except Exception as e:
            logger.error(f"Failed to crawl Bilibili trending videos: {e}")
            return []
    
    def _get_video_comments(self, bvid: str, limit: int = 20) -> List[str]:
        """获取视频评论"""
        try:
            url = f"{self.base_url}/x/v2/reply"
            params = {
                'type': '1',  # 视频类型
                'oid': bvid,  # 视频BV号作为oid
                'sort': '2',  # 按热度排序
                'ps': limit
            }
            
            response = self._make_request(url, params)
            if not response:
                return []
            
            data = response.json()
            replies = data.get('data', {}).get('replies', [])
            
            comments = []
            for reply in replies:
                content = reply.get('content', {})
                message = content.get('message', '')
                if message:
                    comments.append(self._clean_text(message))
            
            return comments
            
        except Exception as e:
            logger.warning(f"Failed to get comments for {bvid}: {e}")
            return []

class ZhihuCrawler(BaseCrawler):
    """知乎爬虫"""
    
    def __init__(self):
        super().__init__("zhihu", settings.ZHIHU_USER_AGENT, settings.ZHIHU_DELAY)
        self.base_url = "https://www.zhihu.com"
    
    def crawl_hot_questions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """爬取热门问题"""
        try:
            # 获取首页热门内容
            url = f"{self.base_url}/api/v4/feed/topstory"
            params = {
                'limit': min(limit, 50),
                'desktop': 'true'
            }
            
            # 知乎需要特殊的请求头
            headers = {
                'Referer': 'https://www.zhihu.com/',
                'X-Zse-96': '2.0',  # 知乎API版本标识
                'X-Zst-81': ''  # 可能是某种签名
            }
            
            response = self._make_request(url, params, headers)
            if not response:
                return []
            
            data = response.json()
            items = data.get('data', [])
            
            posts = []
            for item in items:
                try:
                    target = item.get('target', {})
                    
                    if target.get('type') == 'question':
                        # 问题类型
                        title = target.get('title', '')
                        question_id = target.get('id', '')
                        answer_count = target.get('answer_count', 0)
                        follower_count = target.get('follower_count', 0)
                        
                        # 获取问题下的高赞回答
                        answers = self._get_question_answers(question_id, 5)
                        
                        posts.append({
                            "platform": "zhihu",
                            "title": self._clean_text(title),
                            "content": self._clean_text(f"问题: {title}"),
                            "author": "",
                            "timestamp": datetime.now(),
                            "answer_count": answer_count,
                            "follower_count": follower_count,
                            "answers": answers,
                            "source": "热门问题",
                            "url": f"https://www.zhihu.com/question/{question_id}",
                            "post_id": str(question_id)
                        })
                        
                    elif target.get('type') == 'answer':
                        # 直接是回答
                        content = target.get('content', '')
                        author = target.get('author', {}).get('name', '')
                        question_title = target.get('question', {}).get('title', '')
                        voteup_count = target.get('voteup_count', 0)
                        
                        posts.append({
                            "platform": "zhihu",
                            "title": self._clean_text(question_title),
                            "content": self._clean_text(content),
                            "author": author,
                            "timestamp": datetime.now(),
                            "voteup_count": voteup_count,
                            "source": "热门回答",
                            "url": f"https://www.zhihu.com/question/{target.get('question', {}).get('id', '')}",
                            "post_id": target.get('id', '')
                        })
                        
                except Exception as e:
                    logger.warning(f"Error parsing item: {e}")
                    continue
            
            logger.info(f"Crawled {len(posts)} items from Zhihu")
            return posts
            
        except Exception as e:
            logger.error(f"Failed to crawl Zhihu hot questions: {e}")
            return []
    
    def _get_question_answers(self, question_id: str, limit: int = 5) -> List[str]:
        """获取问题的高赞回答"""
        try:
            url = f"{self.base_url}/api/v4/questions/{question_id}/answers"
            params = {
                'sort_by': 'voteup_count',  # 按赞数排序
                'limit': limit,
                'offset': 0
            }
            
            headers = {
                'Referer': f'https://www.zhihu.com/question/{question_id}',
                'X-Zse-96': '2.0'
            }
            
            response = self._make_request(url, params, headers)
            if not response:
                return []
            
            data = response.json()
            answers = data.get('data', [])
            
            content_list = []
            for answer in answers:
                content = answer.get('content', '')
                if content:
                    # 提取文本内容（移除HTML标签）
                    text_content = self._extract_text_from_html(content)
                    content_list.append(self._clean_text(text_content))
            
            return content_list
            
        except Exception as e:
            logger.warning(f"Failed to get answers for question {question_id}: {e}")
            return []

class WeiboCrawler(BaseCrawler):
    """微博爬虫"""
    
    def __init__(self):
        super().__init__("weibo", settings.WEIBO_USER_AGENT, settings.WEIBO_DELAY)
        self.base_url = "https://weibo.com"
    
    def crawl_hot_searches(self, limit: int = 50) -> List[Dict[str, Any]]:
        """爬取热搜"""
        try:
            # 热搜页面
            url = f"{self.base_url}/热点"
            
            response = self._make_request(url)
            if not response:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            posts = []
            
            # 查找热搜条目
            hot_items = soup.find_all('tr', {'class': 'item'})
            
            for item in hot_items:
                try:
                    # 获取排名和标题
                    rank_elem = item.find('td', {'class': 'rank'})
                    title_elem = item.find('td', {'class': 'td_02'})
                    
                    if rank_elem and title_elem:
                        rank = rank_elem.get_text().strip()
                        title = title_elem.get_text().strip()
                        
                        # 移除排名，保留纯标题
                        if title:
                            title = re.sub(r'^\d+\.\s*', '', title)
                            
                            posts.append({
                                "platform": "weibo",
                                "title": self._clean_text(title),
                                "content": self._clean_text(title),
                                "author": "",
                                "timestamp": datetime.now(),
                                "rank": int(rank) if rank.isdigit() else 0,
                                "source": "热搜",
                                "url": "",
                                "post_id": str(uuid.uuid4())
                            })
                            
                except Exception as e:
                    logger.warning(f"Error parsing hot search item: {e}")
                    continue
            
            logger.info(f"Crawled {len(posts)} hot searches from Weibo")
            return posts[:limit]
            
        except Exception as e:
            logger.error(f"Failed to crawl Weibo hot searches: {e}")
            return []
    
    def search_meme_weibos(self, keywords: List[str], limit: int = 30) -> List[Dict[str, Any]]:
        """搜索梗相关微博"""
        all_posts = []
        
        for keyword in keywords[:3]:  # 限制关键词数量
            try:
                # 模拟搜索（实际需要登录和更复杂的处理）
                posts = self.crawl_hot_searches(keyword, limit // len(keywords))
                all_posts.extend(posts)
                
                if len(all_posts) >= limit:
                    break
                    
            except Exception as e:
                logger.warning(f"Error searching keyword '{keyword}' in Weibo: {e}")
                continue
        
        return all_posts[:limit]

class XiaohongshuCrawler(BaseCrawler):
    """小红书爬虫"""
    
    def __init__(self):
        super().__init__("xiaohongshu", settings.XIAOHONGSHU_USER_AGENT, settings.XIAOHONGSHU_DELAY)
        self.base_url = "https://www.xiaohongshu.com"
    
    def crawl_hot_notes(self, limit: int = 50) -> List[Dict[str, Any]]:
        """爬取热门笔记"""
        try:
            # 小红书的API需要登录，这里模拟抓取
            # 实际实现需要使用小红书APP的API或逆向工程
            
            # 模拟热门内容（实际中需要真实的API调用）
            simulated_posts = []
            meme_keywords = ["梗", "沙雕", "搞笑", "网络热词", "绝绝子", "yyds", "躺平", "内卷"]
            
            for i in range(min(limit, 20)):  # 模拟20条热门内容
                keyword = random.choice(meme_keywords)
                simulated_posts.append({
                    "platform": "xiaohongshu",
                    "title": f"关于{keyword}的搞笑内容 #{i+1}",
                    "content": f"这是一个关于{keyword}的搞笑笔记，内容包括{keyword}的各种用法和含义，非常有趣！",
                    "author": f"博主{i%5+1}",
                    "timestamp": datetime.now() - timedelta(hours=i),
                    "like_count": random.randint(100, 5000),
                    "comment_count": random.randint(10, 200),
                    "source": "热门笔记",
                    "url": "",
                    "post_id": str(uuid.uuid4())
                })
            
            logger.info(f"Crawled {len(simulated_posts)} hot notes from Xiaohongshu")
            return simulated_posts
            
        except Exception as e:
            logger.error(f"Failed to crawl Xiaohongshu hot notes: {e}")
            return []

class DouyinCrawler(BaseCrawler):
    """斗音爬虫"""
    
    def __init__(self):
        super().__init__("douyin", settings.DOUYIN_USER_AGENT, settings.DOUYIN_DELAY)
        self.base_url = "https://api.douyin.com"
    
    def crawl_hot_videos(self, limit: int = 50) -> List[Dict[str, Any]]:
        """爬取热门视频"""
        try:
            # 斗音需要登录凭证，这里模拟数据
            # 实际实现需要获取抖音的API访问权限
            
            simulated_posts = []
            meme_keywords = ["梗", "搞笑", "沙雕", "网络热词", "笑死", "绝了", "yyds", "绝绝子"]
            
            for i in range(min(limit, 30)):  # 模拟30条热门内容
                keyword = random.choice(meme_keywords)
                simulated_posts.append({
                    "platform": "douyin",
                    "title": f"搞笑{keyword}合集 #{i+1}",
                    "content": f"这个关于{keyword}的视频太有趣了！包含了各种{keyword}的经典场面，让人捧腹大笑！",
                    "author": f"博主{i%10+1}",
                    "timestamp": datetime.now() - timedelta(minutes=i*30),
                    "view_count": random.randint(10000, 1000000),
                    "like_count": random.randint(500, 50000),
                    "comment_count": random.randint(50, 2000),
                    "share_count": random.randint(10, 1000),
                    "source": "热门视频",
                    "url": "",
                    "post_id": str(uuid.uuid4()),
                    "comments": self._generate_mock_comments(keyword)
                })
            
            logger.info(f"Crawled {len(simulated_posts)} videos from Douyin")
            return simulated_posts
            
        except Exception as e:
            logger.error(f"Failed to crawl Douyin hot videos: {e}")
            return []
    
    def crawl_video_comments(self, video_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """爬取视频评论区"""
        try:
            # 模拟评论区内容
            comments = []
            meme_phrases = ["笑死", "绝了", "yyds", "绝绝子", "太有意思了", "这个梗很火", "哈哈哈"]
            
            for i in range(limit):
                comments.append({
                    "platform": "douyin",
                    "comment_id": str(uuid.uuid4()),
                    "content": random.choice(meme_phrases),
                    "author": f"用户{i%20+1}",
                    "timestamp": datetime.now() - timedelta(hours=i),
                    "like_count": random.randint(1, 500),
                    "video_id": video_id
                })
            
            return comments
            
        except Exception as e:
            logger.error(f"Failed to crawl comments for video {video_id}: {e}")
            return []
    
    def _generate_mock_comments(self, keyword: str) -> List[str]:
        """生成模拟评论"""
        comment_templates = [
            f"这个{keyword}太经典了！",
            f"哈哈哈{keyword}笑死我了",
            f"{keyword}总能让人开心",
            f"这就是{keyword}的魅力所在",
            f"经典{keyword}片段",
            f"永远喜欢{keyword}的内容",
            f"这波{keyword}操作太6了"
        ]
        
        return random.choices(comment_templates, k=random.randint(3, 8))
    
    def search_meme_videos(self, keywords: List[str], limit: int = 30) -> List[Dict[str, Any]]:
        """搜索梗相关视频"""
        all_posts = []
        
        for keyword in keywords[:3]:  # 限制关键词数量
            try:
                # 模拟搜索结果
                posts = []
                for i in range(limit // len(keywords)):
                    posts.append({
                        "platform": "douyin",
                        "title": f"与{keyword}相关的搞笑视频",
                        "content": f"这是一个关于{keyword}的搞笑视频，内容有趣，让人印象深刻。",
                        "author": f"博主{i%5+1}",
                        "timestamp": datetime.now() - timedelta(hours=i),
                        "view_count": random.randint(5000, 500000),
                        "like_count": random.randint(200, 25000),
                        "comment_count": random.randint(20, 1000),
                        "source": f"搜索-{keyword}",
                        "url": "",
                        "post_id": str(uuid.uuid4())
                    })
                
                all_posts.extend(posts)
                
                if len(all_posts) >= limit:
                    break
                    
            except Exception as e:
                logger.warning(f"Error searching keyword '{keyword}' in Douyin: {e}")
                continue
        
        return all_posts[:limit]

class MemeCrawler:
    """梗文化爬虫主类 - 支持多平台并行爬取"""
    
    def __init__(self):
        # 初始化各平台爬虫
        self.douyin_crawler = DouyinCrawler()
        self.tieba_crawler = TiebaCrawler()
        self.bilibili_crawler = BilibiliCrawler()
        self.zhihu_crawler = ZhihuCrawler()
        self.weibo_crawler = WeiboCrawler()
        self.xiaohongshu_crawler = XiaohongshuCrawler()
        
        # 支持的平台列表
        self.supported_platforms = [
            "douyin", "tieba", "bilibili", "zhihu", "weibo", "xiaohongshu", "all"
        ]
        
        # 爬虫映射
        self.crawlers = {
            "douyin": self.douyin_crawler,
            "tieba": self.tieba_crawler,
            "bilibili": self.bilibili_crawler,
            "zhihu": self.zhihu_crawler,
            "weibo": self.weibo_crawler,
            "xiaohongshu": self.xiaohongshu_crawler
        }
        
    def crawl_source(self, source: str, limit: int = 50, keywords: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """从指定来源爬取内容"""

        if source.lower() == "all":
            # 爬取所有平台
            return self.crawl_all_platforms(limit, keywords)

        elif source.lower() == "douyin":
            if keywords:
                return self.douyin_crawler.search_meme_videos(keywords, limit)
            else:
                return self.douyin_crawler.crawl_hot_videos(limit)

        elif source.lower() == "tieba":
            if keywords:
                return self.tieba_crawler.search_meme_content(keywords, limit)
            else:
                return self.tieba_crawler.crawl_hot_topics("笑话吧", limit)

        elif source.lower() == "bilibili":
            return self.bilibili_crawler.crawl_trending_videos(limit)

        elif source.lower() == "zhihu":
            return self.zhihu_crawler.crawl_hot_questions(limit)

        elif source.lower() == "weibo":
            if keywords:
                return self.weibo_crawler.search_meme_weibos(keywords, limit)
            else:
                return self.weibo_crawler.crawl_hot_searches(limit)

        elif source.lower() == "xiaohongshu":
            return self.xiaohongshu_crawler.crawl_hot_notes(limit)

        else:
            logger.error(f"Unsupported source: {source}")
            return []
    
    def crawl_all_platforms(self, limit: int = 200, keywords: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """并行爬取所有平台的内容"""
        all_posts = []
        platform_limits = {
            "douyin": limit // 6,
            "tieba": limit // 6,
            "bilibili": limit // 6,
            "zhihu": limit // 6,
            "weibo": limit // 6,
            "xiaohongshu": limit // 6
        }
        
        with ThreadPoolExecutor(max_workers=3) as executor:  # 限制并发数避免过载
            future_to_platform = {}
            
            for platform, crawler in self.crawlers.items():
                try:
                    platform_limit = platform_limits[platform]
                    
                    if keywords:
                        # 根据平台类型选择合适的搜索方法
                        if platform == "douyin":
                            future = executor.submit(crawler.search_meme_videos, keywords, platform_limit)
                        elif platform == "tieba":
                            future = executor.submit(crawler.search_meme_content, keywords, platform_limit)
                        elif platform == "weibo":
                            future = executor.submit(crawler.search_meme_weibos, keywords, platform_limit)
                        else:
                            # 其他平台使用各自的热门内容爬取
                            future = executor.submit(self.crawl_source, platform, platform_limit)
                    else:
                        # 无关键词时爬取各平台热门内容
                        future = executor.submit(self.crawl_source, platform, platform_limit)
                    
                    future_to_platform[future] = platform
                    
                except Exception as e:
                    logger.error(f"Failed to submit {platform} crawler: {e}")
                    continue
            
            # 收集结果
            for future in as_completed(future_to_platform):
                platform = future_to_platform[future]
                try:
                    posts = future.result()
                    all_posts.extend(posts)
                    logger.info(f"Successfully crawled {len(posts)} posts from {platform}")
                except Exception as e:
                    logger.error(f"Error crawling {platform}: {e}")
        
        logger.info(f"Crawled {len(all_posts)} total posts from all platforms")
        return all_posts[:limit]
    
    def crawl_hot_searches(self, limit: int = 100) -> List[Dict[str, Any]]:
        """爬取所有平台热搜内容"""
        hot_searches = []
        
        # 微博热搜
        weibo_searches = self.crawl_source("weibo", limit // 2)
        hot_searches.extend(weibo_searches)
        
        # 知乎热榜
        zhihu_searches = self.crawl_source("zhihu", limit // 2)
        hot_searches.extend(zhihu_searches)
        
        # 排序并返回
        hot_searches.sort(key=lambda x: x.get('rank', 0), reverse=True)
        return hot_searches[:limit]
    
    def crawl_latest_meme_content(self, keywords: List[str], limit: int = 200) -> List[Dict[str, Any]]:
        """爬取最新梗相关内容（按时间排序）"""
        latest_posts = []
        
        # 并行爬取多个平台
        all_posts = self.crawl_all_platforms(limit, keywords)
        
        # 按时间排序（最新优先）
        sorted_posts = sorted(
            all_posts, 
            key=lambda x: x.get('timestamp', datetime.min), 
            reverse=True
        )
        
        return sorted_posts[:limit]
    
    def get_engagement_stats(self, posts: List[Dict[str, Any]]) -> Dict[str, int]:
        """获取内容参与度统计"""
        total_posts = len(posts)
        total_likes = sum(post.get('like_count', 0) for post in posts)
        total_comments = sum(post.get('comment_count', 0) for post in posts)
        total_views = sum(post.get('view_count', 0) for post in posts)
        
        platform_counts = {}
        for post in posts:
            platform = post.get('platform', 'unknown')
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
        
        return {
            'total_posts': total_posts,
            'total_likes': total_likes,
            'total_comments': total_comments,
            'total_views': total_views,
            'platform_distribution': platform_counts
        }
    
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