# meme-commons — LLM驱动的梗文化智能分析平台

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📖 项目简介

meme-commons是一个基于大语言模型（LLM）编排的智能化梗文化情报收集、分析和查询系统。该系统通过MCP（Model Context Protocol）协议提供统一的服务接口，支持多平台内容爬取、智能分析、趋势预测和知识管理，为梗文化研究提供完整的技术解决方案。

### 🎯 核心目标

- **智能化内容发现**: 利用LLM自动识别和分析网络热梗
- **多平台数据整合**: 统一管理来自不同社交媒体平台的内容
- **趋势分析预测**: 基于历史数据预测梗文化的演进方向
- **知识图谱构建**: 构建结构化的梗文化知识库
- **实时监控分析**: 提供实时的梗文化变化趋势监控

### 🌟 主要特色

- **🤖 LLM智能编排**: 基于先进大语言模型的自动化工作流
- **🌐 多平台支持**: 支持抖音、微博、B站、知乎、小红书、贴吧等主流中文平台
- **📊 智能分析**: 集成文本嵌入、语义搜索、趋势分析等AI能力
- **🔍 精准搜索**: 基于向量相似性的智能搜索引擎
- **📈 趋势预测**: 实时分析梗文化热度和演进趋势
- **🎯 自动化流程**: 一键式完整分析流程，从爬取到知识卡生成
- **🖥️ 可视化监控**: 基于Streamlit的实时监控和管理界面
- **🔧 模块化设计**: 高度模块化的架构，便于扩展和定制

## 🏗️ 系统架构

### 整体架构图

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端界面      │    │   监控界面      │    │   API客户端     │
│ (Streamlit App) │    │ (自动化监控)    │    │   (REST API)    │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────┬─────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────┐
│              MCP服务器层                        │
│           (FastAPI + MCP协议)                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │ 知识统计API │  │ 自动化流程API│  │ 其他API  │ │
│  └─────────────┘  └─────────────┘  └─────────┘ │
└────────────────────────┬────────────────────────┘
                         │
┌────────────────────────┴────────────────────────┐
│              LLM协调器层                        │
│           (Orchestrator)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │  爬取工具   │  │  分析工具   │  │ 查询工具 │ │
│  │   (Crawler) │  │ (Analyzer)  │  │ (Query) │ │
│  └─────────────┘  └─────────────┘  └─────────┘ │
└────────────────────────┬────────────────────────┘
                         │
┌────────────────────────┴────────────────────────┐
│              数据存储层                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │ 关系数据库  │  │ 向量数据库  │  │ 任务队列 │ │
│  │ (SQLite/PG) │  │ (Vector DB) │  │ (Redis) │ │
│  └─────────────┘  └─────────────┘  └─────────┘ │
└─────────────────────────────────────────────────┘
```

### 核心组件

1. **MCP服务器**: 基于FastAPI的RESTful API服务，提供标准化的接口
2. **LLM协调器**: 核心调度引擎，统一管理和协调各功能模块
3. **数据管理层**: 处理数据存储、检索和管理
4. **工具模块**: 独立的工具组件，执行具体的功能任务
5. **前端界面**: 用户交互和可视化展示

## 🚀 快速开始

### 前置要求

- **Python**: 3.11 或更高版本
- **操作系统**: Linux/macOS/Windows
- **内存**: 建议 4GB+
- **存储**: 建议 10GB+ 可用空间

### 环境准备

#### 1. 克隆项目

```bash
git clone https://github.com/your-org/meme-commons.git
cd meme-commons
```

#### 2. 创建Python环境

**使用conda（推荐）**:
```bash
# 创建独立环境
conda create -n meme-commons python=3.11 -y
conda activate meme-commons

# 安装依赖
pip install -r requirements.txt
```

**使用venv**:
```bash
# 创建虚拟环境
python -m venv venv-meme
source venv-meme/bin/activate  # Linux/macOS
# venv-meme\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

#### 3. 环境配置

```bash
# 复制环境配置模板
cp .env.example .env

# 编辑配置文件
nano .env
```

