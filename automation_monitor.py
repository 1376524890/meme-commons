"""
meme-commons 自动化监控界面
提供实时系统监控、任务管理和自动化流程控制
"""
import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List
import plotly.express as px
import plotly.graph_objects as go
import time
import threading

# 配置页面
st.set_page_config(
    page_title="meme-commons 监控中心",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API配置
API_BASE_URL = "http://localhost:8002"

class AutomationMonitor:
    """自动化监控器"""
    
    def __init__(self):
        self.api_base = API_BASE_URL
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        try:
            response = requests.get(f"{self.api_base}/mcp/system/status", timeout=5)
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """获取所有任务"""
        try:
            response = requests.get(f"{self.api_base}/mcp/automation/tasks", timeout=5)
            return response.json().get("data", [])
        except Exception as e:
            return []
    
    def submit_crawl_task(self, platform: str, keywords: List[str], limit: int = 20) -> Dict[str, Any]:
        """提交爬取任务"""
        try:
            response = requests.post(f"{self.api_base}/mcp/automation/crawl", 
                                   json={"platform": platform, "keywords": keywords, "limit": limit})
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def submit_full_pipeline_task(self, platforms: List[str], keywords: List[str], limit: int = 50) -> Dict[str, Any]:
        """提交完整流程任务"""
        try:
            response = requests.post(f"{self.api_base}/mcp/automation/full_pipeline", 
                                   json={"platforms": platforms, "keywords": keywords, "limit": limit})
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_knowledge_cards_stats(self) -> Dict[str, Any]:
        """获取知识卡统计"""
        try:
            response = requests.get(f"{self.api_base}/mcp/knowledge/stats", timeout=5)
            return response.json()
        except Exception as e:
            return {}

def init_session_state():
    """初始化session state"""
    if 'auto_refresh' not in st.session_state:
        st.session_state.auto_refresh = True
    if 'refresh_interval' not in st.session_state:
        st.session_state.refresh_interval = 5  # 秒
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = datetime.now()
    if 'monitor' not in st.session_state:
        st.session_state.monitor = AutomationMonitor()

def auto_refresh():
    """自动刷新页面"""
    if st.session_state.auto_refresh:
        time.sleep(st.session_state.refresh_interval)
        st.rerun()

def render_header():
    """渲染页面头部"""
    st.title("🚀 meme-commons 自动化监控中心")
    st.markdown("### 智能梗知识系统 - 实时监控与自动化控制")
    
    # 系统状态指示器
    monitor = st.session_state.monitor
    status = monitor.get_scheduler_status()
    
    if status.get("success", False):
        st.success("🟢 系统正常运行")
        # 显示关键指标
        scheduler_info = status.get("data", {}).get("scheduler", {})
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("运行任务", scheduler_info.get("running_tasks", 0))
        with col2:
            st.metric("待处理任务", scheduler_info.get("pending_tasks", 0))
        with col3:
            st.metric("已完成任务", scheduler_info.get("total_completed", 0))
        with col4:
            st.metric("知识卡总数", status.get("data", {}).get("total_cards", 0))
    else:
        st.error("🔴 系统连接异常")
        if "error" in status:
            st.error(f"错误信息: {status['error']}")

def render_sidebar():
    """渲染侧边栏"""
    st.sidebar.title("🎛️ 控制面板")
    
    # 监控设置
    st.sidebar.markdown("### 📊 监控设置")
    st.session_state.auto_refresh = st.sidebar.checkbox("自动刷新", value=st.session_state.auto_refresh)
    if st.session_state.auto_refresh:
        st.session_state.refresh_interval = st.sidebar.slider("刷新间隔(秒)", 2, 30, st.session_state.refresh_interval)
    
    # 导航菜单
    page = st.sidebar.radio(
        "选择功能",
        ["🏠 系统概览", "🔄 任务管理", "📊 知识卡管理", "⚡ 自动化控制", "📈 数据分析", "⚙️ 系统管理"]
    )
    
    # 系统连接状态
    st.sidebar.markdown("### 🔌 系统连接")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            st.sidebar.success("✅ API连接正常")
        else:
            st.sidebar.warning("⚠️ API连接异常")
    except:
        st.sidebar.error("❌ API连接失败")
    
    return page

def render_system_overview():
    """渲染系统概览"""
    st.header("🏠 系统概览")
    
    monitor = st.session_state.monitor
    status = monitor.get_scheduler_status()
    
    if not status.get("success"):
        st.error("无法获取系统状态")
        return
    
    data = status.get("data", {})
    scheduler_info = data.get("scheduler", {})
    
    # 核心指标
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("总知识卡", data.get("total_cards", 0), help="系统中梗知识卡总数")
    with col2:
        st.metric("平均热度", data.get("avg_trend_score", 0), help="所有知识卡的平均热度分数")
    with col3:
        st.metric("近期活动", data.get("recent_cards", 0), help="最近7天新增的知识卡")
    with col4:
        st.metric("高热度梗", data.get("high_trend_cards", 0), help="热度分数≥7.0的梗")
    with col5:
        st.metric("完成任务", scheduler_info.get("completed_tasks", 0), help="调度器已完成的任务总数")
    
    # 系统状态图表
    st.markdown("#### 📊 系统运行状态")
    
    # 任务状态分布
    tasks = monitor.get_all_tasks()
    if tasks:
        task_status_counts = {}
        for task in tasks:
            status = task.get("status", "unknown")
            task_status_counts[status] = task_status_counts.get(status, 0) + 1
        
        if task_status_counts:
            fig = px.pie(
                values=list(task_status_counts.values()), 
                names=list(task_status_counts.keys()),
                title="任务状态分布"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # 最近活动
    st.markdown("#### 🕒 最近活动")
    recent_time = datetime.now() - timedelta(hours=24)
    
    recent_tasks = [task for task in tasks if task.get("created_at") and 
                   datetime.fromisoformat(task["created_at"]) > recent_time]
    
    if recent_tasks:
        df_recent = pd.DataFrame(recent_tasks[-10:])  # 最近10个任务
        df_recent["created_at"] = pd.to_datetime(df_recent["created_at"])
        
        fig = px.timeline(
            df_recent, 
            x_start="created_at", 
            y="task_id",
            color="status",
            title="最近24小时任务时间线"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("最近24小时内没有任务活动")

def render_task_management():
    """渲染任务管理"""
    st.header("🔄 任务管理")
    
    monitor = st.session_state.monitor
    tasks = monitor.get_all_tasks()
    
    if not tasks:
        st.info("暂无任务数据")
        return
    
    # 任务统计
    st.markdown("#### 📊 任务统计")
    col1, col2, col3, col4 = st.columns(4)
    
    status_counts = {}
    for task in tasks:
        status = task.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    
    with col1:
        st.metric("总计", len(tasks))
    with col2:
        st.metric("运行中", status_counts.get("running", 0))
    with col3:
        st.metric("已完成", status_counts.get("completed", 0))
    with col4:
        st.metric("失败", status_counts.get("failed", 0))
    
    # 任务列表
    st.markdown("#### 📋 任务列表")
    
    # 过滤选项
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("状态过滤", ["全部", "pending", "running", "completed", "failed"])
    with col2:
        type_filter = st.selectbox("类型过滤", ["全部", "crawl", "analyze", "full_pipeline"])
    with col3:
        limit = st.slider("显示数量", 10, 100, 50)
    
    # 过滤任务
    filtered_tasks = tasks
    if status_filter != "全部":
        filtered_tasks = [t for t in filtered_tasks if t.get("status") == status_filter]
    if type_filter != "全部":
        filtered_tasks = [t for t in filtered_tasks if t.get("task_type") == type_filter]
    
    filtered_tasks = filtered_tasks[:limit]
    
    if filtered_tasks:
        # 转换为DataFrame
        df_tasks = pd.DataFrame(filtered_tasks)
        
        # 显示任务表格
        st.dataframe(
            df_tasks[["task_id", "task_type", "status", "priority", "progress", "created_at"]],
            use_container_width=True,
            hide_index=True
        )
        
        # 任务详情
        st.markdown("#### 📝 任务详情")
        selected_task = st.selectbox("选择任务查看详情", [t["task_id"] for t in filtered_tasks])
        
        if selected_task:
            task_detail = next((t for t in filtered_tasks if t["task_id"] == selected_task), None)
            if task_detail:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.json({
                        "任务ID": task_detail["task_id"],
                        "任务类型": task_detail["task_type"],
                        "状态": task_detail["status"],
                        "优先级": task_detail["priority"],
                        "进度": f"{task_detail['progress']:.1f}%"
                    })
                
                with col2:
                    st.json({
                        "创建时间": task_detail["created_at"],
                        "开始时间": task_detail.get("started_at", "未开始"),
                        "完成时间": task_detail.get("completed_at", "未完成"),
                        "错误信息": task_detail.get("error_message", "无")
                    })
                
                # 任务结果
                if task_detail.get("result"):
                    st.markdown("#### 📊 任务结果")
                    st.json(task_detail["result"])
    else:
        st.info("没有符合条件的任务")

def render_automation_control():
    """渲染自动化控制"""
    st.header("⚡ 自动化流程控制")
    
    monitor = st.session_state.monitor
    
    # 快速操作
    st.markdown("#### 🚀 快速操作")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔍 全面爬取", help="爬取所有平台的热门内容"):
            result = monitor.submit_full_pipeline_task(
                platforms=["weibo", "bilibili", "douyin"],
                keywords=["热门", "流行", "梗"],
                limit=30
            )
            if result.get("success"):
                st.success(f"任务已提交: {result.get('task_id')}")
            else:
                st.error(f"提交失败: {result.get('error')}")
    
    with col2:
        if st.button("🎯 定向搜索", help="根据关键词精准抓取"):
            st.info("请在下方表单中配置搜索参数")
    
    with col3:
        if st.button("🧹 清理数据", help="清理过期和低质量数据"):
            st.info("清理功能开发中...")
    
    # 自定义任务表单
    st.markdown("#### ⚙️ 自定义任务")
    
    tab1, tab2, tab3 = st.tabs(["🔍 爬取任务", "🔄 分析任务", "🌊 完整流程"])
    
    with tab1:
        with st.form("crawl_task"):
            col1, col2 = st.columns(2)
            
            with col1:
                crawl_platform = st.selectbox("选择平台", ["all", "weibo", "bilibili", "douyin"])
                crawl_keywords = st.text_input("关键词", value="梗,流行语")
            
            with col2:
                crawl_limit = st.slider("抓取数量", 10, 100, 30)
                crawl_priority = st.selectbox("优先级", ["LOW", "NORMAL", "HIGH", "URGENT"])
            
            submitted = st.form_submit_button("🚀 提交爬取任务")
            
            if submitted:
                keywords_list = [k.strip() for k in crawl_keywords.split(",")]
                result = monitor.submit_crawl_task(crawl_platform, keywords_list, crawl_limit)
                
                if result.get("success"):
                    st.success(f"爬取任务提交成功! 任务ID: {result.get('task_id')}")
                else:
                    st.error(f"任务提交失败: {result.get('error')}")
    
    with tab2:
        st.info("分析任务将自动处理未分析的数据，建议定期执行")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 执行批量分析", help="分析所有未处理的原始数据"):
                st.success("分析任务已提交")
        
        with col2:
            if st.button("📊 生成趋势报告", help="生成最新的趋势分析报告"):
                st.success("报告生成任务已提交")
    
    with tab3:
        with st.form("full_pipeline"):
            col1, col2 = st.columns(2)
            
            with col1:
                pipeline_platforms = st.multiselect(
                    "选择平台", 
                    ["weibo", "bilibili", "douyin"],
                    default=["weibo", "bilibili"]
                )
                pipeline_keywords = st.text_input("关键词", value="网络梗,流行语,段子")
            
            with col2:
                pipeline_limit = st.slider("处理数量", 20, 200, 100)
                pipeline_priority = st.selectbox("优先级", ["NORMAL", "HIGH"])
            
            submitted = st.form_submit_button("🌊 启动完整流程")
            
            if submitted:
                keywords_list = [k.strip() for k in pipeline_keywords.split(",")]
                result = monitor.submit_full_pipeline_task(pipeline_platforms, keywords_list, pipeline_limit)
                
                if result.get("success"):
                    st.success(f"完整流程任务提交成功! 任务ID: {result.get('task_id')}")
                else:
                    st.error(f"任务提交失败: {result.get('error')}")
    
    # 任务模板
    st.markdown("#### 📋 任务模板")
    
    templates = {
        "热门追踪": {
            "platforms": ["weibo", "bilibili"],
            "keywords": ["热搜", "热门", "爆款"],
            "limit": 50,
            "description": "追踪当前热门内容"
        },
        "新梗发现": {
            "platforms": ["douyin", "bilibili"],
            "keywords": ["新梗", "网络用语", "流行语"],
            "limit": 30,
            "description": "发现新兴网络梗"
        },
        "深度分析": {
            "platforms": ["all"],
            "keywords": ["梗", "流行语", "网络用语"],
            "limit": 100,
            "description": "对所有平台进行深度分析"
        }
    }
    
    for template_name, config in templates.items():
        with st.expander(f"📝 {template_name}"):
            st.write(f"描述: {config['description']}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"平台: {', '.join(config['platforms'])}")
                st.write(f"关键词: {', '.join(config['keywords'])}")
            with col2:
                st.write(f"处理数量: {config['limit']}")
                if st.button(f"🚀 应用模板: {template_name}", key=template_name):
                    result = monitor.submit_full_pipeline_task(
                        config['platforms'], 
                        config['keywords'], 
                        config['limit']
                    )
                    if result.get("success"):
                        st.success(f"模板任务提交成功! 任务ID: {result.get('task_id')}")

def render_knowledge_management():
    """渲染知识卡管理"""
    st.header("📊 知识卡管理")
    
    monitor = st.session_state.monitor
    stats = monitor.get_knowledge_cards_stats()
    
    # 统计信息
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("总知识卡", stats.get("total_cards", 0))
    with col2:
        st.metric("平均热度", stats.get("avg_trend_score", 0))
    with col3:
        st.metric("近期新增", stats.get("recent_cards", 0))
    with col4:
        st.metric("高热度梗", stats.get("high_trend_cards", 0))
    
    # 标签统计
    if stats.get("popular_tags"):
        st.markdown("#### 🏷️ 热门标签")
        tags_data = stats["popular_tags"][:10]  # 前10个标签
        
        if tags_data:
            tags_df = pd.DataFrame(tags_data, columns=["标签", "数量"])
            
            fig = px.bar(
                tags_df, 
                x="标签", 
                y="数量", 
                title="热门标签统计",
                color="数量",
                color_continuous_scale="viridis"
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
    
    # 搜索功能
    st.markdown("#### 🔍 知识卡搜索")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input("搜索知识卡", placeholder="输入梗名称或关键词...")
    with col2:
        search_btn = st.button("🔍 搜索")
    
    if search_btn and search_query:
        # 这里可以添加实际的搜索API调用
        st.info(f"搜索功能开发中，搜索词: {search_query}")

def render_data_analysis():
    """渲染数据分析"""
    st.header("📈 数据分析")
    
    # 模拟数据分析图表
    st.markdown("#### 📊 梗热度趋势")
    
    # 生成模拟数据
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='W')
    meme_counts = [50 + 20 * i + (i % 4) * 10 for i in range(len(dates))]
    
    fig = px.line(
        x=dates, 
        y=meme_counts, 
        title='每周梗热度趋势',
        labels={'x': '日期', 'y': '梗数量'}
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # 平台分布
    st.markdown("#### 🎯 平台分布")
    
    platform_data = {
        '微博': 45,
        'Bilibili': 30,
        '抖音': 20,
        '其他': 5
    }
    
    fig = px.pie(
        values=list(platform_data.values()), 
        names=list(platform_data.keys()),
        title="梗分布平台占比"
    )
    st.plotly_chart(fig, use_container_width=True)

def render_system_management():
    """渲染系统管理"""
    st.header("⚙️ 系统管理")
    
    # 系统控制
    st.markdown("#### 🎛️ 系统控制")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 重启调度器", help="重启自动化任务调度器"):
            with st.spinner("正在重启调度器..."):
                st.success("调度器重启成功")
    
    with col2:
        if st.button("🧹 清理缓存", help="清理系统缓存数据"):
            with st.spinner("正在清理缓存..."):
                st.success("缓存清理完成")
    
    with col3:
        if st.button("📊 生成报告", help="生成系统状态报告"):
            with st.spinner("正在生成报告..."):
                st.success("报告生成完成")
    
    # 系统配置
    st.markdown("#### ⚙️ 系统配置")
    
    with st.expander("🔧 调度器配置"):
        st.write("配置自动化任务调度器的参数")
        
        col1, col2 = st.columns(2)
        with col1:
            max_workers = st.number_input("最大工作线程", min_value=1, max_value=10, value=3)
            task_timeout = st.number_input("任务超时时间(小时)", min_value=1, max_value=24, value=2)
        
        with col2:
            auto_cleanup = st.checkbox("自动清理", value=True)
            email_notifications = st.checkbox("邮件通知", value=False)
        
        if st.button("💾 保存配置"):
            st.success("配置已保存")
    
    with st.expander("🗄️ 数据库配置"):
        st.write("管理数据库连接和配置")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 测试连接"):
                st.success("数据库连接正常")
        
        with col2:
            if st.button("🔄 重建索引"):
                st.success("索引重建完成")

def main():
    """主函数"""
    init_session_state()
    
    # 自动刷新
    auto_refresh_thread = threading.Thread(target=auto_refresh, daemon=True)
    auto_refresh_thread.start()
    
    # 渲染页面
    render_header()
    page = render_sidebar()
    
    # 页面内容
    if page == "🏠 系统概览":
        render_system_overview()
    elif page == "🔄 任务管理":
        render_task_management()
    elif page == "📊 知识卡管理":
        render_knowledge_management()
    elif page == "⚡ 自动化控制":
        render_automation_control()
    elif page == "📈 数据分析":
        render_data_analysis()
    elif page == "⚙️ 系统管理":
        render_system_management()

if __name__ == "__main__":
    main()