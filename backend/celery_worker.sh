#!/bin/bash

# Celery Worker 启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查Redis连接
check_redis() {
    log_step "检查Redis连接..."
    
    if ! command -v redis-cli &> /dev/null; then
        log_error "redis-cli 未找到，请安装Redis"
        return 1
    fi
    
    if redis-cli ping | grep -q "PONG"; then
        log_info "Redis连接正常"
        return 0
    else
        log_error "Redis连接失败"
        return 1
    fi
}

# 启动Celery Worker
start_worker() {
    log_step "启动Celery Worker..."
    
    # 切换到项目目录
    cd "$(dirname "$0")"
    
    # 检查环境变量文件
    if [ ! -f ".env" ]; then
        log_error ".env 文件不存在"
        exit 1
    fi
    
    # 激活虚拟环境
    if [ -d "venv" ]; then
        source venv/bin/activate
        log_info "虚拟环境已激活"
    else
        log_error "虚拟环境不存在，请先运行 ./start.sh install"
        exit 1
    fi
    
    # 设置PYTHONPATH
    export PYTHONPATH=$PWD:$PYTHONPATH
    
    # 检查Redis
    if ! check_redis; then
        exit 1
    fi
    
    # 启动Worker
    log_info "启动Celery Worker进程..."
    celery -A app.tasks.celery_app worker --loglevel=info --concurrency=4 --events
}

# 启动Celery Beat (定时任务调度器)
start_beat() {
    log_step "启动Celery Beat..."
    
    cd "$(dirname "$0")"
    
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        log_error "虚拟环境不存在"
        exit 1
    fi
    
    export PYTHONPATH=$PWD:$PYTHONPATH
    
    if ! check_redis; then
        exit 1
    fi
    
    log_info "启动Celery Beat调度器..."
    celery -A app.tasks.celery_app beat --loglevel=info
}

# 启动Flower (监控界面)
start_flower() {
    log_step "启动Celery Flower监控..."
    
    cd "$(dirname "$0")"
    
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        log_error "虚拟环境不存在"
        exit 1
    fi
    
    # 检查是否安装了flower
    if ! pip show flower &> /dev/null; then
        log_info "安装Flower..."
        pip install flower
    fi
    
    export PYTHONPATH=$PWD:$PYTHONPATH
    
    if ! check_redis; then
        exit 1
    fi
    
    log_info "启动Flower监控界面 (http://localhost:5555)..."
    celery -A app.tasks.celery_app flower --port=5555
}

# 查看队列状态
show_status() {
    log_step "查看Celery状态..."
    
    cd "$(dirname "$0")"
    
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        log_error "虚拟环境不存在"
        exit 1
    fi
    
    export PYTHONPATH=$PWD:$PYTHONPATH
    
    echo "=== Active Workers ==="
    celery -A app.tasks.celery_app inspect active
    
    echo "=== Queue Stats ==="
    celery -A app.tasks.celery_app inspect stats
    
    echo "=== Registered Tasks ==="
    celery -A app.tasks.celery_app inspect registered
}

# 清空队列
purge_queues() {
    log_step "清空所有队列..."
    
    cd "$(dirname "$0")"
    
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        log_error "虚拟环境不存在"
        exit 1
    fi
    
    export PYTHONPATH=$PWD:$PYTHONPATH
    
    read -p "确定要清空所有队列吗？这将删除所有待处理的任务 (y/N): " confirm
    if [[ $confirm == [yY] ]]; then
        celery -A app.tasks.celery_app purge -f
        log_info "队列已清空"
    else
        log_info "操作已取消"
    fi
}

# 主函数
main() {
    case "${1:-worker}" in
        "worker")
            start_worker
            ;;
        "beat")
            start_beat
            ;;
        "flower")
            start_flower
            ;;
        "status")
            show_status
            ;;
        "purge")
            purge_queues
            ;;
        "dev")
            log_info "启动开发模式 (Worker + Beat)"
            # 在后台启动beat
            start_beat &
            BEAT_PID=$!
            
            # 启动worker (前台)
            trap "kill $BEAT_PID 2>/dev/null" EXIT
            start_worker
            ;;
        *)
            echo "用法: $0 {worker|beat|flower|status|purge|dev}"
            echo "  worker  - 启动Celery Worker"
            echo "  beat    - 启动Celery Beat调度器"
            echo "  flower  - 启动Flower监控界面"
            echo "  status  - 查看Celery状态"
            echo "  purge   - 清空所有队列"
            echo "  dev     - 开发模式(Worker+Beat)"
            exit 1
            ;;
    esac
}

main "$@"