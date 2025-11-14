#!/bin/bash

# meme-commons 开发模式启动脚本
# 日志显示在控制台，便于调试和监控

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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

log_debug() {
    echo -e "${CYAN}[DEBUG]${NC} $1"
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
        log_info "激活meme环境..."
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
        eval "$(conda shell.bash hook)"
        conda activate meme
        log_success "meme环境激活成功"
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

# 清理后台进程
cleanup_processes() {
    log_info "清理可能存在的后台进程..."
    pkill -f "python.*main.py" || true
    pkill -f "streamlit.*streamlit_app.py" || true
    sleep 1
    log_success "清理完成"
}

# 启动后端服务（控制台模式）
start_backend_console() {
    log_info "🚀 启动后端MCP服务器（控制台模式）..."
    
    # 设置环境变量
    export PYTHONPATH="/home/codeserver/codes:$PYTHONPATH"
    export MEME_DB_PATH="/home/codeserver/codes/meme_commons/database/meme_commons.db"
    
    cd /home/codeserver/codes/meme_commons
    
    echo
    echo "=================================================="
    echo -e "${CYAN}📝 后端服务日志输出（实时）${NC}"
    echo "=================================================="
    echo
    echo -e "${YELLOW}⚠️  注意：此模式下日志直接显示在控制台${NC}"
    echo -e "${YELLOW}按 Ctrl+C 可以随时停止服务${NC}"
    echo
    
    # 启动后端服务（前台运行，显示日志）
    conda run -n meme python main.py
}

# 启动前端服务（后台模式）
start_frontend_background() {
    log_info "启动前端Streamlit应用（后台模式）..."
    
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

# 启动后端服务（后台模式）
start_backend_background() {
    log_info "启动后端MCP服务器（后台模式）..."
    
    # 设置环境变量
    export PYTHONPATH="/home/codeserver/codes:$PYTHONPATH"
    export MEME_DB_PATH="/home/codeserver/codes/meme_commons/database/meme_commons.db"
    
    # 启动后端服务（后台运行）
    cd /home/codeserver/codes/meme_commons
    nohup conda run -n meme python main.py > backend.log 2>&1 &
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
    echo "  • 前端PID: $(cat frontend.pid 2>/dev/null || echo '未知')"
    echo "  • 启动时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo
    echo "🔧 管理命令："
    echo "  • 查看前端日志: tail -f frontend.log"
    echo "  • 检查状态: curl http://localhost:8002/health"
    echo "  • 停止前端: kill \$(cat frontend.pid)"
    echo
    echo "📝 功能说明："
    echo "  • 后端服务在控制台显示实时日志"
    echo "  • 前端服务运行在后台"
    echo "  • 梗知识查询和智能分析"
    echo "  • 热门梗趋势分析"
    echo "  • 数据可视化和统计分析"
    echo
    echo "=================================================="
    echo
}

# 清理函数
cleanup() {
    log_info "正在停止所有服务..."
    
    if [ -f frontend.pid ]; then
        FRONTEND_PID=$(cat frontend.pid)
        if ps -p $FRONTEND_PID > /dev/null 2>&1; then
            kill $FRONTEND_PID
            log_success "前端服务已停止"
        fi
        rm -f frontend.pid
    fi
    
    cleanup_processes
    log_success "所有服务已停止"
    exit 0
}

# 显示帮助信息
show_help() {
    echo "meme-commons 开发模式启动脚本"
    echo
    echo "用法:"
    echo "  $0 [模式]"
    echo
    echo "模式:"
    echo "  backend     仅启动后端服务（日志显示在控制台）"
    echo "  frontend    仅启动前端服务（后台模式）"
    echo "  both        启动前后端服务（后端控制台，前端后台）"
    echo "  --help      显示此帮助信息"
    echo
    echo "示例:"
    echo "  $0 backend    # 仅调试后端服务"
    echo "  $0 frontend   # 仅测试前端服务"
    echo "  $0 both       # 完整启动"
    echo
}

# 主函数
main() {
    # 解析命令行参数
    MODE=${1:-"both"}
    
    case $MODE in
        --help|-h)
            show_help
            exit 0
            ;;
        backend)
            log_info "🚀 启动模式：仅后端服务"
            check_conda
            setup_conda_env
            cleanup_processes
            start_backend_console
            ;;
        frontend)
            log_info "🚀 启动模式：仅前端服务"
            check_conda
            setup_conda_env
            check_ports
            start_frontend_background
            show_startup_info
            ;;
        both)
            log_info "🚀 启动模式：前后端完整服务"
            check_conda
            setup_conda_env
            check_ports
            cleanup_processes
            
            # 设置信号处理
            trap cleanup SIGINT SIGTERM
            
            # 启动前端（后台）
            start_frontend_background
            
            # 启动后端（前台）
            start_backend_console
            ;;
        *)
            log_error "未知模式: $MODE"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"