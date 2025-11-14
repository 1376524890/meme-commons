#!/usr/bin/env python3
"""
meme-commons Streamlit前端应用
梗知识查询和控制台界面
"""

import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List
import plotly.express as px
import plotly.graph_objects as go

# 配置页面
st.set_page_config(
    page_title="meme-commons - 梗知识智能系统",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API配置
API_BASE_URL = "http://localhost:8002"

class MemeCommonsAPI:
    """meme-commons API客户端"""
    
    @staticmethod
    def get_knowledge(query: str) -> Dict[str, Any]:
        """获取梗知识卡"""
        try:
            response = requests.get(f"{API_BASE_URL}/mcp/knowledge", params={"q": query})
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"获取梗知识失败: {e}")
            return {}
    
    @staticmethod
    def search_memes(query: str, limit: int = 10) -> Dict[str, Any]:
        """搜索梗"""
        try:
            response = requests.post(f"{API_BASE_URL}/mcp/search", 
                                   json={"query": query, "limit": limit})
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"搜索梗失败: {e}")
            return {}
    
    @staticmethod
    def get_trending(limit: int = 20) -> Dict[str, Any]:
        """获取热门梗"""
        try:
            response = requests.get(f"{API_BASE_URL}/mcp/trending", params={"limit": limit})
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"获取热门梗失败: {e}")
            return {}
    
    @staticmethod
    def get_categories() -> Dict[str, Any]:
        """获取梗分类"""
        try:
            response = requests.get(f"{API_BASE_URL}/mcp/categories")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"获取梗分类失败: {e}")
            return {}
    
    @staticmethod
    def get_system_status() -> Dict[str, Any]:
        """获取系统状态"""
        try:
            response = requests.get(f"{API_BASE_URL}/mcp/status")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"获取系统状态失败: {e}")
            return {}

def init_session_state():
    """初始化session state"""
    if 'search_history' not in st.session_state:
        st.session_state.search_history = []
    if 'favorite_memes' not in st.session_state:
        st.session_state.favorite_memes = []

