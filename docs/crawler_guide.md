# 多平台爬虫系统使用指南

## 概述

增强后的爬虫系统支持以下平台的并行爬取：
- **百度贴吧** (tieba)
- **Bilibili** (bilibili) 
- **知乎** (zhihu)
- **微博** (weibo)
- **小红书** (xiaohongshu)
- **Reddit** (reddit)

## 支持的爬取内容

### 1. 热门搜索
- 微博热搜榜单
- 知乎热榜问题
- 百度贴吧热门帖子
- Bilibili热门视频

### 2. 热门评论
- Bilibili视频评论
- 知乎高赞回答
- 贴吧热门回复

### 3. 最新梗相关内容
- 按时间排序的最新梗相关帖子
- 各平台梗文化相关内容
- 关键词搜索结果

## 使用方法

### 基础爬取

```python
from tools.crawler import MemeCrawler

# 初始化爬虫
crawler = MemeCrawler()

# 爬取单个平台
reddit_posts = crawler.crawl_source("reddit", limit=50)
tieba_posts = crawler.crawl_source("tieba", limit=30)
weibo_posts = crawler.crawl_source("weibo", limit=40)

# 爬取所有平台
all_posts = crawler.crawl_source("all", limit=200)
```

### 关键词搜索

```python
# 搜索特定关键词
meme_keywords = ["梗", "沙雕", "网络热词", "yyds", "绝绝子"]
search_results = crawler.crawl_all_platforms(limit=100, keywords=meme_keywords)

# 爬取最新内容（按时间排序）
latest_memes = crawler.crawl_latest_meme_content(
    keywords=["梗", "网络热词"], 
    limit=150
)
```

### 热搜爬取

```python
# 爬取各平台热搜
hot_searches = crawler.crawl_hot_searches(limit=50)
```

### 数据分析

```python
# 获取爬取统计信息
stats = crawler.get_engagement_stats(all_posts)
print(f"总共爬取: {stats['total_posts']} 条内容")
print(f"总点赞数: {stats['total_likes']}")
print(f"总评论数: {stats['total_comments']}")
print(f"平台分布: {stats['platform_distribution']}")
```

## 数据结构

### 返回数据格式

```python
{
    "platform": "平台名称",
    "title": "标题内容", 
    "content": "正文内容",
    "author": "作者",
    "timestamp": "发布时间",
    "like_count": "点赞数",
    "comment_count": "评论数", 
    "view_count": "浏览数",
    "source": "内容来源",
    "url": "原文链接",
    "post_id": "帖子ID"
}
```

### 平台特定数据

不同平台会包含特定的扩展数据：

#### 微博
- `rank`: 热搜排名
- `platform_specific`: {"rank": 1}

#### Bilibili  
- `view_count`, `like_count`: 播放数和点赞数
- `comments`: 评论列表
- `platform_specific`: {"bvid": "BV号"}

#### 知乎
- `answer_count`: 回答数
- `follower_count`: 关注数  
- `voteup_count`: 赞同数
- `answers`: 高赞回答列表
- `platform_specific`: {"question_id": "问题ID"}

#### 贴吧
- `comment_count`: 回复数
- `platform_specific`: {"forum_name": "吧名"}

## 配置说明

### 配置文件 (config.py)

```python
# 各平台User-Agent配置
TIEBA_USER_AGENT = "Mozilla/5.0 (compatible crawler)"
BILIBILI_USER_AGENT = "Mozilla/5.0 (compatible crawler)"
ZHIHU_USER_AGENT = "Mozilla/5.0 (compatible crawler)" 
WEIBO_USER_AGENT = "Mozilla/5.0 (compatible crawler)"
XIAOHONGSHU_USER_AGENT = "Mozilla/5.0 (compatible crawler)"

# 爬取延迟设置（秒）
TIEBA_DELAY = 1.0
BILIBILI_DELAY = 1.5
ZHIHU_DELAY = 2.0
WEIBO_DELAY = 1.0  
XIAOHONGSHU_DELAY = 2.5

# 通用配置
MAX_CRAWL_PAGES = 50
CRAWL_TIMEOUT = 30
```

## 最佳实践

### 1. 合理设置并发数
```python
# 限制并发爬虫数量，避免对目标网站造成压力
with ThreadPoolExecutor(max_workers=3) as executor:
    # 爬取任务
```

### 2. 适当的延迟设置
```python
# 在BaseCrawler中已经包含了随机延迟
time.sleep(self.delay + random.uniform(0.1, 0.5))
```

### 3. 错误处理
```python
# 爬虫内置了重试机制和错误处理
try:
    posts = crawler.crawl_source("weibo", limit=50)
except Exception as e:
    logger.error(f"爬取失败: {e}")
```

### 4. 数据存储
```python
# 爬取的数据可以存储到数据库
from database.models import RawPost, get_db_session

session = get_db_session()
for post_data in posts:
    post = RawPost(**post_data)
    session.add(post)
session.commit()
```

## 注意事项

1. **遵守爬取频率限制**: 系统已内置延迟机制，但建议根据目标网站政策调整
2. **处理反爬措施**: 某些平台可能有反爬虫机制，需要相应的处理策略  
3. **数据质量控制**: 爬取后建议进行数据清洗和去重
4. **法律合规性**: 确保爬取行为符合相关法律法规和网站服务条款
5. **资源消耗**: 大量并发爬取可能消耗较多系统资源

## 扩展开发

如需添加新平台，可以：

1. 继承`BaseCrawler`类
2. 实现平台特定的爬取方法
3. 在`MemeCrawler`中注册新爬虫
4. 更新配置文件

示例：
```python
class NewPlatformCrawler(BaseCrawler):
    def __init__(self):
        super().__init__("new_platform", settings.NEWPLATFORM_USER_AGENT)
        
    def crawl_content(self, limit: int = 50):
        # 实现具体的爬取逻辑
        pass
```

## 故障排除

### 常见问题

1. **请求超时**: 增加`CRAWL_TIMEOUT`设置
2. **被反爬**: 更换User-Agent，增加延迟
3. **数据解析错误**: 检查HTML结构是否发生变化
4. **内存使用过高**: 减少并发数和单次爬取数量

### 日志分析

爬虫系统提供详细的日志信息：
```python
logger.info(f"Successfully crawled {len(posts)} posts from {platform}")
logger.warning(f"Request failed: {e}")
logger.error(f"Failed to crawl {platform}: {e}")
```

## 更新日志

- v2.0: 添加多平台支持，实现并行爬取
- v1.0: 基础Reddit爬虫功能