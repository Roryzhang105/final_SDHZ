#!/bin/bash

# 送达回证自动化处理系统启动脚本

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 命令未找到，请先安装"
        return 1
    fi
    return 0
}

# 检查服务是否运行
check_service() {
    local service_name=$1
    local port=$2
    local host=${3:-localhost}
    
    if nc -z $host $port 2>/dev/null; then
        log_info "$service_name 服务运行正常 ($host:$port)"
        return 0
    else
        log_error "$service_name 服务未运行 ($host:$port)"
        return 1
    fi
}

# 等待服务启动
wait_for_service() {
    local service_name=$1
    local port=$2
    local host=${3:-localhost}
    local max_attempts=${4:-30}
    local attempt=1
    
    log_info "等待 $service_name 服务启动..."
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z $host $port 2>/dev/null; then
            log_info "$service_name 服务已启动"
            return 0
        fi
        
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done
    
    log_error "$service_name 服务启动超时"
    return 1
}

# 检查依赖环境
check_dependencies() {
    log_step "检查依赖环境..."
    
    # 检查Python
    if ! check_command python3; then
        exit 1
    fi
    
    # 检查pip
    if ! check_command pip3; then
        exit 1
    fi
    
    # 检查PostgreSQL
    if ! check_service "PostgreSQL" 5432; then
        log_warn "PostgreSQL未运行，请启动PostgreSQL服务"
        log_info "Ubuntu/Debian: sudo systemctl start postgresql"
        log_info "macOS: brew services start postgresql"
        read -p "PostgreSQL已启动，按Enter继续..."
    fi
    
    # 检查Redis
    if ! check_service "Redis" 6379; then
        log_warn "Redis未运行，请启动Redis服务"
        log_info "Ubuntu/Debian: sudo systemctl start redis"
        log_info "macOS: brew services start redis"
        read -p "Redis已启动，按Enter继续..."
    fi
}

# 安装Python依赖
install_dependencies() {
    log_step "安装Python依赖..."
    
    # 检查虚拟环境
    if [ ! -d "venv" ]; then
        log_info "创建虚拟环境..."
        python3 -m venv venv
    fi
    
    # 激活虚拟环境
    log_info "激活虚拟环境..."
    source venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装依赖
    log_info "安装项目依赖..."
    pip install -r requirements.txt
}

# 初始化数据库
init_database() {
    log_step "初始化数据库..."
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 运行数据库初始化脚本
    python init_db.py
    
    if [ $? -eq 0 ]; then
        log_info "数据库初始化完成"
    else
        log_error "数据库初始化失败"
        exit 1
    fi
}

# 启动应用
start_application() {
    log_step "启动FastAPI应用..."
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 设置PYTHONPATH
    export PYTHONPATH=$PWD:$PYTHONPATH
    
    # 启动应用
    log_info "启动应用服务器..."
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
}

# 主函数
main() {
    log_info "=== 送达回证自动化处理系统启动 ==="
    
    # 切换到脚本目录
    cd "$(dirname "$0")"
    
    # 检查环境变量文件
    if [ ! -f ".env" ]; then
        log_error ".env 文件不存在，请先配置环境变量"
        log_info "可以复制 .env.example 并修改配置"
        exit 1
    fi
    
    # 检查依赖
    check_dependencies
    
    # 安装依赖
    install_dependencies
    
    # 初始化数据库
    init_database
    
    # 启动应用
    start_application
}

# 脚本选项
case "${1:-start}" in
    "start")
        main
        ;;
    "check")
        check_dependencies
        ;;
    "install")
        install_dependencies
        ;;
    "init-db")
        init_database
        ;;
    "dev")
        log_step "启动开发服务器..."
        source venv/bin/activate
        export PYTHONPATH=$PWD:$PYTHONPATH
        uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
        ;;
    *)
        echo "用法: $0 {start|check|install|init-db|dev}"
        echo "  start    - 完整启动流程"
        echo "  check    - 检查依赖环境"
        echo "  install  - 安装Python依赖"
        echo "  init-db  - 初始化数据库"
        echo "  dev      - 启动开发服务器"
        exit 1
        ;;
esac