**完整配置示例**:
```bash
# ===========================================
# 数据库配置
# ===========================================
DATABASE_URL=sqlite:///meme_commons.db
# 生产环境建议使用PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost:5432/meme_commons

# ===========================================
# API密钥配置  
# ===========================================
# Dashscope API (阿里云)
DASHSCOPE_API_KEY=your_dashscope_api_key_here

# OpenAI API (可选)
OPENAI_API_KEY=your_openai_api_key_here

# ===========================================
# MCP服务器配置
# ===========================================
MCP_HOST=0.0.0.0
MCP_PORT=8002

# ===========================================
# 前端界面配置
# =========================================== 
STREAMLIT_PORT=8501
STREAMLIT_HOST=0.0.0.0

# ===========================================
# Cookie配置 (重要!)
# ===========================================
# 配置各平台Cookie可显著提高数据获取质量
DOUYIN_COOKIE=your_douyin_cookie_here
WEIBO_COOKIE=your_weibo_cookie_here  
BILIBILI_COOKIE=your_bilibili_cookie_here
ZHIHU_COOKIE=your_zhihu_cookie_here
XIAOHONGSHU_COOKIE=your_xiaohongshu_cookie_here
TIEBA_COOKIE=your_tieba_cookie_here

# ===========================================
# 高级配置
# ===========================================
# 向量嵌入模型
EMBEDDING_MODEL=text-embedding-v2

# 最大并发数
MAX_CONCURRENT_REQUESTS=10

# 请求间隔 (秒)
REQUEST_INTERVAL=1

# 日志级别
LOG_LEVEL=INFO
```

### 🍪 Cookie配置详细说明

Cookie配置是获取高质量数据的关键。以下是各平台Cookie获取方法：

#### 获取Cookie的通用步骤
1. **打开平台网站**: 使用Chrome/Firefox浏览器
2. **登录账户**: 确保已正常登录
3. **打开开发者工具**: 按F12或右键→检查
4. **定位Cookie**: 
   - Chrome: Application → Storage → Cookies
   - Firefox: Storage → Cookies
5. **复制Cookie值**: 选择对应域名，复制完整的Cookie字符串

#### 各平台访问地址

| 平台 | 访问地址 | Cookie域名 |
|------|----------|------------|
| 抖音 | https://www.douyin.com | .douyin.com |
| 微博 | https://www.weibo.com | .weibo.com |
| B站 | https://www.bilibili.com | .bilibili.com |
| 知乎 | https://www.zhihu.com | .zhihu.com |
| 小红书 | https://www.xiaohongshu.com | .xiaohongshu.com |
| 贴吧 | https://tieba.baidu.com | .tieba.baidu.com |

### 4. 系统启动

#### 🎯 一键启动（推荐）

我们提供了简化的启动脚本：

```bash
# 完整启动（包括前端和后端）
./run.sh

# 仅安装依赖
./run.sh --deps-only

# 查看帮助
./run.sh --help
```

#### 🔧 手动启动

**启动后端服务（MCP服务器）**:
```bash
# 方法1: 直接启动
python main.py

# 方法2: 后台运行
nohup python main.py > backend.log 2>&1 &
echo $! > backend.pid

# 方法3: 使用systemd (Linux)
sudo systemctl start meme-commons-backend
```

**启动前端界面**:
```bash
# 方法1: 直接启动
streamlit run automation_monitor.py --server.port 8501 --server.address 0.0.0.0

# 方法2: 后台运行
nohup streamlit run automation_monitor.py --server.port 8501 --server.address 0.0.0.0 > frontend.log 2>&1 &
echo $! > frontend.pid

# 方法3: 使用systemd (Linux)
sudo systemctl start meme-commons-frontend
```

#### ✅ 启动验证

**检查服务状态**:
```bash
# 检查后端健康状态
curl http://localhost:8002/health

# 检查前端界面
curl http://localhost:8501

# 查看服务端口
netstat -tuln | grep -E ":(8002|8501)"
```

**预期输出**:
```json
{
  "status": "healthy",
  "database": "connected",
  "version": "1.0.0",
  "services": {
    "mcp_server": "running",
    "database": "connected",
    "vector_store": "ready"
  }
}
```

### 5. 访问系统

启动成功后，通过以下地址访问系统：

- **🎛️ 自动化监控界面**: http://localhost:8501
- **🔧 后端API文档**: http://localhost:8002/docs
- **❤️ 健康检查**: http://localhost:8002/health
- **📊 知识统计**: http://localhost:8002/mcp/knowledge/stats
- **📈 系统状态**: http://localhost:8002/mcp/status

