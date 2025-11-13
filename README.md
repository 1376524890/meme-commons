# meme-commons — LLM Orchestrated Meme Intelligence System

梗文化智能系统是一个基于LLM编排的梗文化情报收集、分析和查询系统。

## 功能特性

- **多平台爬取**: 支持Reddit、Twitter、微博等平台的梗文化内容爬取
- **智能嵌入**: 使用先进的文本嵌入技术进行语义搜索
- **趋势分析**: 实时分析梗文化的热度趋势和演进方向
- **自动总结**: 基于LLM的智能内容总结和知识卡生成
- **向量搜索**: 高效的向量相似性搜索
- **REST API**: 提供完整的API接口服务

## 系统架构

```
用户/API请求 → MCP服务器 → LLM协调器 → 各工具模块 → 数据库+向量存储
```

## 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt

# 复制环境配置
cp .env.example .env

# 编辑配置文件
vim .env
```

### 2. 配置环境变量

在`.env`文件中配置必要的API密钥和数据库信息：

```bash
# 数据库配置
DATABASE_URL=sqlite:///meme_commons.db

# Dashscope API配置
DASHSCOPE_API_KEY=your_api_key_here

# MCP服务器配置
MCP_HOST=0.0.0.0
MCP_PORT=8080
```

### 3. 启动系统

```bash
# 启动完整系统
python -m meme_commons.main

# 或者直接运行
python main.py
```

### 4. API使用示例

#### 查询梗知识
```bash
curl "http://localhost:8080/mcp/knowledge?q=梗文化&limit=10"
```

#### 获取热门梗
```bash
curl "http://localhost:8080/mcp/trending?time_window=24h&limit=20"
```

#### 分析梗趋势
```bash
curl -X POST "http://localhost:8080/mcp/trend/analyze" \
  -H "Content-Type: application/json" \
  -d '{"meme_id": "some_meme_id", "time_window": "7d"}'
```

#### 总结内容
```bash
curl -X POST "http://localhost:8080/mcp/summarize" \
  -H "Content-Type: application/json" \
  -d '{"content": "要总结的内容"}'
```

#### 爬取平台内容
```bash
curl -X POST "http://localhost:8080/mcp/crawl" \
  -H "Content-Type: application/json" \
  -d '{"platforms": ["reddit"], "keywords": ["meme"], "limit": 100}'
```

## 模块说明

### 核心模块

- **Config** (`config.py`): 系统配置管理
- **Database** (`database/models.py`): 数据模型和数据库管理
- **VectorStore** (`vector_store.py`): 向量存储和相似性搜索
- **LLMOrchestrator** (`orchestrator.py`): 核心协调器，调度各工具

### 工具模块

- **Crawler** (`tools/crawler.py`): 多平台内容爬取
- **Embedding** (`tools/embedding.py`): 文本嵌入和向量化
- **Query** (`tools/query.py`): 知识库查询和搜索
- **Summarizer** (`tools/summarizer.py`): 基于LLM的内容总结
- **TrendAnalysis** (`tools/trend_analysis.py`): 趋势分析和预测

### 服务模块

- **MCPServer** (`server/mcp_server.py`): HTTP API服务器

## 数据结构

### MemeCard (梗知识卡)
```json
{
  "id": "唯一标识",
  "name": "梗名称",
  "description": "梗描述",
  "category": "分类",
  "keywords": ["关键词1", "关键词2"],
  "source_platforms": ["reddit", "twitter"],
  "embedding": [0.1, 0.2, ...],
  "popularity_score": 0.85,
  "trend_score": 0.73,
  "last_updated": "2024-01-01T00:00:00",
  "is_active": true
}
```

### RawPost (原始帖子)
```json
{
  "id": "唯一标识",
  "platform": "reddit",
  "post_id": "平台帖子ID",
  "author": "作者",
  "content": "帖子内容",
  "url": "帖子链接",
  "upvotes": 100,
  "downvotes": 5,
  "comment_count": 25,
  "timestamp": "2024-01-01T00:00:00",
  "keywords": ["关键词"]
}
```

## API参考

### 核心接口

- `GET /mcp/knowledge?q=<query>&limit=<limit>`: 查询梗知识
- `GET /mcp/trending?time_window=<window>&limit=<count>`: 获取热门梗
- `POST /mcp/trend/analyze`: 分析梗趋势
- `POST /mcp/summarize`: 总结内容
- `POST /mcp/crawl`: 爬取平台内容

### 系统接口

- `GET /health`: 健康检查
- `GET /mcp/status`: 系统状态
- `GET /mcp/categories`: 获取分类
- `GET /mcp/meme/{id}`: 获取梗详情
- `POST /mcp/compare`: 比较梗信息

## 开发指南

### 添加新工具

1. 在`tools/`目录下创建新工具模块
2. 实现工具类，包含必要的功能方法
3. 在`orchestrator.py`中注册新工具
4. 在MCP服务器中添加相应的API接口

### 自定义工作流程

可以使用协调器的工作流程功能：

```python
workflow_steps = [
    {
        "step": "crawl_content",
        "tool": "crawler",
        "params": {"keywords": ["meme"], "platforms": ["reddit"]}
    },
    {
        "step": "summarize_content", 
        "tool": "summarizer",
        "data_from_previous": "crawl_content"
    }
]

result = await orchestrator.execute_workflow(workflow_steps)
```

## 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

如有问题或建议，请提交 Issue 或联系开发团队。

---

**meme-commons** - 让梗文化更有趣 🎭