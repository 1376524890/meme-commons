# 开发环境配置和工具模块
# 用于数据处理工作流的独立开发和测试

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

class DevConfig:
    """开发环境配置"""
    
    def __init__(self):
        # 测试相关配置
        self.TEST_KEYWORDS = ["梗", "meme", "网络流行语"]
        self.TEST_PLATFORMS = ["reddit", "tieba"]
        self.TEST_BATCH_SIZE = 10
        self.TEST_MAX_POSTS_PER_KEYWORD = 20
        self.TEST_DB_PATH = "/home/codeserver/codes/meme_commons/database/meme_commons_test.db"
        
        # 开发模式配置
        self.DEBUG_MODE = True
        self.VERBOSE_LOGGING = True

class DevTools:
    """开发工具类"""
    
    @staticmethod
    def get_test_data() -> Dict[str, Any]:
        """获取测试数据"""
        return {
            "sample_posts": [
                {
                    "platform": "reddit",
                    "title": "有趣的梗分享",
                    "content": "这个梗真的很有趣，大家都觉得搞笑",
                    "author": "test_user",
                    "timestamp": datetime.now(),
                    "comment_count": 10,
                    "source": "r/funny",
                    "url": "https://reddit.com/r/funny/test",
                    "post_id": "mock_001"
                },
                {
                    "platform": "tieba",
                    "title": "网络流行语讨论",
                    "content": "最近网上流行的梗是什么意思？",
                    "author": "user1",
                    "timestamp": datetime.now(),
                    "comment_count": 5,
                    "source": "tieba.baidu.com",
                    "url": "https://tieba.baidu.com/test",
                    "post_id": "mock_002"
                }
            ],
            "sample_keywords": ["梗", "meme", "网络流行语"],
            "sample_platforms": ["reddit", "tieba"]
        }
    
    @staticmethod
    def create_test_database(db_path: str) -> bool:
        """创建测试数据库"""
        try:
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            # 这里应该创建真实的测试数据库
            # 目前只是创建目录
            return True
        except Exception:
            return False
    
    @staticmethod
    def clean_test_data(db_path: str):
        """清理测试数据"""
        try:
            if os.path.exists(db_path):
                os.remove(db_path)
        except Exception:
            pass

class DevUtils:
    """开发工具函数"""
    
    @staticmethod
    def format_test_result(results: Dict[str, Any]) -> str:
        """格式化测试结果"""
        lines = ["测试结果摘要:"]
        for test_name, result in results.items():
            status = "✅ 通过" if result else "❌ 失败"
            lines.append(f"  {test_name}: {status}")
        return "\n".join(lines)
    
    @staticmethod
    def get_database_stats(db_path: str) -> Dict[str, int]:
        """获取数据库统计信息"""
        stats = {
            "raw_posts_count": 0,
            "meme_cards_count": 0,
            "trends_count": 0
        }
        # 这里应该查询真实的数据库统计
        return stats
    
    @staticmethod
    def print_performance_summary(performance_data: Dict[str, Any]):
        """打印性能摘要"""
        if "statistics" in performance_data:
            stats = performance_data["statistics"]
            print(f"总运行次数: {stats.get('total_runs', 0)}")
            print(f"成功运行: {stats.get('successful_runs', 0)}")
            print(f"爬取帖子: {stats.get('total_posts_crawled', 0)}")
            print(f"存储帖子: {stats.get('total_posts_stored', 0)}")
            print(f"生成知识卡: {stats.get('total_knowledge_cards', 0)}")
            print(f"最后运行耗时: {stats.get('last_run_duration', 0):.2f}秒")

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics = {}
        self.enabled = False
    
    def enable(self):
        """启用性能监控"""
        self.enabled = True
    
    def disable(self):
        """禁用性能监控"""
        self.enabled = False
    
    @classmethod
    def get_metrics(cls) -> Dict[str, Any]:
        """获取性能指标"""
        return cls.metrics.copy()
    
    @classmethod
    def record_metric(cls, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """记录性能指标"""
        if cls.enabled:
            metric = {
                "timestamp": datetime.now().isoformat(),
                "value": value,
                "tags": tags or {}
            }
            if name not in cls.metrics:
                cls.metrics[name] = []
            cls.metrics[name].append(metric)

# 全局配置实例
dev_config = DevConfig()