## 📚 详细使用指南

### 🔍 知识库查询

#### 基础查询
```bash
# 按关键词查询梗知识
curl "http://localhost:8002/mcp/knowledge?q=梗文化&limit=10"

# 按分类查询
curl "http://localhost:8002/mcp/knowledge?category=搞笑&limit=20"

# 高级查询（包含筛选条件）
curl "http://localhost:8002/mcp/knowledge?q=人工智能&min_trend_score=0.5&limit=15"
```

#### 响应示例
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "meme_001",
        "name": "AI梗",
        "description": "与人工智能相关的幽默内容",
        "category": "科技",
        "keywords": ["AI", "人工智能", "机器人"],
        "trend_score": 0.85,
        "popularity_score": 0.72,
        "source_platforms": ["微博", "B站"],
        "last_updated": "2024-01-15T10:30:00Z"
      }
    ],
    "total": 1,
    "query_time": 0.156
  }
}
```

### 📊 知识统计功能

#### 获取知识库整体统计
```bash
# 获取完整统计信息
curl "http://localhost:8002/mcp/knowledge/stats"
```

#### 响应示例
```json
{
  "success": true,
  "data": {
    "total_cards": 1247,
    "avg_trend_score": 0.67,
    "recent_cards": 89,
    "high_trend_cards": 156,
    "popular_tags": ["梗文化", "搞笑", "沙雕", "表情包"]
  },
  "timestamp": "2024-01-15T12:00:00Z"
}
```

### 🤖 自动化流程

#### 1. 内容爬取任务

**基础爬取**:
```bash
# 爬取抖音热门内容
curl -X POST "http://localhost:8002/mcp/automation/crawl" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "douyin",
    "keywords": ["梗", "搞笑"],
    "limit": 50
  }'
```

**高级爬取**:
```bash
# 多平台并发爬取
curl -X POST "http://localhost:8002/mcp/automation/crawl" \
  -H "Content-Type: application/json" \
  -d '{
    "platforms": ["douyin", "weibo", "bilibili"],
    "keywords": ["梗文化", "meme", "沙雕"],
    "limit": 200,
    "use_cookies": true,
    "sort_by": "popularity"
  }'
```

**响应示例**:
```json
{
  "success": true,
  "task_id": "crawl_1763098549.352884",
  "message": "Crawl task submitted successfully"
}
```

#### 2. 完整分析流程

**一键式分析流程**:
```bash
# 提交完整流程任务（爬取→清洗→分析→生成知识卡）
curl -X POST "http://localhost:8002/mcp/automation/full_pipeline" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "weibo",
    "keywords": ["梗", "meme"],
    "limit": 100,
    "analysis_config": {
      "min_posts_threshold": 10,
      "trend_threshold": 0.6,
      "generate_knowledge_cards": true
    }
  }'
```

**完整流程任务响应**:
```json
{
  "success": true,
  "task_id": "pipeline_1763098575.611754",
  "message": "Full pipeline task submitted successfully"
}
```

#### 3. 任务状态监控

**查询任务状态**:
```bash
# 获取所有任务状态
curl "http://localhost:8002/mcp/automation/tasks"

# 查询特定任务状态
curl "http://localhost:8002/mcp/automation/tasks/task_1763098549.352884"
```

**任务状态响应**:
```json
{
  "success": true,
  "data": {
    "crawl_1763098549.352884": {
      "status": "completed",
      "progress": 100,
      "result": {
        "total_crawled": 156,
        "valid_posts": 142,
        "crawled_platforms": ["douyin", "weibo"]
      },
      "start_time": "2024-01-15T10:00:00Z",
      "end_time": "2024-01-15T10:05:30Z"
    }
  }
}
```

#### 4. 独立分析任务

**启动分析任务**:
```bash
# 对现有数据进行分析
curl -X POST "http://localhost:8002/mcp/automation/analysis" \
  -H "Content-Type: application/json" \
  -d '{
    "min_posts_threshold": 5,
    "trend_analysis_config": {
      "time_window": "7d",
      "min_trend_score": 0.5
    }
  }'
```

### 📈 趋势分析

#### 获取热门梗排行
```bash
# 获取24小时热门梗
curl "http://localhost:8002/mcp/trending?time_window=24h&limit=20"

