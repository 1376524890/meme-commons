#!/bin/bash

# meme-commons 一键启动脚本
# 使用conda虚拟环境meme，检查环境存在性并自动启动服务

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查conda是否安装
check_conda() {
    if ! command -v conda &> /dev/null; then
        echo "❌ 错误: conda未安装"
        echo "请先安装miniconda或anaconda"
        exit 1
    fi
    echo "✅ conda已安装"
}

# 检查并创建conda环境
setup_conda_env() {
    log_info "检查conda环境 'meme'..."
    
    if conda env list | grep -q "meme"; then
        log_success "conda环境 'meme' 已存在"
        log_info "使用现有环境"
        # 激活meme环境
        eval "$(conda shell.bash hook)"
        conda activate meme
        if [ $? -eq 0 ]; then
            log_success "meme环境激活成功"
        else
            log_warning "meme环境激活失败，尝试重新激活..."
            conda activate meme
        fi
    else
        log_info "创建conda环境 'meme'..."
        conda create -n meme python=3.11 -y
        log_success "conda环境 'meme' 创建成功"
        # 激活meme环境
        eval "$(conda shell.bash hook)"
        conda activate meme
        log_success "meme环境激活成功"
    fi
}

# 安装依赖包
install_dependencies() {
    log_info "检查和安装依赖包..."
    
    # 检查核心依赖是否已安装
    python -c "import streamlit, plotly, requests, pandas" 2>/dev/null
    
    if [ $? -ne 0 ]; then
        log_info "安装前端依赖包..."
        pip install streamlit plotly requests pandas
        
        log_info "安装后端依赖包..."
        pip install fastapi uvicorn sqlalchemy psycopg2-binary
        pip install openai anthropic langchain-core langchain-openai
        pip install numpy scikit-learn faiss-cpu
        pip install beautifulsoup4 selenium playwright
        pip install jupyter ipython
        
        log_success "依赖包安装完成"
    else
        log_success "依赖包已存在，跳过安装"
    fi
}

# 检查端口占用
check_ports() {
    log_info "检查端口占用情况..."
    
    # 检查8002端口（后端API）
    if lsof -i :8002 &>/dev/null; then
        log_warning "端口8002已被占用，尝试清理..."
        fuser -k 8002/tcp 2>/dev/null || true
        sleep 2
    fi
    
    # 检查8501端口（前端界面）
    if lsof -i :8501 &>/dev/null; then
        log_warning "端口8501已被占用，尝试清理..."
        fuser -k 8501/tcp 2>/dev/null || true
        sleep 2
    fi
    
    log_success "端口检查完成"
}

# 启动后端服务
start_backend() {
    log_info "启动后端MCP服务器..."
    
    # 设置环境变量
    export PYTHONPATH="/home/codeserver/codes:$PYTHONPATH"
    export MEME_DB_PATH="/home/codeserver/codes/meme_commons/database/meme_commons.db"
    
    # 启动后端服务（后台运行）
    cd /home/codeserver/codes
    nohup conda run -n meme python -m meme_commons.main > backend.log 2>&1 &
    BACKEND_PID=$!
    
    echo $BACKEND_PID > backend.pid
    log_success "后端服务已启动 (PID: $BACKEND_PID)"
    
    # 等待服务启动
    log_info "等待后端服务启动..."
    for i in {1..30}; do
        if curl -s http://localhost:8002/health > /dev/null 2>&1; then
            log_success "后端服务启动完成"
            break
        fi
        sleep 1
        if [ $i -eq 30 ]; then
            log_error "后端服务启动超时"
            exit 1
        fi
    done
}

