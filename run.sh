#!/bin/bash

# meme-commons 一键启动脚本
# 用于启动全部服务：前端、后台监控和后端服务

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# 生成带时间戳的日志目录
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_DIR="logs/logs_$TIMESTAMP"
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"
MONITOR_LOG="$LOG_DIR/monitor.log"

# 进程ID文件
PID_DIR=".pid"
BACKEND_PID="$PID_DIR/backend.pid"
FRONTEND_PID="$PID_DIR/frontend.pid"
MONITOR_PID="$PID_DIR/monitor.pid"

# 虚拟环境配置
VENV_NAME="venv_meme_commons"
VENV_PATH="./$VENV_NAME"
PYTHON_PATH="$VENV_PATH/bin/python"
STREAMLIT_PATH="$VENV_PATH/bin/streamlit"

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

log_monitor() {
    echo -e "${PURPLE}[MONITOR]${NC} $1"
}

# 创建必要的目录
create_directories() {
    log_info "创建必要目录..."
    mkdir -p "$LOG_DIR"
    log_info "日志目录已创建: $LOG_DIR"
    mkdir -p "$PID_DIR"
    log_success "目录创建完成"
}

# 检查环境
check_environment() {
    log_info "检查运行环境..."
    
    # 检查Python 3.11
    if ! command -v python3.11 &> /dev/null; then
        log_error "Python 3.11未安装"
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
    
    # 检查前端文件
    if [ ! -f "streamlit_app.py" ]; then
        log_error "streamlit_app.py文件不存在"
        exit 1
    fi
    
    # 检查监控文件
    if [ ! -f "monitor_app.py" ]; then
        log_error "monitor_app.py文件不存在"
        exit 1
    fi
    
    log_success "环境检查完成"
}

# 创建虚拟环境
create_venv() {
    if [ ! -d "$VENV_PATH" ]; then
        log_info "创建Python 3.11虚拟环境: $VENV_NAME..."
        python3.11 -m venv "$VENV_PATH"
        log_success "虚拟环境创建完成"
    else
        log_info "虚拟环境已存在: $VENV_NAME"
    fi
}

