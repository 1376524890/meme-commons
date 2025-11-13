#!/usr/bin/env python3
"""
多平台爬虫系统测试脚本
用于验证各个平台的爬取功能
"""

import sys
import os
import json
import logging
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.crawler import MemeCrawler
from config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_single_platform(platform: str, limit: int = 10):
    """测试单个平台爬取"""
    print(f"\n=== 测试平台: {platform.upper()} ===")
    
    try:
        crawler = MemeCrawler()
        posts = crawler.crawl_source(platform, limit=limit)
        
        if posts:
            print(f"✅ 成功爬取 {len(posts)} 条内容")
            
            # 显示第一条内容示例
            if posts:
                sample = posts[0]
                print(f"📝 示例内容:")
                print(f"   标题: {sample.get('title', 'N/A')}")
                print(f"   作者: {sample.get('author', 'N/A')}")
                print(f"   平台: {sample.get('platform', 'N/A')}")
                print(f"   来源: {sample.get('source', 'N/A')}")
                
                # 显示平台特定数据
                if sample.get('platform_specific'):
                    print(f"   平台数据: {sample['platform_specific']}")
        else:
            print(f"⚠️  未爬取到内容")
            
        return posts
        
    except Exception as e:
        print(f"❌ 爬取失败: {e}")
        return []

def test_keyword_search():
    """测试关键词搜索"""
    print(f"\n=== 测试关键词搜索 ===")
    
    try:
        crawler = MemeCrawler()
        keywords = ["梗", "网络热词", "搞笑"]
        
        posts = crawler.crawl_source("all", limit=20, keywords=keywords)
        
        if posts:
            print(f"✅ 通过关键词搜索到 {len(posts)} 条内容")
            
            # 按平台统计
            platform_counts = {}
            for post in posts:
                platform = post.get('platform', 'unknown')
                platform_counts[platform] = platform_counts.get(platform, 0) + 1
            
            print(f"📊 平台分布: {platform_counts}")
            
            return posts
        else:
            print(f"⚠️  关键词搜索未找到相关内容")
            return []
            
    except Exception as e:
        print(f"❌ 关键词搜索失败: {e}")
        return []

def test_all_platforms():
    """测试所有平台并行爬取"""
    print(f"\n=== 测试全平台并行爬取 ===")
    
    try:
        crawler = MemeCrawler()
        
        # 并行爬取所有平台
        posts = crawler.crawl_all_platforms(limit=30)
        
        if posts:
            print(f"✅ 并行爬取成功，共获得 {len(posts)} 条内容")
            
            # 统计信息
            stats = crawler.get_engagement_stats(posts)
            print(f"📈 统计信息:")
            print(f"   总帖数: {stats['total_posts']}")
            print(f"   总点赞: {stats['total_likes']}")
            print(f"   总评论: {stats['total_comments']}")
            print(f"   平台分布: {stats['platform_distribution']}")
            
            return posts
        else:
            print(f"⚠️  并行爬取未获得内容")
            return []
            
    except Exception as e:
        print(f"❌ 并行爬取失败: {e}")
        return []

def test_latest_content():
    """测试最新内容爬取"""
    print(f"\n=== 测试最新内容爬取 ===")
    
    try:
        crawler = MemeCrawler()
        keywords = ["梗", "网络热词"]
        
        posts = crawler.crawl_latest_meme_content(keywords, limit=20)
        
        if posts:
            print(f"✅ 爬取到 {len(posts)} 条最新内容")
            
            # 显示时间分布
            time_ranges = {
                "1小时内": 0,
                "1-6小时": 0,
                "6-24小时": 0,
                "1天以上": 0
            }
            
            now = datetime.now()
            for post in posts[:10]:  # 只分析前10条
                if post.get('timestamp'):
                    time_diff = now - post['timestamp']
                    hours = time_diff.total_seconds() / 3600
                    
                    if hours <= 1:
                        time_ranges["1小时内"] += 1
                    elif hours <= 6:
                        time_ranges["1-6小时"] += 1
                    elif hours <= 24:
                        time_ranges["6-24小时"] += 1
                    else:
                        time_ranges["1天以上"] += 1
            
            print(f"⏰ 时间分布: {time_ranges}")
            
            return posts
        else:
            print(f"⚠️  未爬取到最新内容")
            return []
            
    except Exception as e:
        print(f"❌ 最新内容爬取失败: {e}")
        return []

