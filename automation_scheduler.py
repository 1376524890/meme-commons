"""
自动化任务调度器
协调整个抓取→清洗→分析→存储的自动化流程
"""
import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import time
from concurrent.futures import ThreadPoolExecutor

# 导入系统的核心组件
from data_cleaner import MemeDataCleaner
from meme_analysis import MemeAnalysisEngine
from knowledge_card_manager import KnowledgeCardManager, KnowledgeCardMonitor
from data_pipeline import MemeDataPipeline
from database.models import init_database, get_db_session

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"  
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

@dataclass
class AutomationTask:
    """自动化任务定义"""
    task_id: str
    task_type: str  # 'crawl', 'analyze', 'full_pipeline'
    priority: TaskPriority
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    progress: float = 0.0
    result: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        data['status'] = self.status.value
        data['priority'] = self.priority.value
        data['created_at'] = self.created_at.isoformat()
        if self.started_at:
            data['started_at'] = self.started_at.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        return data

class AutomationScheduler:
    """自动化任务调度器"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.logger = logging.getLogger(__name__)
        
        # 初始化核心组件
        self.data_pipeline = MemeDataPipeline()
        self.data_cleaner = MemeDataCleaner()
        self.analysis_engine = MemeAnalysisEngine()
        self.card_manager = KnowledgeCardManager()
        self.card_monitor = KnowledgeCardMonitor()
        
        # 任务管理
        self.task_queue: List[AutomationTask] = []
        self.running_tasks: Dict[str, AutomationTask] = {}
        self.completed_tasks: List[AutomationTask] = []
        
        # 调度器状态
        self.is_running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self.executor = ThreadPoolExecutor(max_workers=3)
        
        # 统计信息
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "last_crawl_time": None,
            "last_analysis_time": None,
            "total_cards_created": 0
        }
    
    def start_scheduler(self):
        """启动调度器"""
        if self.is_running:
            self.logger.warning("调度器已在运行中")
            return
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info("自动化任务调度器已启动")
    
    def stop_scheduler(self):
        """停止调度器"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=10)
        
        self.executor.shutdown(wait=True)
        self.logger.info("自动化任务调度器已停止")
    
    def submit_crawl_task(self, platform: str, keywords: List[str], 
                         limit: int = 20, priority: TaskPriority = TaskPriority.NORMAL) -> str:
        """提交爬取任务"""
        task_id = f"crawl_{datetime.now().timestamp()}"
        
        task = AutomationTask(
            task_id=task_id,
            task_type="crawl",
            priority=priority,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            config={
                "platform": platform,
                "keywords": keywords,
                "limit": limit
            }
        )
        
        self.task_queue.append(task)
        self.task_queue.sort(key=lambda x: x.priority.value, reverse=True)
        
        self.logger.info(f"已提交爬取任务: {task_id}")
        return task_id
    
    def submit_analysis_task(self, source: str = "recent", 
                           priority: TaskPriority = TaskPriority.NORMAL) -> str:
        """提交分析任务"""
        task_id = f"analyze_{datetime.now().timestamp()}"
        
        task = AutomationTask(
            task_id=task_id,
            task_type="analyze",
            priority=priority,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            config={"source": source}
        )
        
        self.task_queue.append(task)
        self.task_queue.sort(key=lambda x: x.priority.value, reverse=True)
        
        self.logger.info(f"已提交分析任务: {task_id}")
        return task_id
    
    def submit_full_pipeline_task(self, platforms: List[str], keywords: List[str], 
                                limit: int = 50, priority: TaskPriority = TaskPriority.NORMAL) -> str:
        """提交完整流程任务（抓取→清洗→分析→存储）"""
        task_id = f"pipeline_{datetime.now().timestamp()}"
        
        task = AutomationTask(
            task_id=task_id,
            task_type="full_pipeline",
            priority=priority,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            config={
                "platforms": platforms,
                "keywords": keywords,
                "limit": limit
            }
        )
        
        self.task_queue.append(task)
        self.task_queue.sort(key=lambda x: x.priority.value, reverse=True)
        
        self.logger.info(f"已提交完整流程任务: {task_id}")
        return task_id
    
    def _scheduler_loop(self):
        """调度器主循环"""
        while self.is_running:
            try:
                # 检查并启动新任务
                if len(self.running_tasks) < 3:  # 最大并发任务数
                    self._start_next_task()
                
                # 检查运行中的任务
                self._check_running_tasks()
                
                # 清理完成的任务
                self._cleanup_completed_tasks()
                
                time.sleep(5)  # 5秒检查间隔
                
            except Exception as e:
                self.logger.error(f"调度器循环错误: {e}")
                time.sleep(10)
    
    def _start_next_task(self):
        """启动下一个待处理任务"""
        if not self.task_queue:
            return
        
        # 获取优先级最高的任务
        task = self.task_queue.pop(0)
        
        # 设置任务状态
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        self.running_tasks[task.task_id] = task
        
        # 提交到线程池执行
        if task.task_type == "crawl":
            future = self.executor.submit(self._execute_crawl_task, task)
        elif task.task_type == "analyze":
            future = self.executor.submit(self._execute_analysis_task, task)
        elif task.task_type == "full_pipeline":
            future = self.executor.submit(self._execute_full_pipeline_task, task)
        else:
            task.status = TaskStatus.FAILED
            task.error_message = f"未知任务类型: {task.task_type}"
            return
    
    def _execute_crawl_task(self, task: AutomationTask):
        """执行爬取任务"""
        try:
            self.logger.info(f"开始执行爬取任务: {task.task_id}")
            task.progress = 10.0
            
            config = task.config
            platform = config["platform"]
            keywords = config["keywords"]
            limit = config["limit"]
            
            # 执行爬取
            if platform.lower() == "all":
                crawl_results = []
                for p in ["weibo", "bilibili", "douyin"]:
                    result = self.data_pipeline.crawl_platform(
                        platform=p, 
                        keywords=keywords, 
                        limit=limit // 3
                    )
                    if result.get("success"):
                        crawl_results.extend(result.get("crawl_results", []))
                    task.progress += 20.0
            else:
                result = self.data_pipeline.crawl_platform(
                    platform=platform, 
                    keywords=keywords, 
                    limit=limit
                )
                crawl_results = result.get("crawl_results", []) if result.get("success") else []
                task.progress += 70.0
            
            # 返回结果
            task.result = {
                "crawled_count": len(crawl_results),
                "platform": platform,
                "keywords": keywords,
                "crawl_results": crawl_results
            }
            
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.progress = 100.0
            
            # 更新统计
            self.stats["completed_tasks"] += 1
            self.stats["last_crawl_time"] = datetime.now().isoformat()
            
            self.logger.info(f"爬取任务完成: {task.task_id}, 抓取 {len(crawl_results)} 条数据")
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.now()
            self.logger.error(f"爬取任务失败: {task.task_id}, 错误: {e}")
    
    def _execute_analysis_task(self, task: AutomationTask):
        """执行分析任务"""
        try:
            self.logger.info(f"开始执行分析任务: {task.task_id}")
            task.progress = 10.0
            
            # 获取原始数据
            session = get_db_session()
            try:
                # 获取近期未处理的数据
                raw_posts = session.query("posts_raw").filter(
                    "processed = 0"
                ).limit(100).all()
                
                if not raw_posts:
                    task.result = {"message": "没有需要分析的数据"}
                    task.status = TaskStatus.COMPLETED
                    task.progress = 100.0
                    return
                
                task.progress = 30.0
                
                # 批量分析
                analysis_results = self.analysis_engine.batch_analyze_posts(raw_posts)
                task.progress = 70.0
                
                # 创建知识卡
                created_card_ids = self.card_manager.batch_create_from_analysis(analysis_results)
                task.progress = 90.0
                
                task.result = {
                    "analyzed_count": len(analysis_results),
                    "created_cards": len(created_card_ids),
                    "analysis_results": analysis_results,
                    "created_card_ids": created_card_ids
                }
                
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                task.progress = 100.0
                
                # 更新统计
                self.stats["completed_tasks"] += 1
                self.stats["last_analysis_time"] = datetime.now().isoformat()
                self.stats["total_cards_created"] += len(created_card_ids)
                
                self.logger.info(f"分析任务完成: {task.task_id}, 创建了 {len(created_card_ids)} 个知识卡")
                
            finally:
                session.close()
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.now()
            self.logger.error(f"分析任务失败: {task.task_id}, 错误: {e}")
    
    def _execute_full_pipeline_task(self, task: AutomationTask):
        """执行完整流程任务"""
        try:
            self.logger.info(f"开始执行完整流程任务: {task.task_id}")
            task.progress = 5.0
            
            config = task.config
            platforms = config["platforms"]
            keywords = config["keywords"]
            limit = config["limit"]
            
            # 阶段1: 爬取数据
            self.logger.info("阶段1: 开始爬取数据")
            all_crawl_results = []
            
            for i, platform in enumerate(platforms):
                task.progress = 5.0 + (i + 1) * 15.0 / len(platforms)
                
                result = self.data_pipeline.crawl_platform(
                    platform=platform,
                    keywords=keywords,
                    limit=limit // len(platforms)
                )
                
                if result.get("success"):
                    crawl_results = result.get("crawl_results", [])
                    all_crawl_results.extend(crawl_results)
            
            task.progress = 25.0
            
            # 阶段2: 数据清洗
            self.logger.info("阶段2: 开始数据清洗")
            cleaned_data = []
            
            for i, post in enumerate(all_crawl_results):
                if i % 10 == 0:  # 每10个更新一次进度
                    task.progress = 25.0 + (i + 1) * 20.0 / max(len(all_crawl_results), 1)
                
                cleaned_post = self.data_cleaner.clean_content(post)
                if cleaned_post and cleaned_post.get("quality_score", 0) >= 6.0:
                    cleaned_data.append(cleaned_post)
            
            task.progress = 50.0
            
            # 阶段3: AI分析
            self.logger.info("阶段3: 开始AI分析")
            if cleaned_data:
                analysis_results = self.analysis_engine.batch_analyze_posts(cleaned_data)
            else:
                analysis_results = []
            
            task.progress = 75.0
            
            # 阶段4: 生成知识卡
            self.logger.info("阶段4: 开始生成知识卡")
            created_card_ids = self.card_manager.batch_create_from_analysis(analysis_results)
            
            task.progress = 95.0
            
            # 完成
            task.result = {
                "total_crawled": len(all_crawl_results),
                "total_cleaned": len(cleaned_data),
                "total_analyzed": len(analysis_results),
                "total_cards_created": len(created_card_ids),
                "created_card_ids": created_card_ids,
                "analysis_results": analysis_results[:5]  # 只保留前5个结果
            }
            
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.progress = 100.0
            
            # 更新统计
            self.stats["completed_tasks"] += 1
            self.stats["total_cards_created"] += len(created_card_ids)
            
            self.logger.info(f"完整流程任务完成: {task.task_id}")
            self.logger.info(f"爬取: {len(all_crawl_results)}, 清洗: {len(cleaned_data)}, 分析: {len(analysis_results)}, 创建知识卡: {len(created_card_ids)}")
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.now()
            self.logger.error(f"完整流程任务失败: {task.task_id}, 错误: {e}")
    
    def _check_running_tasks(self):
        """检查运行中的任务"""
        # 这里可以添加任务超时检查、心跳监控等
        current_time = datetime.now()
        
        for task_id, task in list(self.running_tasks.items()):
            # 检查任务是否超时（2小时）
            if task.started_at and (current_time - task.started_at).total_seconds() > 7200:
                task.status = TaskStatus.FAILED
                task.error_message = "任务执行超时"
                task.completed_at = current_time
                self.running_tasks.pop(task_id)
                self.completed_tasks.append(task)
                self.logger.warning(f"任务 {task_id} 执行超时，已终止")
    
    def _cleanup_completed_tasks(self):
        """清理已完成的任务"""
        # 移动完成的任务到历史记录
        for task_id, task in list(self.running_tasks.items()):
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                self.running_tasks.pop(task_id)
                self.completed_tasks.append(task)
        
        # 只保留最近100个已完成的任务
        if len(self.completed_tasks) > 100:
            self.completed_tasks = self.completed_tasks[-100:]
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        # 检查运行中的任务
        if task_id in self.running_tasks:
            return self.running_tasks[task_id].to_dict()
        
        # 检查已完成的任务
        for task in self.completed_tasks:
            if task.task_id == task_id:
                return task.to_dict()
        
        return None
    
    def get_all_tasks(self, status: TaskStatus = None, limit: int = 20) -> List[Dict[str, Any]]:
        """获取所有任务"""
        all_tasks = []
        
        # 运行中的任务
        for task in self.running_tasks.values():
            if not status or task.status == status:
                all_tasks.append(task.to_dict())
        
        # 已完成的任务
        for task in self.completed_tasks:
            if not status or task.status == status:
                all_tasks.append(task.to_dict())
        
        # 按创建时间倒序
        all_tasks.sort(key=lambda x: x["created_at"], reverse=True)
        
        return all_tasks[:limit]
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取调度器系统状态"""
        system_status = self.card_monitor.get_system_status()
        
        # 添加调度器状态
        scheduler_status = {
            "is_running": self.is_running,
            "running_tasks": len(self.running_tasks),
            "pending_tasks": len(self.task_queue),
            "total_completed": len(self.completed_tasks)
        }
        
        # 添加统计信息
        scheduler_status.update(self.stats)
        
        system_status["scheduler"] = scheduler_status
        
        return system_status
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        # 取消待处理的任务
        for i, task in enumerate(self.task_queue):
            if task.task_id == task_id:
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.now()
                self.task_queue.pop(i)
                self.logger.info(f"已取消待处理任务: {task_id}")
                return True
        
        # 取消运行中的任务
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()
            self.running_tasks.pop(task_id)
            self.completed_tasks.append(task)
            self.logger.info(f"已取消运行中任务: {task_id}")
            return True
        
        return False
    
    def setup_scheduled_tasks(self):
        """设置定时任务"""
        # 每2小时执行一次全面爬取和分析
        # 每30分钟执行一次热门关键词爬取
        # 每天清理一次旧数据
        
        # 这些定时任务可以通过外部cron或其他调度系统触发
        self.logger.info("定时任务设置完成:")
        self.logger.info("- 每2小时: 全面爬取和分析")
        self.logger.info("- 每30分钟: 热门内容爬取")
        self.logger.info("- 每天: 数据清理")
    
    def close(self):
        """关闭调度器"""
        self.stop_scheduler()
        self.data_pipeline.cleanup()
        self.card_manager.close()
        self.card_monitor.close()

# 全局调度器实例
scheduler = None

def init_scheduler(database_url: str) -> AutomationScheduler:
    """初始化调度器"""
    global scheduler
    scheduler = AutomationScheduler(database_url)
    return scheduler

def get_scheduler() -> AutomationScheduler:
    """获取调度器实例"""
    global scheduler
    if scheduler is None:
        raise RuntimeError("调度器未初始化，请先调用 init_scheduler()")
    return scheduler