# 获取周热门梗
curl "http://localhost:8002/mcp/trending?time_window=7d&limit=50"
```

#### 分析特定梗的趋势
```bash
# 分析单个梗的趋势
curl -X POST "http://localhost:8002/mcp/trend/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "meme_id": "meme_001",
    "time_window": "30d",
    "prediction_days": 7
  }'
```

### 📝 内容总结

#### 文本总结
```bash
# 总结单段文本
curl -X POST "http://localhost:8002/mcp/summarize" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "这是要总结的文本内容...",
    "summary_type": "brief",
    "max_length": 200
  }'

# 批量总结
curl -X POST "http://localhost:8002/mcp/summarize/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": ["文本1", "文本2", "文本3"],
    "summary_type": "detailed"
  }'
```

## 🖥️ 监控界面使用

### 自动化监控界面

访问 http://localhost:8501 打开自动化监控界面，该界面提供：

#### 📊 实时监控面板
- **任务状态总览**: 实时显示所有运行中的任务
- **系统资源监控**: CPU、内存、数据库状态
- **爬取统计**: 各平台数据爬取统计
- **错误日志**: 实时错误监控和报警

#### 🔧 任务管理
- **任务列表**: 显示所有历史和当前任务
- **任务详情**: 查看具体任务的执行详情和结果
- **任务控制**: 暂停、恢复、取消正在运行的任务

#### 📈 数据统计
- **知识库统计**: 总卡数、趋势分析、分类分布
- **爬取效果**: 各平台数据质量和数量统计
- **系统性能**: API响应时间、并发处理能力

### 界面功能说明

1. **概览页面**: 系统整体状态和关键指标
2. **任务监控**: 实时任务执行状态和进度
3. **数据管理**: 知识库数据的浏览和管理
4. **系统设置**: 配置参数调整和系统优化

## 🛠️ 开发指南

### 项目结构

```
meme-commons/
├── 📁 server/                    # 服务器相关
│   ├── mcp_server.py            # MCP服务器主文件
│   └── ...
├── 📁 database/                  # 数据库相关
│   ├── models.py                # 数据模型定义
│   └── ...
├── 📁 tools/                     # 工具模块
│   ├── crawler.py               # 爬取工具
│   ├── embedding.py             # 向量嵌入
│   ├── query.py                 # 查询工具
│   ├── summarizer.py            # 总结工具
│   └── trend_analysis.py        # 趋势分析
├── 📁 orchestrator/              # LLM协调器
│   ├── orchestrator.py          # 核心协调器
│   └── ...
├── 📁 automation_monitor.py      # Streamlit监控界面
├── 📁 main.py                    # 应用入口
├── 📁 config.py                  # 配置管理
├── 📁 requirements.txt           # 依赖列表
├── 📁 .env.example              # 环境配置模板
├── 📁 run.sh                    # 启动脚本
└── 📁 README.md                 # 项目文档
```

### 添加新工具模块

#### 1. 创建工具模块

在`tools/`目录下创建新的工具文件：

```python
# tools/new_tool.py
from typing import Dict, List, Any
import asyncio

