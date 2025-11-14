#!/bin/bash

# meme-commons 简化启动脚本
# 用于快速启动梗文化智能系统

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 检查环境
check_environment() {
    log_info "检查运行环境..."
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3未安装"
        exit 1
    fi
    
    # 检查依赖文件
    if [ ! -f "requirements.txt" ]; then
        log_error "requirements.txt文件不存在"
        exit 1
    fi
    
    # 检查主程序
    if [ ! -f "main.py" ]; then
        log_error "main.py文件不存在"
        exit 1
    fi
    
    log_success "环境检查完成"
}

# 安装依赖
install_deps() {
    log_info "检查和安装依赖..."
    
    if [ -n "$CONDA_DEFAULT_ENV" ] && [ "$CONDA_DEFAULT_ENV" = "meme" ]; then
        log_info "检测到conda环境: $CONDA_DEFAULT_ENV"
        conda run -n meme pip install -r requirements.txt
    else
        log_info "使用系统Python环境安装依赖"
        pip install -r requirements.txt
    fi
    
    if [ $? -eq 0 ]; then
        log_success "依赖安装完成"
    else
        log_error "依赖安装失败"
        exit 1
    fi
}

# 启动服务
start_service() {
    log_info "启动meme-commons系统..."
    
    if [ -n "$CONDA_DEFAULT_ENV" ] && [ "$CONDA_DEFAULT_ENV" = "meme" ]; then
        log_info "在conda环境中启动服务"
        conda run -n meme python main.py
    else
        log_info "在系统Python环境中启动服务"
        python main.py
    fi
}

# 主函数
main() {
    echo "🎭 meme-commons 梗文化智能系统启动器"
    echo "========================================"
    
    check_environment
    
    read -p "是否安装/更新依赖? (y/N): " install_deps_choice
    if [[ $install_deps_choice =~ ^[Yy]$ ]]; then
        install_deps
    fi
    
    echo
    log_info "准备启动系统..."
    log_info "前端界面: http://localhost:8501"
    log_info "后端API: http://localhost:8002"
    log_info "健康检查: http://localhost:8002/health"
    echo
    
    start_service
}

# 帮助信息
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "meme-commons 启动脚本"
    echo
    echo "用法: $0 [选项]"
    echo
    echo "选项:"
    echo "  -h, --help    显示帮助信息"
    echo "  --deps-only   仅安装依赖，不启动服务"
    echo
    echo "环境变量:"
    echo "  CONDA_DEFAULT_ENV    如果设置为meme，将在conda环境中运行"
    echo
    exit 0
fi

# 仅安装依赖模式
if [[ "$1" == "--deps-only" ]]; then
    check_environment
    install_deps
    exit 0
fi

# 运行主程序
main