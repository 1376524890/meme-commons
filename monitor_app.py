#!/usr/bin/env python3
"""
meme-commons 后台监控界面
提供自动化流程执行、监控和系统配置管理功能
运行端口：8502
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
import os
import sys
from config import settings

# 配置页面
st.set_page_config(
    page_title="meme-commons 后台监控中心",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API配置
API_BASE_URL = "http://localhost:8002"

class MonitorAPI:
    """监控API客户端"""
    
    def __init__(self):
        self.api_base = API_BASE_URL
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
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
    
    def get_health_status(self) -> bool:
        """获取健康检查状态"""
        try:
            response = requests.get(f"{self.api_base}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def restart_system(self) -> Dict[str, Any]:
        """重启系统"""
        try:
            response = requests.post(f"{self.api_base}/mcp/system/restart", timeout=10)
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def clear_cache(self) -> Dict[str, Any]:
        """清理缓存"""
        try:
            response = requests.post(f"{self.api_base}/mcp/system/clear_cache", timeout=5)
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

def init_session_state():
    """初始化session state"""
    if 'auto_refresh' not in st.session_state:
        st.session_state.auto_refresh = True
    if 'refresh_interval' not in st.session_state:
        st.session_state.refresh_interval = 5  # 秒
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = datetime.now()
    if 'api_client' not in st.session_state:
        st.session_state.api_client = MonitorAPI()
    if 'expanded_task' not in st.session_state:
        st.session_state.expanded_task = None

def render_header():
    """渲染页面头部"""
    st.title("🚀 meme-commons 后台监控中心")
    st.markdown("### 自动化流程监控与系统配置管理")
    
    # 系统状态指示器
    api_client = st.session_state.api_client
    status = api_client.get_system_status()
    
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
        ["🏠 系统概览", "🔄 任务管理", "⚡ 自动化执行", "⚙️ 系统配置", "📊 数据分析"]
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
    
    # 显示最后刷新时间
    st.sidebar.markdown(f"### 🕒 最后刷新\n{st.session_state.last_refresh.strftime('%Y-%m-%d %H:%M:%S')}")
    
    return page

def render_system_overview():
    """渲染系统概览页面"""
    st.header("🏠 系统概览")
    
    api_client = st.session_state.api_client
    status = api_client.get_system_status()
    
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
    tasks = api_client.get_all_tasks()
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
    
    recent_tasks = [task for task in tasks if task.get("created_at") and \
                   datetime.fromisoformat(task["created_at"]) > recent_time][:10]
    
    if recent_tasks:
        df = pd.DataFrame(recent_tasks)
        if not df.empty:
            # 只显示重要列
            if all(col in df.columns for col in ['id', 'type', 'status', 'created_at', 'platform']):
                st.dataframe(
                    df[['id', 'type', 'status', 'created_at', 'platform']].sort_values('created_at', ascending=False),
                    use_container_width=True
                )
    else:
        st.info("过去24小时内暂无活动")

def render_task_management():
    """渲染任务管理页面"""
    st.header("🔄 任务管理")
    
    api_client = st.session_state.api_client
    tasks = api_client.get_all_tasks()
    
    if tasks:
        # 转换为DataFrame进行展示
        df = pd.DataFrame(tasks)
        
        # 添加筛选器
        st.sidebar.markdown("### 🔍 任务筛选")
        status_filter = st.sidebar.multiselect(
            "状态",
            df['status'].unique() if 'status' in df.columns else [],
            default=None
        )
        
        type_filter = st.sidebar.multiselect(
            "任务类型",
            df['type'].unique() if 'type' in df.columns else [],
            default=None
        )
        
        # 应用筛选
        if status_filter:
            df = df[df['status'].isin(status_filter)]
        if type_filter:
            df = df[df['type'].isin(type_filter)]
        
        # 显示任务列表
        st.markdown("#### 📋 任务列表")
        
        # 定义展示的列
        display_columns = []
        for col in ['id', 'type', 'status', 'created_at', 'platform', 'keywords', 'progress']:
            if col in df.columns:
                display_columns.append(col)
        
        if display_columns:
            st.dataframe(df[display_columns], use_container_width=True)
        
        # 任务详情展示
        st.markdown("#### 📝 任务详情")
        task_ids = [task.get('id') for task in tasks if task.get('id')]
        selected_task_id = st.selectbox("选择任务ID查看详情", task_ids)
        
        if selected_task_id:
            selected_task = next((task for task in tasks if task.get('id') == selected_task_id), None)
            if selected_task:
                st.json(selected_task)
                
                # 如果任务失败，显示错误信息
                if selected_task.get('status') == 'failed' and 'error' in selected_task:
                    st.error(f"错误信息: {selected_task['error']}")
    else:
        st.info("暂无任务数据")

def render_automation_execution():
    """渲染自动化执行页面"""
    st.header("⚡ 自动化执行")
    
    api_client = st.session_state.api_client
    
    # 创建任务表单
    with st.form("automation_form"):
        st.markdown("#### 📋 创建自动化任务")
        
        # 任务类型选择
        task_type = st.radio(
            "选择任务类型",
            ["🔍 单一平台爬取", "🔄 完整流程执行"]
        )
        
        # 平台选择
        platforms = ["douyin", "bilibili", "xiaohongshu", "zhihu", "weibo", "tieba"]
        platform_names = {"douyin": "抖音", "bilibili": "哔哩哔哩", "xiaohongshu": "小红书", 
                         "zhihu": "知乎", "weibo": "微博", "tieba": "百度贴吧"}
        
        if task_type == "🔍 单一平台爬取":
            platform = st.selectbox(
                "选择平台",
                platforms,
                format_func=lambda x: platform_names.get(x, x)
            )
        else:
            selected_platforms = st.multiselect(
                "选择平台（可多选）",
                platforms,
                format_func=lambda x: platform_names.get(x, x),
                default=["douyin", "bilibili"]
            )
        
        # 关键词输入
        keywords_input = st.text_input(
            "输入关键词（多个关键词用逗号分隔）",
            placeholder="例如：赤石, yyds, 绝绝子"
        )
        
        # 爬取数量限制
        limit = st.slider("爬取数量限制", 10, 200, 50)
        
        # 提交按钮
        submitted = st.form_submit_button("🚀 执行任务", type="primary")
    
    # 处理表单提交
    if submitted:
        # 处理关键词
        keywords = [k.strip() for k in keywords_input.split(',') if k.strip()]
        
        if not keywords:
            st.error("请至少输入一个关键词")
            return
        
        with st.spinner("正在提交任务..."):
            if task_type == "🔍 单一平台爬取":
                result = api_client.submit_crawl_task(platform, keywords, limit)
            else:
                result = api_client.submit_full_pipeline_task(selected_platforms, keywords, limit)
            
            if result.get("success", False):
                st.success(f"✅ 任务提交成功！任务ID: {result.get('task_id')}")
                st.balloons()
            else:
                st.error(f"❌ 任务提交失败: {result.get('error', '未知错误')}")
    
    # 最近执行的任务
    st.markdown("#### 🕒 最近执行的任务")
    tasks = api_client.get_all_tasks()
    recent_tasks = sorted(tasks, key=lambda x: x.get('created_at', ''), reverse=True)[:5]
    
    if recent_tasks:
        for task in recent_tasks:
            with st.expander(f"任务 {task.get('id')} - {task.get('type')} - {task.get('status')}"):
                st.json(task)
    else:
        st.info("暂无执行历史")

def render_system_configuration():
    """渲染系统配置页面"""
    st.header("⚙️ 系统配置管理")
    
    # 系统信息展示
    st.markdown("#### 📊 系统信息")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Python版本**: {sys.version}")
        st.write(f"**系统平台**: {sys.platform}")
        st.write(f"**当前时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    with col2:
        st.write(f"**API基础URL**: {API_BASE_URL}")
        st.write(f"**数据库URL**: {settings.DATABASE_URL}")
        st.write(f"**向量数据库URL**: {settings.VECTOR_DB_URL}")
    
    # 系统操作
    st.markdown("#### 🛠️ 系统操作")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 重启系统", type="primary", use_container_width=True):
            st.warning("系统重启将暂时中断服务，是否确认？")
            if st.button("✅ 确认重启", type="secondary", use_container_width=True):
                with st.spinner("正在重启系统..."):
                    result = st.session_state.api_client.restart_system()
                    if result.get("success", False):
                        st.success("系统重启命令已发送")
                    else:
                        st.error(f"重启失败: {result.get('error', '未知错误')}")
    
    with col2:
        if st.button("🧹 清理缓存", use_container_width=True):
            with st.spinner("正在清理缓存..."):
                result = st.session_state.api_client.clear_cache()
                if result.get("success", False):
                    st.success("缓存清理成功")
                else:
                    st.error(f"清理失败: {result.get('error', '未知错误')}")
    
    # 配置信息展示
    st.markdown("#### ⚙️ 配置信息")
    
    # 数据库配置
    st.markdown("##### 🗄️ 数据库配置")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("数据库URL", value=settings.DATABASE_URL, disabled=True)
    with col2:
        st.text_input("缓存URL", value=settings.CACHE_URL, disabled=True)
    
    # API配置
    st.markdown("##### 🔌 API配置")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("DashScope API Key", value="***" if settings.DASHSCOPE_API_KEY else "未设置", disabled=True)
        st.text_input("LLM模型", value=settings.DASHSCOPE_LLM_MODEL, disabled=True)
    with col2:
        st.text_input("嵌入模型", value=settings.DASHSCOPE_EMBEDDING_MODEL, disabled=True)
        st.text_input("嵌入维度", value=settings.EMBEDDING_DIMENSION, disabled=True)
    
    # 爬虫配置
    st.markdown("##### 🕷️ 爬虫配置")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("最大爬取页数", value=settings.MAX_CRAWL_PAGES, disabled=True)
        st.text_input("最大爬取项目数", value=settings.MAX_CRAWL_ITEMS, disabled=True)
    with col2:
        st.text_input("爬取超时(秒)", value=settings.CRAWL_TIMEOUT, disabled=True)
        st.text_input("缓存TTL(秒)", value=settings.CACHE_TTL, disabled=True)

def render_data_analysis():
    """渲染数据分析页面"""
    st.header("📊 数据分析")
    
    api_client = st.session_state.api_client
    stats = api_client.get_knowledge_cards_stats()
    
    if stats.get("success", False):
        data = stats.get("data", {})
        
        # 数据概览
        st.markdown("#### 📈 数据概览")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("总知识卡", data.get("total_cards", 0))
        with col2:
            st.metric("今日新增", data.get("today_cards", 0))
        with col3:
            st.metric("本周新增", data.get("week_cards", 0))
        with col4:
            st.metric("平均热度", data.get("avg_trend_score", 0))
        
        # 平台分布
        st.markdown("#### 🌐 平台分布")
        platform_data = data.get("platform_distribution", {})
        if platform_data:
            fig = px.pie(
                values=list(platform_data.values()),
                names=list(platform_data.keys()),
                title="知识卡平台来源分布"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # 热度趋势
        st.markdown("#### 📈 热度趋势")
        trend_data = data.get("trend_history", [])
        if trend_data:
            df = pd.DataFrame(trend_data)
            if 'date' in df.columns and 'avg_trend' in df.columns:
                fig = px.line(df, x='date', y='avg_trend', title='平均热度趋势')
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("暂无数据分析数据")

def main():
    """主函数"""
    init_session_state()
    
    # 渲染头部
    render_header()
    
    # 渲染侧边栏和主要内容
    page = render_sidebar()
    
    # 页面内容
    if page == "🏠 系统概览":
        render_system_overview()
    elif page == "🔄 任务管理":
        render_task_management()
    elif page == "⚡ 自动化执行":
        render_automation_execution()
    elif page == "⚙️ 系统配置":
        render_system_configuration()
    elif page == "📊 数据分析":
        render_data_analysis()
    
    # 更新最后刷新时间
    st.session_state.last_refresh = datetime.now()
    
    # 设置自动刷新
    if st.session_state.auto_refresh:
        st.empty()  # 占位符
        st.markdown(f"*自动刷新: {st.session_state.refresh_interval}秒*")
        st.rerun()

if __name__ == "__main__":
    main()