def test_engagement_analysis():
    """测试参与度分析"""
    print(f"\n=== 测试参与度分析 ===")
    
    try:
        crawler = MemeCrawler()
        
        # 先爬取一些内容用于分析
        posts = crawler.crawl_source("bilibili", limit=10)
        
        if posts:
            stats = crawler.get_engagement_stats(posts)
            
            print(f"📊 参与度分析结果:")
            for key, value in stats.items():
                print(f"   {key}: {value}")
            
            return stats
        else:
            print(f"⚠️  没有内容可用于分析")
            return {}
            
    except Exception as e:
        print(f"❌ 参与度分析失败: {e}")
        return {}

def save_test_results(results: dict, filename: str = "crawler_test_results.json"):
    """保存测试结果"""
    try:
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        # 转换datetime对象为字符串
        serializable_results = {}
        for key, value in results.items():
            if isinstance(value, datetime):
                serializable_results[key] = value.isoformat()
            elif isinstance(value, list):
                serializable_results[key] = [
                    {
                        k: (v.isoformat() if isinstance(v, datetime) else v)
                        for k, v in item.items()
                        if not isinstance(v, datetime) or hasattr(v, 'isoformat')
                    }
                    for item in value[:5]  # 只保存前5条记录
                ]
            else:
                serializable_results[key] = value
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, ensure_ascii=False, indent=2)
        
        print(f"💾 测试结果已保存到: {filepath}")
        
    except Exception as e:
        print(f"❌ 保存结果失败: {e}")

def main():
    """主测试函数"""
    print("🚀 开始多平台爬虫系统测试")
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 存储测试结果
    test_results = {}
    
    # 测试各个平台
    platforms = ["bilibili", "weibo", "tieba", "zhihu", "xiaohongshu"]
    
    for platform in platforms:
        posts = test_single_platform(platform, limit=5)
        test_results[f"{platform}_posts"] = posts
        test_results[f"{platform}_count"] = len(posts)
    
    # 测试关键词搜索
    keyword_posts = test_keyword_search()
    test_results["keyword_posts"] = keyword_posts
    test_results["keyword_count"] = len(keyword_posts)
    
    # 测试全平台并行爬取
    all_posts = test_all_platforms()
    test_results["all_platforms_posts"] = all_posts
    test_results["all_platforms_count"] = len(all_posts)
    
    # 测试最新内容
    latest_posts = test_latest_content()
    test_results["latest_posts"] = latest_posts
    test_results["latest_count"] = len(latest_posts)
    
    # 测试参与度分析
    engagement_stats = test_engagement_analysis()
    test_results["engagement_stats"] = engagement_stats
    
    # 总结测试结果
    print(f"\n" + "="*50)
    print(f"📋 测试总结")
    print(f"="*50)
    
    total_successful_crawls = sum(
        test_results.get(f"{platform}_count", 0) 
        for platform in platforms
    )
    
    print(f"✅ 单平台爬取成功: {total_successful_crawls} 条内容")
    print(f"✅ 关键词搜索: {test_results.get('keyword_count', 0)} 条内容")
    print(f"✅ 全平台并行: {test_results.get('all_platforms_count', 0)} 条内容")
    print(f"✅ 最新内容: {test_results.get('latest_count', 0)} 条内容")
    
    # 保存测试结果
    save_test_results(test_results)
    
    print(f"\n🎉 测试完成！")
    return test_results

if __name__ == "__main__":
    main()