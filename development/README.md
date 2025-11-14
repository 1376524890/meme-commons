# 数据管道开发环境

这个目录包含了数据处理工作流的独立开发和测试工具，用于将数据处理工作流从 main.py 中分离出来进行独立开发。

## 目录结构

```
development/
├── __init__.py                 # 开发模块初始化
├── data_pipeline_dev.py        # 开发版本数据管道（v1）
├── data_pipeline_v2.py         # 优化版本数据管道（v2）
├── dev_config.py               # 开发环境配置
├── run_dev_tests.py            # 完整测试套件
├── test_simple.py              # 简单测试脚本
└── README.md                   # 本文件
```

## 核心组件

### 1. MemeDataPipelineV2 (data_pipeline_v2.py)
优化后的数据管道类，支持独立运行和测试：
- ✅ 更好的错误处理和日志记录
- ✅ 性能监控和统计
- ✅ 配置灵活，支持开发/测试模式
- ✅ 独立运行能力

### 2. DataPipelineDeveloper (data_pipeline_dev.py)
数据管道开发工具类，提供：
- 🛠 测试环境设置和清理
- 🧪 各个组件的独立测试
- 📊 性能监控和调试
- 🔧 配置管理和验证

### 3. DevConfig (dev_config.py)
开发环境配置和管理：
- 🔧 测试数据配置
- ⚙️ 开发/测试环境常量
- 📈 性能监控配置
- 🧪 测试工具函数

## 快速开始

### 1. 简单测试
```bash
# 运行简单测试
cd /home/codeserver/codes/meme_commons
python development/test_simple.py
```

### 2. 综合测试套件
```bash
# 运行完整测试套件
cd /home/codeserver/codes/meme_commons  
python development/run_dev_tests.py
```

### 3. 单独测试数据管道
```python
from development.data_pipeline_v2 import create_pipeline

# 创建管道实例
pipeline = create_pipeline({
    "keywords": ["梗", "meme"],
    "platforms": ["reddit", "tieba"],
    "batch_size": 10,
    "max_posts_per_keyword": 5,
    "verbose_logging": True
})

# 运行完整流程
result = await pipeline.run_full_pipeline()
```

## 开发模式

### 组件单独测试
```python
from development.data_pipeline_dev import DataPipelineDeveloper

developer = DataPipelineDeveloper()

# 设置测试环境
await developer.setup_test_environment()

# 单独测试各个组件
posts = await developer.test_crawler_component()
stored = await developer.test_database_storage(posts)
cards = await developer.test_knowledge_generation()
```

### 性能监控
```python
from development.dev_config import PerformanceMonitor

# 启用性能监控
PerformanceMonitor.enable()
performance_data = PerformanceMonitor.get_metrics()
```

## 集成到 main.py

开发完成后的集成步骤：

### 1. 选择最终版本
- 如果测试通过，选择 `MemeDataPipelineV2` 作为最终版本
- 或者根据需要优化和合并功能

### 2. 集成到 main.py
```python
# 在 main.py 中替换现有数据管道
from development.data_pipeline_v2 import create_pipeline

# 替换这一行：
# data_pipeline = MemeDataPipeline()

# 改为：
data_pipeline = create_pipeline({
    "keywords": DEFAULT_KEYWORDS,  # 从 main.py 导入或使用配置的关键词
    "platforms": ["reddit", "tieba", "weibo"],
    "batch_size": 20,
    "max_posts_per_keyword": 10,
    "verbose_logging": False
})

# 在初始化中使用：
await data_pipeline.initialize()
await data_pipeline.run_full_pipeline()
```

### 3. 移除开发文件
集成完成后，可以删除开发目录：
```bash
rm -rf development/
```

## 调试和日志

### 日志级别
- `development/dev_config.py` 中的 `DEBUG_MODE` 控制调试级别
- `verbose_logging` 参数控制详细日志输出

### 性能分析
- 管道自动记录性能指标
- 查看 `get_performance_report()` 获取详细统计
- 测试套件提供完整性能报告

## 常见问题

### Q: 爬虫不获取数据？
A: 检查：
1. 网络连接
2. 关键词设置（使用英文关键词，如 "meme"）
3. 平台配置
4. 请求延迟设置

### Q: 知识卡生成失败？
A: 检查：
1. LLM API 配置
2. 数据库连接
3. 足够的测试数据（至少需要3-5条帖子）

### Q: 性能优化建议？
A: 建议：
1. 增加 `batch_size` 提高批处理效率
2. 调整 `request_delay` 平衡速度和稳定性
3. 使用 `PerformanceMonitor` 分析瓶颈

## 开发流程

1. **独立开发**: 使用 `development/` 目录中的工具
2. **单元测试**: 各个组件独立测试
3. **集成测试**: 完整流程测试
4. **性能测试**: 运行基准测试
5. **集成到 main.py**: 将完成的组件合并
6. **清理**: 删除开发文件

这个开发环境允许你在不影响主系统的情况下独立开发和测试数据处理工作流。