# 启动前端服务
start_frontend() {
    log_info "启动前端Streamlit应用..."
    
    # 启动前端服务（后台运行）
    cd /home/codeserver/codes/meme_commons
    nohup conda run -n meme streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0 > frontend.log 2>&1 &
    FRONTEND_PID=$!
    
    echo $FRONTEND_PID > frontend.pid
    log_success "前端服务已启动 (PID: $FRONTEND_PID)"
    
    # 等待服务启动
    log_info "等待前端服务启动..."
    for i in {1..30}; do
        if curl -s http://localhost:8501 > /dev/null 2>&1; then
            log_success "前端服务启动完成"
            break
        fi
        sleep 1
        if [ $i -eq 30 ]; then
            log_warning "前端服务启动超时，可能仍在启动中"
            break
        fi
    done
}

# 显示启动信息
show_startup_info() {
    echo
    echo "=================================================="
    log_success "🎉 meme-commons 梗知识智能系统启动完成！"
    echo "=================================================="
    echo
    echo "🌐 访问地址："
    echo "  • 前端界面: http://localhost:8501"
    echo "  • 后端API:  http://localhost:8002"
    echo "  • API文档:  http://localhost:8002/docs"
    echo
    echo "📊 系统状态："
    echo "  • 后端PID: $(cat backend.pid 2>/dev/null || echo '未知')"
    echo "  • 前端PID: $(cat frontend.pid 2>/dev/null || echo '未知')"
    echo "  • 启动时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo
    echo "🔧 管理命令："
    echo "  • 停止所有服务: ./stop_meme_commons.sh"
    echo "  • 查看日志: tail -f backend.log frontend.log"
    echo "  • 检查状态: curl http://localhost:8002/health"
    echo
    echo "📝 功能说明："
    echo "  • 梗知识查询和智能分析"
    echo "  • 热门梗趋势分析"
    echo "  • 数据可视化和统计分析"
    echo "  • 系统状态监控"
    echo
    echo "=================================================="
    echo
    log_info "按 Ctrl+C 停止所有服务"
}

# 清理函数
cleanup() {
    log_info "正在停止所有服务..."
    
    if [ -f backend.pid ]; then
        BACKEND_PID=$(cat backend.pid)
        if ps -p $BACKEND_PID > /dev/null 2>&1; then
            kill $BACKEND_PID
            log_success "后端服务已停止"
        fi
        rm -f backend.pid
    fi
    
    if [ -f frontend.pid ]; then
        FRONTEND_PID=$(cat frontend.pid)
        if ps -p $FRONTEND_PID > /dev/null 2>&1; then
            kill $FRONTEND_PID
            log_success "前端服务已停止"
        fi
        rm -f frontend.pid
    fi
    
    log_success "所有服务已停止"
    exit 0
}

# 主函数
main() {
    # 设置信号处理
    trap cleanup SIGINT SIGTERM
    
    echo
    log_info "🚀 开始启动 meme-commons 梗知识智能系统"
    echo
    
    # 执行启动步骤
    check_conda
    setup_conda_env
    install_dependencies
    check_ports
    start_backend
    start_frontend
    show_startup_info
    
    # 监控服务状态（改进版）
    log_info "开始监控服务状态..."
    while true; do
        sleep 3
        # 检查后端服务
        if [ -f /home/codeserver/codes/backend.pid ]; then
            BACKEND_PID=$(cat /home/codeserver/codes/backend.pid)
            if ! ps -p $BACKEND_PID > /dev/null 2>&1; then
                log_warning "后端服务已停止，尝试重启..."
                start_backend
            fi
        fi
        
        # 检查前端服务
        if [ -f /home/codeserver/codes/meme_commons/frontend.pid ]; then
            FRONTEND_PID=$(cat /home/codeserver/codes/meme_commons/frontend.pid)
            if ! ps -p $FRONTEND_PID > /dev/null 2>&1; then
                log_warning "前端服务已停止，尝试重启..."
                start_frontend
            fi
        fi
        
        # 检查API连接
        if ! curl -s http://localhost:8002/health > /dev/null 2>&1; then
            log_warning "后端API不可达，可能需要重启后端服务"
        fi
    done
}

# 执行主函数
main "$@"