def render_header():
    """渲染页面头部"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("🧠 meme-commons")
        st.markdown("### LLM Orchestrated Meme Intelligence System")
        st.markdown("---")
        
        # 系统状态指示器
        status = MemeCommonsAPI.get_system_status()
        if status.get('success', False):
            st.success("🟢 系统正常运行")
        else:
            st.error("🔴 系统异常")

def render_sidebar():
    """渲染侧边栏"""
    st.sidebar.title("🎛️ 控制面板")
    
    # 导航菜单
    page = st.sidebar.radio(
        "选择功能",
        ["🔍 梗知识查询", "📊 热门梗", "🔎 高级搜索", "📈 数据分析"]
    )
    
    # API连接状态
    st.sidebar.markdown("### 🔌 API连接")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            st.sidebar.success("✅ 已连接")
        else:
            st.sidebar.warning("⚠️ 连接异常")
    except:
        st.sidebar.error("❌ 连接失败")
    
    # 后台监控链接
    st.sidebar.markdown("### 🔧 管理入口")
    st.sidebar.markdown("[后台监控界面](http://localhost:8502) - 用于系统配置和管理")
    
    # 用户偏好设置
    st.sidebar.markdown("### ⚙️ 偏好设置")
    theme = st.sidebar.selectbox("主题", ["深色", "浅色"])
    language = st.sidebar.selectbox("语言", ["中文", "English"])
    
    return page

def render_knowledge_search():
    """渲染梗知识查询界面"""
    st.header("🔍 梗知识查询")
    
    # 搜索输入
    col1, col2 = st.columns([4, 1])
    with col1:
        query = st.text_input("输入梗的名称或关键词", placeholder="例如：赤石、yyds、绝绝子...")
    with col2:
        search_btn = st.button("🔍 查询", type="primary")
    
    # 示例查询
    st.markdown("#### 💡 热门查询")
    example_queries = ["赤石", "yyds", "绝绝子", "躺平", "内卷", "社死"]
    cols = st.columns(len(example_queries))
    
    for i, example in enumerate(example_queries):
        with cols[i]:
            if st.button(example, key=f"example_{i}"):
                query = example
                search_btn = True
    
    # 执行搜索
    if search_btn and query:
        with st.spinner("正在查询梗知识..."):
            result = MemeCommonsAPI.get_knowledge(query)
            
            if result:
                st.session_state.search_history.append({
                    "query": query,
                    "timestamp": datetime.now().isoformat(),
                    "result": result
                })
                
                render_knowledge_card(result)
            else:
                st.warning("未找到相关梗知识")
    
    # 搜索历史
    if st.session_state.search_history:
        st.markdown("#### 📜 搜索历史")
        for item in reversed(st.session_state.search_history[-5:]):
            with st.expander(f"🔍 {item['query']} - {item['timestamp'][:19]}"):
                render_knowledge_card(item['result'])

def render_knowledge_card(knowledge: Dict[str, Any]):
    """渲染知识卡"""
    if not knowledge:
        return
    
    # 主卡片
    with st.container():
        st.markdown("---")
        
        # 标题和基本信息
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader(f"📝 {knowledge.get('title', '未知梗')}")
            st.caption(f"趋势分数: {knowledge.get('trend_score', 0):.2f}")
        with col2:
            st.metric("🔥 热度", f"{knowledge.get('trend_score', 0):.1f}")
        
        # 起源和含义
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 🌟 起源")
            origin = knowledge.get('origin', '暂无信息')
            st.write(origin if origin else "暂无信息")
        
        with col2:
            st.markdown("#### 💡 含义")
            meaning = knowledge.get('meaning', '暂无信息')
            st.write(meaning if meaning else "暂无信息")
        
        # 示例
        if knowledge.get('examples'):
            st.markdown("#### 📖 使用示例")
            examples = knowledge.get('examples', [])
            if isinstance(examples, list):
                for i, example in enumerate(examples[:3]):
                    st.write(f"• {example}")
            else:
                st.write(examples)
        
        # 元信息
        last_updated = knowledge.get('last_updated', '')
        if last_updated:
            st.caption(f"🕒 最后更新: {last_updated[:19]}")
        
        # 操作按钮
        col1, col2, col3 = st.columns(3)
        
        # 生成唯一标识符确保按钮key不重复
        knowledge_id = knowledge.get('id', 'unknown')
        title = knowledge.get('title', 'untitled')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_suffix = f"{title}_{knowledge_id}_{timestamp}"
        
        with col1:
            if st.button("⭐ 收藏", key=f"favorite_{unique_suffix}"):
                st.success("已添加到收藏")
                st.session_state.favorite_memes.append({
                    'id': knowledge_id,
                    'title': title,
                    'timestamp': datetime.now().isoformat()
                })
        with col2:
            if st.button("📤 分享", key=f"share_{unique_suffix}"):
                st.info("分享链接已复制")
        with col3:
            if st.button("🔄 刷新", key=f"refresh_{unique_suffix}"):
                st.rerun()

def render_trending():
    """渲染热门梗界面"""
    st.header("📊 热门梗排行榜")
    
    # 获取热门梗
    with st.spinner("正在获取热门梗..."):
        trending_data = MemeCommonsAPI.get_trending(limit=20)
    
    if trending_data and trending_data.get('success'):
        data = trending_data.get('data', [])
        
        if data:
            # 数据表格
            st.markdown("#### 📋 热门梗列表")
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
            
            # 趋势图表
            if 'trend_score' in df.columns:
                st.markdown("#### 📈 热度趋势图")
                fig = px.bar(df, x='title', y='trend_score', 
                           title='梗热度排行', 
                           labels={'trend_score': '热度分数', 'title': '梗名称'})
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("暂无热门梗数据")
    else:
        st.error("获取热门梗数据失败")

def render_advanced_search():
    """渲染高级搜索界面"""
    st.header("🔎 高级搜索")
    
    # 搜索表单
    with st.form("advanced_search"):
        col1, col2 = st.columns(2)
        
        with col1:
            query = st.text_input("关键词")
            category = st.selectbox("分类", ["全部", "游戏", "网络用语", "流行语", "方言"])
        
        with col2:
            limit = st.slider("结果数量", 1, 50, 10)
            sort_by = st.selectbox("排序方式", ["热度", "时间", "相关性"])
        
        submitted = st.form_submit_button("🔍 搜索", type="primary")
    
    if submitted and query:
        with st.spinner("正在搜索..."):
            result = MemeCommonsAPI.search_memes(query, limit)
            # 这里可以渲染更复杂的搜索结果
            st.json(result)

def render_data_analysis():
    """渲染数据分析界面"""
    st.header("📈 数据分析")
    
    # 数据统计
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("总梗数量", "1,234")
    with col2:
        st.metric("今日新增", "12")
    with col3:
        st.metric("活跃用户", "567")
    with col4:
        st.metric("查询次数", "8,901")
    
    # 图表区域
    st.markdown("#### 📊 数据可视化")
    
    # 模拟数据图表
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    meme_counts = [10 + 5 * i + (i % 7) * 2 for i in range(len(dates))]
    
    fig = px.line(x=dates, y=meme_counts, 
                  title='梗数量趋势', 
                  labels={'x': '日期', 'y': '梗数量'})
    st.plotly_chart(fig, use_container_width=True)

def render_system_management():
    """渲染系统管理界面 - 已迁移到后台监控"""
    st.header("⚙️ 系统管理")
    st.warning("系统管理功能已迁移到后台监控界面")
    st.info("请访问 http://localhost:8502 进行系统配置和管理")

def main():
    """主函数"""
    init_session_state()
    
    # 渲染头部
    render_header()
    
    # 渲染侧边栏和主要内容
    page = render_sidebar()
    
    # 页面内容
    if page == "🔍 梗知识查询":
        render_knowledge_search()
    elif page == "📊 热门梗":
        render_trending()
    elif page == "🔎 高级搜索":
        render_advanced_search()
    elif page == "📈 数据分析":
        render_data_analysis()

if __name__ == "__main__":
    main()