# 激活虚拟环境
activate_venv() {
    if [ -d "$VENV_PATH" ]; then
        log_info "激活虚拟环境..."
        # 检测操作系统类型
        if [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # macOS 或 Linux
            source "$VENV_PATH/bin/activate"
        elif [[ "$OSTYPE" == "msys"* ]] || [[ "$OSTYPE" == "win32"* ]]; then
            # Windows
            "$VENV_PATH/Scripts/activate"
        fi
        log_success "虚拟环境已激活"
        return 0
    else
        log_error "虚拟环境不存在，请先创建虚拟环境"
        return 1
    fi
}

# 安装依赖
install_deps() {
    log_info "安装依赖..."
    
    # 使用虚拟环境中的pip
    log_info "使用虚拟环境中的pip安装依赖..."
    
    # 检查虚拟环境是否存在
    if [ ! -d "$VENV_PATH" ]; then
        log_error "虚拟环境不存在，请先创建虚拟环境"
        return 1
    fi
    
    # 升级虚拟环境中的pip
    log_info "升级虚拟环境中的pip..."
    "$VENV_PATH/bin/pip" install --upgrade pip --no-cache-dir
    
    # 安装基础构建工具
    log_info "安装基础构建工具..."
    "$VENV_PATH/bin/pip" install --upgrade setuptools wheel --no-cache-dir
    
    # 安装项目依赖
    log_info "安装项目依赖..."
    "$VENV_PATH/bin/pip" install -r requirements.txt --no-cache-dir
    
    if [ $? -eq 0 ]; then
        log_success "依赖安装完成"
    else
        log_error "依赖安装失败"
        return 1
    fi
}

# 停止服务
stop_service() {
    service_name=$1
    pid_file=$2
    
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        log_info "停止 $service_name 服务 (PID: $pid)"
        
        # 尝试优雅终止
        if kill -15 "$pid" 2>/dev/null; then
            # 等待进程终止，最多10秒
            i=1
            while [ $i -le 10 ]; do
                if ! kill -0 "$pid" 2>/dev/null; then
                    log_success "$service_name 服务已成功停止"
                    rm -f "$pid_file"
                    return 0
                fi
                sleep 1
                i=$((i+1))
            done
            
            # 如果优雅终止失败，强制终止
            log_warning "$service_name 服务无法优雅终止，尝试强制终止"
            kill -9 "$pid" 2>/dev/null
            rm -f "$pid_file"
            log_success "$service_name 服务已强制停止"
        else
            log_warning "$service_name 服务进程不存在或无法终止，清理PID文件"
            rm -f "$pid_file"
        fi
    else
        log_warning "$service_name 服务PID文件不存在，可能未运行"
    fi
}

# 停止所有服务
stop_all_services() {
    log_info "停止所有服务..."
    stop_service "前端界面" "$FRONTEND_PID"
    stop_service "后台监控" "$MONITOR_PID"
    stop_service "后端服务" "$BACKEND_PID"
    log_success "所有服务已停止"
}

# 启动后端服务
start_backend() {
    log_info "启动后端服务..."
    
    # 使用虚拟环境中的Python路径
    if [ ! -f "$PYTHON_PATH" ]; then
        log_error "无法找到虚拟环境中的Python: $PYTHON_PATH"
        return 1
    fi
    
    # 确保日志目录存在
    mkdir -p "$(dirname "$BACKEND_LOG")"
    
    # 清除旧的日志文件
    rm -f "$BACKEND_LOG"
    
    # 在后台运行后端服务
    nohup "$PYTHON_PATH" main.py > "$BACKEND_LOG" 2>&1 &
    BACKEND_PID_VALUE=$!
    echo "$BACKEND_PID_VALUE" > "$BACKEND_PID"
    
    log_success "后端服务已启动 (PID: $BACKEND_PID_VALUE)"
    log_info "后端API: http://localhost:8002"
    log_info "健康检查: http://localhost:8002/health"
    log_info "日志文件: $BACKEND_LOG"
    
    # 等待服务启动并检查状态
    log_info "等待后端服务初始化..."
    sleep 5
    
    # 检查进程是否仍在运行
    if ps -p "$BACKEND_PID_VALUE" > /dev/null; then
        log_success "后端服务进程正在运行"
    else
        log_error "后端服务进程已退出，检查日志获取更多信息"
        tail -n 20 "$BACKEND_LOG" | log_error
        return 1
    fi
    
    # 尝试检查服务是否响应
    if command -v curl &> /dev/null; then
        log_info "尝试连接后端服务..."
        if curl -s -o /dev/null -w "%{http_code}" "http://localhost:8002/health" | grep -q "200"; then
            log_success "后端服务已成功启动并响应请求"
        else
            log_warning "无法连接到后端服务，可能仍在初始化中"
        fi
    fi
}

# 启动前端服务
start_frontend() {
    log_info "启动前端界面..."
    
    # 使用虚拟环境中的Streamlit路径
    if [ ! -f "$STREAMLIT_PATH" ]; then
        log_error "无法找到虚拟环境中的Streamlit: $STREAMLIT_PATH"
        return 1
    fi
    
    # 确保日志目录存在
    mkdir -p "$(dirname "$FRONTEND_LOG")"
    
    # 清除旧的日志文件
    rm -f "$FRONTEND_LOG"
    
    # 在后台运行前端服务，明确指定使用8501端口
    nohup "$STREAMLIT_PATH" run streamlit_app.py --server.port=8501 > "$FRONTEND_LOG" 2>&1 &
    FRONTEND_PID_VALUE=$!
    echo "$FRONTEND_PID_VALUE" > "$FRONTEND_PID"
    
    log_success "前端界面已启动 (PID: $FRONTEND_PID_VALUE)"
    log_info "前端界面: http://localhost:8501"
    log_info "日志文件: $FRONTEND_LOG"
    
    # 等待服务启动并检查状态
    log_info "等待前端服务初始化..."
    sleep 3
    
    # 检查进程是否仍在运行
    if ps -p "$FRONTEND_PID_VALUE" > /dev/null; then
        log_success "前端服务进程正在运行"
    else
        log_error "前端服务进程已退出，检查日志获取更多信息"
        tail -n 20 "$FRONTEND_LOG" | log_error
        return 1
    fi
}

# 启动后台监控服务
start_monitor() {
    log_info "启动后台监控界面..."
    
    # 使用虚拟环境中的Streamlit路径
    if [ ! -f "$STREAMLIT_PATH" ]; then
        log_error "无法找到虚拟环境中的Streamlit: $STREAMLIT_PATH"
        return 1
    fi
    
    # 确保日志目录存在
    mkdir -p "$(dirname "$MONITOR_LOG")"
    
    # 清除旧的日志文件
    rm -f "$MONITOR_LOG"
    
    # 在后台运行监控服务，使用端口8502
    nohup "$STREAMLIT_PATH" run monitor_app.py --server.port=8502 > "$MONITOR_LOG" 2>&1 &
    MONITOR_PID_VALUE=$!
    echo "$MONITOR_PID_VALUE" > "$MONITOR_PID"
    
    log_success "后台监控界面已启动 (PID: $MONITOR_PID_VALUE)"
    log_info "后台监控: http://localhost:8502"
    log_info "日志文件: $MONITOR_LOG"
    
    # 等待服务启动并检查状态
    log_info "等待监控服务初始化..."
    sleep 3
    
    # 检查进程是否仍在运行
    if ps -p "$MONITOR_PID_VALUE" > /dev/null; then
        log_success "监控服务进程正在运行"
    else
        log_error "监控服务进程已退出，检查日志获取更多信息"
        tail -n 20 "$MONITOR_LOG" | log_error
        return 1
    fi
}

# 启动全部服务
start_all_services() {
    log_info "启动全部服务..."
    
    # 先停止所有服务（如果正在运行）
    stop_all_services
    
    # 按顺序启动服务并检查每个服务的启动状态
    log_info "======================= 启动后端服务 ======================="
    if ! start_backend; then
        log_error "后端服务启动失败，中止启动流程"
        return 1
    fi
    
    log_info "\n======================= 启动前端服务 ======================="
    if ! start_frontend; then
        log_error "前端服务启动失败，但会继续尝试启动其他服务"
    fi
    
    log_info "\n======================= 启动监控服务 ======================="
    if ! start_monitor; then
        log_error "监控服务启动失败，但其他服务可能已经运行"
    fi
    
    log_success "\n所有服务启动尝试完成！"
    display_service_info
    
    # 建议用户检查状态
    log_info "建议运行 '$0 --status' 检查所有服务的实际运行状态"
    log_info "如有服务未正常运行，请检查相应的日志文件获取详细错误信息"
}

# 显示服务信息
display_service_info() {
    echo -e "\n${PURPLE}======================================${NC}"
    echo -e "${PURPLE}        meme-commons 服务信息        ${NC}"
    echo -e "${PURPLE}======================================${NC}"
    echo -e "${GREEN}📱 前端界面:${NC} http://localhost:8501"
    echo -e "${BLUE}🔧 后台监控:${NC} http://localhost:8502"
    echo -e "${YELLOW}⚙️ 后端API:${NC} http://localhost:8002"
    echo -e "${GREEN}🩺 健康检查:${NC} http://localhost:8002/health"
    echo -e "${PURPLE}======================================${NC}\n"
}

# 显示日志
show_logs() {
    service_name=$1
    log_file=$2
    
    log_info "显示 $service_name 日志..."
    echo -e "${PURPLE}======================================${NC}"
    echo -e "${PURPLE}      $service_name 最近日志      ${NC}"
    echo -e "${PURPLE}======================================${NC}"
    
    if [ -f "$log_file" ]; then
        tail -n 30 "$log_file"
    else
        log_error "日志文件不存在: $log_file"
    fi
    
    echo -e "${PURPLE}======================================${NC}\n"
}

# 显示所有日志
show_all_logs() {
    show_logs "后端服务" "$BACKEND_LOG"
    show_logs "前端界面" "$FRONTEND_LOG"
    show_logs "后台监控" "$MONITOR_LOG"
}

# 显示服务状态
show_status() {
    log_info "检查服务状态..."
    echo -e "${PURPLE}======================================${NC}"
    echo -e "${PURPLE}        meme-commons 服务状态        ${NC}"
    echo -e "${PURPLE}======================================${NC}"
    
    # 检查后端服务
    if [ -f "$BACKEND_PID" ]; then
        pid=$(cat "$BACKEND_PID")
        if ps -p "$pid" > /dev/null; then
            echo -e "${GREEN}🟢 后端服务:${NC} 运行中 (PID: $pid)"
        else
            echo -e "${RED}🔴 后端服务:${NC} 已停止 (PID文件存在)"
            rm -f "$BACKEND_PID"
        fi
    else
        echo -e "${RED}🔴 后端服务:${NC} 未运行"
    fi
    
    # 检查前端服务
    if [ -f "$FRONTEND_PID" ]; then
        pid=$(cat "$FRONTEND_PID")
        if ps -p "$pid" > /dev/null; then
            echo -e "${GREEN}🟢 前端界面:${NC} 运行中 (PID: $pid)"
        else
            echo -e "${RED}🔴 前端界面:${NC} 已停止 (PID文件存在)"
            rm -f "$FRONTEND_PID"
        fi
    else
        echo -e "${RED}🔴 前端界面:${NC} 未运行"
    fi
    
    # 检查监控服务
    if [ -f "$MONITOR_PID" ]; then
        pid=$(cat "$MONITOR_PID")
        if ps -p "$pid" > /dev/null; then
            echo -e "${GREEN}🟢 后台监控:${NC} 运行中 (PID: $pid)"
        else
            echo -e "${RED}🔴 后台监控:${NC} 已停止 (PID文件存在)"
            rm -f "$MONITOR_PID"
        fi
    else
        echo -e "${RED}🔴 后台监控:${NC} 未运行"
    fi
    
    echo -e "${PURPLE}======================================${NC}\n"
}

# 主函数
main() {
    echo -e "${PURPLE}🎭 meme-commons 梗文化智能系统一键启动器${NC}"
    echo -e "${PURPLE}========================================${NC}\n"
    
    # 创建必要的目录
    create_directories
    
    # 检查环境
    check_environment
    
    # 处理命令行参数
    if [[ "$1" == "-h" || "$1" == "--help" ]]; then
        show_help
        exit 0
    elif [[ "$1" == "--deps-only" ]]; then
        # 仅安装依赖
        create_venv
        install_deps
        exit 0
    elif [[ "$1" == "--stop" ]]; then
        # 停止所有服务
        stop_all_services
        exit 0
    elif [[ "$1" == "--status" ]]; then
        # 显示服务状态
        show_status
        exit 0
    elif [[ "$1" == "--logs" ]]; then
        # 显示日志
        if [[ "$2" == "backend" ]]; then
            show_logs "后端服务" "$BACKEND_LOG"
        elif [[ "$2" == "frontend" ]]; then
            show_logs "前端界面" "$FRONTEND_LOG"
        elif [[ "$2" == "monitor" ]]; then
            show_logs "后台监控" "$MONITOR_LOG"
        else
            show_all_logs
        fi
        exit 0
    fi
    
    # 自动使用虚拟环境
    log_info "自动使用虚拟环境..."
    create_venv
    
    # 自动安装/更新依赖
    log_info "自动安装/更新依赖..."
    if ! install_deps; then
        log_error "依赖安装失败，退出"
        exit 1
    fi
    
    # 启动所有服务
    start_all_services
    
    # 最后显示服务状态
    show_status
    
    log_info "使用以下命令管理服务:"
    log_info "  $0 --stop    - 停止所有服务"
    log_info "  $0 --status  - 查看服务状态"
    log_info "  $0 --logs    - 查看所有日志"
    log_info "  $0 --logs backend/frontend/monitor - 查看特定服务日志"
    echo
}

# 显示帮助信息
show_help() {
    echo -e "${PURPLE}meme-commons 一键启动脚本${NC}"
    echo -e "${PURPLE}========================${NC}\n"
    echo "用法: $0 [选项]"
    echo
    echo "选项:"
    echo "  -h, --help          显示帮助信息"
    echo "  --deps-only         仅创建虚拟环境并安装依赖，不启动服务"
    echo "  --stop              停止所有服务"
    echo "  --status            查看服务运行状态"
    echo "  --logs [service]    查看服务日志 (service: backend/frontend/monitor)"
    echo
    echo "示例:"
    echo "  $0                  一键启动所有服务"
    echo "  $0 --deps-only      仅安装依赖"
    echo "  $0 --stop           停止所有服务"
    echo "  $0 --logs backend   查看后端服务日志"
    echo
}

# 处理SIGINT和SIGTERM信号
trap stop_all_services SIGINT SIGTERM

# 运行主程序
main "$@"