class NewTool:
    """新工具模块说明"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """执行工具功能"""
        # 实现具体功能
        pass
        
    def get_capabilities(self) -> List[str]:
        """返回工具能力列表"""
        return ["capability1", "capability2"]
```

#### 2. 注册工具到协调器

在`orchestrator.py`中注册新工具：

```python
# orchestrator/orchestrator.py
from tools.new_tool import NewTool

class LLMOrchestrator:
    def __init__(self, config):
        # 注册新工具
        self.register_tool("new_tool", NewTool(config))
        
    async def execute_tool(self, tool_name: str, **kwargs):
        # 工具执行逻辑
        pass
```

#### 3. 添加API接口

在MCP服务器中添加相应接口：

```python
# server/mcp_server.py
from orchestrator import LLMOrchestrator

@app.post("/mcp/new_tool/execute")
async def execute_new_tool(request: dict):
    """新工具API接口"""
    result = await orchestrator.execute_tool("new_tool", **request)
    return {"success": True, "data": result}
```

### 自定义工作流程

#### 创建复杂工作流程

```python
# 自定义工作流程示例
workflow_config = {
    "steps": [
        {
            "step": "crawl_content",
            "tool": "crawler",
            "params": {
                "platforms": ["weibo", "douyin"],
                "keywords": ["梗文化"],
                "limit": 100
            },
            "timeout": 300
        },
        {
            "step": "clean_content",
            "tool": "cleaner",
            "depends_on": "crawl_content",
            "params": {
                "min_length": 10,
                "remove_duplicates": True
            }
        },
        {
            "step": "analyze_content", 
            "tool": "analyzer",
            "depends_on": "clean_content",
            "params": {
                "trend_threshold": 0.6,
                "generate_embeddings": True
            }
        },
        {
            "step": "generate_knowledge_cards",
            "tool": "summarizer", 
            "depends_on": "analyze_content",
            "params": {
                "card_template": "meme_template",
                "auto_approve": False
            }
        }
    ],
    "error_handling": {
        "retry_attempts": 3,
        "continue_on_error": False
    }
}

# 执行工作流程
result = await orchestrator.execute_workflow(workflow_config)
```

## 🔧 高级配置

### 数据库优化

#### SQLite优化配置
```sql
-- 启用WAL模式提高并发性能
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=10000;
PRAGMA temp_store=memory;
```

#### PostgreSQL配置（推荐生产环境）
```bash
# postgresql.conf 关键配置
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
```

### 性能调优

#### MCP服务器调优
```bash
# .env 性能相关配置
# Worker进程数量（建议CPU核心数）
WORKERS=4

# 最大连接数
MAX_CONNECTIONS=1000

# 请求超时时间（秒）
TIMEOUT=30

# 启用压缩
ENABLE_COMPRESSION=true

# 缓存配置
CACHE_TTL=3600
CACHE_MAX_SIZE=1000
```

#### 爬虫调优
```bash
# 并发控制
MAX_CONCURRENT_REQUESTS=10
REQUESTS_PER_SECOND=5

# 重试机制
MAX_RETRIES=3
RETRY_DELAY=2

# 超时设置
REQUEST_TIMEOUT=30
READ_TIMEOUT=60
```

### 监控和日志

#### 日志配置
```python
# config.py 日志配置
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
    },
    "handlers": {
        "default": {
            "level": "INFO",
            "formatter": "standard",
            "class": "logging.StreamHandler",
        },
        "file": {
            "level": "DEBUG",
            "formatter": "standard", 
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "meme_commons.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        },
    },
    "loggers": {
        "": {
            "handlers": ["default", "file"],
            "level": "DEBUG",
            "propagate": False
        }
    }
}
```

#### 监控指标
系统提供以下监控指标：

- **性能指标**: 响应时间、吞吐量、错误率
- **资源指标**: CPU、内存、磁盘使用率
- **业务指标**: 爬取成功率、知识卡生成数量
- **数据库指标**: 连接数、查询性能、索引使用率

## 🚨 故障排除

### 常见问题及解决方案

#### 1. 服务启动失败

**问题**: `Address already in use`
```bash
# 检查端口占用
lsof -i :8002
lsof -i :8501

# 终止占用进程
kill -9 <PID>

# 或使用端口重映射
export MCP_PORT=8003
export STREAMLIT_PORT=8502
```

**问题**: `Database connection failed`
```bash
# 检查数据库文件权限
ls -la meme_commons.db

# 修复权限
chmod 664 meme_commons.db

# 重新初始化数据库
rm meme_commons.db
python -c "from database.models import init_db; init_db()"
```

#### 2. 爬取功能异常

**问题**: `Cookie expired or invalid`
```bash
# 重新获取Cookie
# 1. 清除浏览器Cookie
# 2. 重新登录各平台
# 3. 更新.env文件中的Cookie配置
# 4. 重启服务
```

**问题**: `Rate limit exceeded`
```bash
# 增加请求间隔
export REQUEST_INTERVAL=3
export MAX_CONCURRENT_REQUESTS=5

# 检查平台限制策略
# 调整爬取策略
```

#### 3. API调用失败

**问题**: `Knowledge card statistics API failed`
```bash
# 检查知识库初始化
curl http://localhost:8002/mcp/status

# 重新初始化知识库
curl -X POST http://localhost:8002/mcp/knowledge/init
```

**问题**: `LLM API quota exceeded`
```bash
# 检查API配额使用情况
curl http://localhost:8002/mcp/system/usage

# 切换到备用API或等待配额重置
export DASHSCOPE_API_KEY=backup_key
```

#### 4. 监控界面问题

**问题**: `Streamlit connection failed`
```bash
# 检查Streamlit日志
tail -f streamlit.log

# 重新启动Streamlit
streamlit run automation_monitor.py --server.port 8501 --server.address 0.0.0.0 --logger.level debug
```

### 日志分析

#### 关键日志文件
```bash
# 应用日志
tail -f meme_commons.log

# MCP服务器日志
tail -f backend.log

# Streamlit日志  
tail -f frontend.log

# 爬虫详细日志
tail -f crawler.log

# 错误专用日志
grep ERROR meme_commons.log
```

#### 常见错误模式
```
ERROR [crawler] Rate limit exceeded for platform douyin
WARNING [orchestrator] Task timeout: crawl_task_123
ERROR [database] Connection pool exhausted
WARNING [llm] API response slow: 15.2s
```

### 性能问题诊断

#### 1. 系统资源检查
```bash
# CPU和内存使用
top -p $(pgrep -f "python main.py")

# 磁盘空间
df -h

# 网络连接
netstat -an | grep :8002
```

#### 2. 数据库性能
```sql
-- SQLite性能检查
PRAGMA compile_options;
PRAGMA database_list;

-- 慢查询分析
EXPLAIN QUERY PLAN SELECT * FROM knowledge_cards WHERE category = '搞笑';
```

#### 3. API性能测试
```bash
# 负载测试
ab -n 1000 -c 10 http://localhost:8002/health

# 响应时间测试
curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:8002/mcp/knowledge/stats"

# curl-format.txt 内容:
#      time_namelookup:  %{time_namelookup}\n
#         time_connect:  %{time_connect}\n
#      time_appconnect:  %{time_appconnect}\n
#     time_pretransfer:  %{time_pretransfer}\n
#        time_redirect:  %{time_redirect}\n
#   time_starttransfer:  %{time_starttransfer}\n
#                     ----------\n
#           time_total:  %{time_total}\n
```

## 🔒 安全考虑

### API安全

#### 1. 访问控制
```python
# 添加API密钥验证
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header()):
    valid_keys = ["key1", "key2"]
    if x_api_key not in valid_keys:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

@app.get("/mcp/knowledge")
async def get_knowledge(api_key: str = Depends(verify_api_key)):
    # API实现
    pass
```

#### 2. 限流配置
```python
# 限流中间件
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

@app.get("/mcp/knowledge")
@limiter.limit("100/minute")
async def get_knowledge(request: Request):
    # API实现
    pass
```

### 数据安全

#### 1. 敏感数据加密
```python
# 使用Fernet加密敏感配置
from cryptography.fernet import Fernet

# 生成密钥
key = Fernet.generate_key()
cipher_suite = Fernet(key)

# 加密Cookie等敏感数据
encrypted_cookie = cipher_suite.encrypt(b"cookie_content")

# 解密使用
decrypted_cookie = cipher_suite.decrypt(encrypted_cookie)
```

#### 2. 数据库安全
```bash
# 设置数据库文件权限
chmod 600 meme_commons.db

# 启用SQLite加密
# 在SQLite编译时启用加密支持
```

## 📊 系统维护

### 定期维护任务

#### 1. 数据库维护
```bash
# 数据库备份
cp meme_commons.db "backup_$(date +%Y%m%d_%H%M%S).db"

# 清理过期数据
curl -X POST http://localhost:8002/mcp/admin/cleanup \
  -d '{"older_than_days": 30}'

# 数据库优化
sqlite3 meme_commons.db "VACUUM;"
sqlite3 meme_commons.db "ANALYZE;"
```

#### 2. 日志轮转
```bash
# 配置logrotate
sudo cat > /etc/logrotate.d/meme-commons << EOF
/path/to/meme_commons/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 www-data www-data
}
EOF
```

#### 3. 系统监控脚本
```bash
#!/bin/bash
# monitoring.sh - 系统健康检查脚本

# 检查服务状态
check_service() {
    if ! curl -f http://localhost:8002/health > /dev/null 2>&1; then
        echo "MCP服务器异常"
        # 重启服务
        pkill -f "python main.py"
        nohup python main.py > backend.log 2>&1 &
    fi
    
    if ! curl -f http://localhost:8501 > /dev/null 2>&1; then
        echo "Streamlit服务异常"
        # 重启服务
        pkill -f "streamlit"
        nohup streamlit run automation_monitor.py --server.port 8501 --server.address 0.0.0.0 > frontend.log 2>&1 &
    fi
}

# 检查磁盘空间
check_disk() {
    USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ $USAGE -gt 90 ]; then
        echo "磁盘使用率过高: ${USAGE}%"
        # 清理日志文件
        find . -name "*.log" -mtime +7 -delete
    fi
}

# 执行检查
check_service
check_disk
```

### 性能优化

#### 1. 数据库索引优化
```sql
-- 为常用查询字段添加索引
CREATE INDEX idx_knowledge_cards_category ON knowledge_cards(category);
CREATE INDEX idx_knowledge_cards_trend_score ON knowledge_cards(trend_score);
CREATE INDEX idx_posts_platform_timestamp ON raw_posts(platform, timestamp);
CREATE INDEX idx_posts_keywords ON raw_posts(keywords);

-- 复合索引
CREATE INDEX idx_cards_category_trend ON knowledge_cards(category, trend_score);
```

#### 2. 缓存策略
```python
# Redis缓存配置
import redis
from datetime import timedelta

redis_client = redis.Redis(host='localhost', port=6379, db=0)

# 缓存热点数据
def get_cached_trending(platform, time_window):
    cache_key = f"trending:{platform}:{time_window}"
    
    # 尝试从缓存获取
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
    
    # 从数据库获取并缓存
    data = fetch_from_database(platform, time_window)
    redis_client.setex(
        cache_key, 
        timedelta(hours=1), 
        json.dumps(data)
    )
    return data
```

## 🤝 贡献指南

### 开发环境设置

1. **Fork项目**:
   ```bash
   git clone https://github.com/your-username/meme-commons.git
   cd meme-commons
   ```

2. **创建开发分支**:
   ```bash
   git checkout -b feature/amazing-feature
   ```

3. **设置pre-commit钩子**:
   ```bash
   pip install pre-commit
   pre-commit install
   ```

### 代码规范

#### Python代码风格
- 遵循PEP 8标准
- 使用Black格式化代码
- 使用isort整理导入
- 使用flake8检查代码质量

```bash
# 代码格式化
black .
isort .
flake8 .

# 类型检查
mypy .
```

#### 提交规范
```
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式修改
refactor: 代码重构
test: 测试相关
chore: 构建/工具相关
```

### 测试

#### 单元测试
```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_crawler.py

# 生成覆盖率报告
pytest --cov=. --cov-report=html
```

#### 集成测试
```bash
# 启动测试环境
./scripts/test_setup.sh

# 运行API测试
pytest tests/integration/test_api.py

# 运行端到端测试
pytest tests/e2e/
```

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

```
MIT License

Copyright (c) 2024 meme-commons contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 📞 联系方式

### 技术支持
- **项目主页**: https://github.com/your-org/meme-commons
- **问题反馈**: https://github.com/your-org/meme-commons/issues
- **讨论社区**: https://github.com/your-org/meme-commons/discussions

### 开发者
- **维护者**: meme-commons团队
- **邮箱**: meme-commons@example.com
- **官网**: https://meme-commons.org

### 社区
- **贡献者**: 感谢所有为本项目做出贡献的开发者和研究者
- **用户群体**: 梗文化研究者、数据科学家、AI工程师

## 🙏 致谢

本项目基于以下优秀的开源项目：

- [FastAPI](https://fastapi.tiangolo.com/) - 现代高性能Web框架
- [Streamlit](https://streamlit.io/) - 数据科学Web应用框架  
- [LangChain](https://github.com/langchain-ai/langchain) - LLM应用开发框架
- [SQLAlchemy](https://sqlalchemy.org/) - Python SQL工具包和ORM
- [Chroma](https://www.trychroma.com/) - 开源向量数据库
- [Requests](https://requests.readthedocs.io/) - 优雅的HTTP库

特别感谢所有梗文化研究者和开源社区的支持！

---

**🎭 meme-commons - 让梗文化研究更智能、更有趣！**

*最后更新时间: 2024年1月15日*