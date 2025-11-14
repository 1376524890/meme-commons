"""
meme-commons 数据处理管道开发测试环境
用于独立开发和调试数据处理工作流
"""
import asyncio
import logging
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import RawPost, MemeCard, TrendData, init_database, get_db_session
from tools.crawler import crawler
from tools.summarizer import meme_summarizer
from vector_store import vector_store
from config import settings
from data_pipeline import MemeDataPipeline

# 配置开发环境日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('development/data_pipeline_dev.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DataPipelineDeveloper:
    """数据管道开发测试工具"""
    
    def __init__(self):
        self.pipeline = MemeDataPipeline()
        self.test_results = {
            "crawl_test": {},
            "preprocess_test": {},
            "knowledge_card_test": {},
            "vector_storage_test": {},
            "full_pipeline_test": {}
        }
    
    async def setup_test_environment(self):
        """设置测试环境"""
        try:
            logger.info("Setting up test environment...")
            
            # 初始化数据库
            init_database(settings.DATABASE_URL)
            logger.info("Database initialized")
            
            # 创建开发日志目录
            os.makedirs("development/logs", exist_ok=True)
            
            logger.info("Test environment setup completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup test environment: {e}")
            return False
    
    async def test_crawling_only(self):
        """只测试爬取功能"""
        logger.info("=== Testing Crawling Only ===")
        
        try:
            # 测试小规模爬取
            test_keywords = ["梗", "meme"]  # 减少测试关键词
            test_platforms = ["reddit"]  # 只测试一个平台
            
            crawl_results = crawler.crawl_multiple_platforms(
                platforms=test_platforms,
                keywords=test_keywords,
                limit=5  # 限制爬取数量
            )
            
            self.test_results["crawl_test"] = {
                "status": "success",
                "results": crawl_results,
                "total_posts": sum(len(result.get("posts", [])) for result in crawl_results.values())
            }
            
            logger.info(f"Crawl test completed: {self.test_results['crawl_test']['total_posts']} posts")
            return self.test_results["crawl_test"]
            
        except Exception as e:
            logger.error(f"Crawl test failed: {e}")
            self.test_results["crawl_test"] = {
                "status": "failed",
                "error": str(e)
            }
            return self.test_results["crawl_test"]
    
    async def test_database_storage(self, sample_posts: List[Dict[str, Any]]):
        """测试数据库存储"""
        logger.info("=== Testing Database Storage ===")
        
        try:
            if not sample_posts:
                # 创建测试数据
                sample_posts = [{
                    "platform": "test",
                    "title": "测试梗",
                    "content": "这是一个测试用的梗内容",
                    "author": "测试用户",
                    "timestamp": datetime.now(),
                    "comment_count": 0,
                    "source": "test",
                    "url": "http://test.com",
                    "post_id": f"test_{datetime.now().timestamp()}",
                    "keywords": json.dumps(["测试", "梗"]),
                    "sentiment": "neutral",
                    "crawled_at": datetime.now()
                }]
            
            # 存储测试数据
            stored_count = await self.pipeline.preprocess_and_store_data(sample_posts)
            
            self.test_results["preprocess_test"] = {
                "status": "success",
                "stored_count": stored_count,
                "sample_data": sample_posts[:1]  # 只保存一个样本用于日志
            }
            
            logger.info(f"Storage test completed: {stored_count} posts stored")
            return self.test_results["preprocess_test"]
            
        except Exception as e:
            logger.error(f"Storage test failed: {e}")
            self.test_results["preprocess_test"] = {
                "status": "failed",
                "error": str(e)
            }
            return self.test_results["preprocess_test"]
    
    async def test_knowledge_card_generation(self):
        """测试知识卡生成"""
        logger.info("=== Testing Knowledge Card Generation ===")
        
        try:
            # 先插入一些测试数据
            test_posts = [{
                "platform": "test",
                "title": "测试梗",
                "content": "这是一个非常有趣的测试梗，大家都在讨论",
                "author": "测试用户",
                "timestamp": datetime.now(),
                "comment_count": 10,
                "source": "test",
                "url": "http://test.com",
                "post_id": f"test_{datetime.now().timestamp()}",
                "keywords": json.dumps(["测试", "梗"]),
                "sentiment": "positive",
                "crawled_at": datetime.now()
            }]
            
            await self.pipeline.preprocess_and_store_data(test_posts)
            
            # 生成知识卡
            generated_count = await self.pipeline.generate_knowledge_cards(min_posts_threshold=1)
            
            self.test_results["knowledge_card_test"] = {
                "status": "success",
                "generated_count": generated_count
            }
            
            logger.info(f"Knowledge card test completed: {generated_count} cards generated")
            return self.test_results["knowledge_card_test"]
            
        except Exception as e:
            logger.error(f"Knowledge card test failed: {e}")
            self.test_results["knowledge_card_test"] = {
                "status": "failed",
                "error": str(e)
            }
            return self.test_results["knowledge_card_test"]
    
    async def test_vector_storage(self):
        """测试向量存储"""
        logger.info("=== Testing Vector Storage ===")
        
        try:
            # 获取数据库中的知识卡
            session = get_db_session()
            meme_cards = session.query(MemeCard).limit(5).all()
            session.close()
            
            if meme_cards:
                # 模拟向量存储更新
                logger.info(f"Found {len(meme_cards)} meme cards for vector storage")
                
                self.test_results["vector_storage_test"] = {
                    "status": "success",
                    "cards_found": len(meme_cards),
                    "message": "Vector storage test would update embeddings for found cards"
                }
            else:
                self.test_results["vector_storage_test"] = {
                    "status": "success",
                    "cards_found": 0,
                    "message": "No meme cards found for vector storage test"
                }
            
            logger.info("Vector storage test completed")
            return self.test_results["vector_storage_test"]
            
        except Exception as e:
            logger.error(f"Vector storage test failed: {e}")
            self.test_results["vector_storage_test"] = {
                "status": "failed",
                "error": str(e)
            }
            return self.test_results["vector_storage_test"]
    
    async def run_full_pipeline_test(self):
        """运行完整管道测试"""
        logger.info("=== Running Full Pipeline Test ===")
        
        try:
            # 运行完整的管道
            result = await self.pipeline.run_full_pipeline()
            
            self.test_results["full_pipeline_test"] = result
            
            logger.info(f"Full pipeline test completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Full pipeline test failed: {e}")
            self.test_results["full_pipeline_test"] = {
                "status": "failed",
                "error": str(e)
            }
            return self.test_results["full_pipeline_test"]
    
    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("Starting comprehensive data pipeline development tests...")
        
        # 设置测试环境
        setup_success = await self.setup_test_environment()
        if not setup_success:
            logger.error("Test environment setup failed, aborting tests")
            return
        
        # 1. 测试爬取
        crawl_result = await self.test_crawling_only()
        
        # 2. 测试数据库存储
        if crawl_result.get("status") == "success":
            sample_posts = []
            for platform_result in crawl_result.get("results", {}).values():
                sample_posts.extend(platform_result.get("posts", []))
            
            if sample_posts:
                storage_result = await self.test_database_storage(sample_posts)
            else:
                storage_result = await self.test_database_storage(None)
        else:
            storage_result = await self.test_database_storage(None)
        
        # 3. 测试知识卡生成
        knowledge_card_result = await self.test_knowledge_card_generation()
        
        # 4. 测试向量存储
        vector_result = await self.test_vector_storage()
        
        # 5. 运行完整管道测试
        full_pipeline_result = await self.run_full_pipeline_test()
        
        # 生成测试报告
        await self.generate_test_report()
    
    async def generate_test_report(self):
        """生成测试报告"""
        try:
            report = {
                "timestamp": datetime.now().isoformat(),
                "test_summary": {
                    "total_tests": len(self.test_results),
                    "successful_tests": sum(1 for result in self.test_results.values() if result.get("status") == "success"),
                    "failed_tests": sum(1 for result in self.test_results.values() if result.get("status") == "failed")
                },
                "detailed_results": self.test_results
            }
            
            # 保存测试报告
            report_file = "development/test_report.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"Test report saved to {report_file}")
            logger.info(f"Test Summary: {report['test_summary']}")
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate test report: {e}")

async def main():
    """开发测试主函数"""
    developer = DataPipelineDeveloper()
    await developer.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())