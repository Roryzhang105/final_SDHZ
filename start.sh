#!/bin/bash

# SDHZ 快递管理系统一键启动脚本
# 使用方法: ./start.sh [--docker|--dev]

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
PID_DIR="$PROJECT_ROOT/.pids"

# 创建必要目录
mkdir -p "$LOG_DIR" "$PID_DIR"

# 颜色输出
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

# 检查端口是否被占用
check_port() {
    local port=$1
    if lsof -i :$port >/dev/null 2>&1; then
        log_warn "端口 $port 已被占用"
        return 1
    fi
    return 0
}

# 停止已运行的服务
stop_existing_services() {
    log_step "停止已运行的服务..."
    
    # 停止进程
    for pid_file in "$PID_DIR"/*.pid; do
        if [ -f "$pid_file" ]; then
            local pid=$(cat "$pid_file")
            local service_name=$(basename "$pid_file" .pid)
            if kill -0 "$pid" 2>/dev/null; then
                log_info "停止 $service_name (PID: $pid)"
                kill -TERM "$pid" 2>/dev/null || true
                sleep 2
                # 强制杀死未响应的进程
                if kill -0 "$pid" 2>/dev/null; then
                    kill -KILL "$pid" 2>/dev/null || true
                fi
            fi
            rm -f "$pid_file"
        fi
    done
    
    # 清理端口
    for port in 8000 3000 80; do
        local pids=$(lsof -ti :$port 2>/dev/null || true)
        if [ -n "$pids" ]; then
            log_info "清理端口 $port 上的进程"
            echo "$pids" | xargs -r kill -TERM 2>/dev/null || true
        fi
    done
    
    sleep 1
}

# Docker 模式启动
start_docker() {
    log_step "使用 Docker Compose 启动服务..."
    
    cd "$PROJECT_ROOT"
    
    # 检查 docker-compose.yml 是否存在
    if [ ! -f "docker-compose.yml" ]; then
        log_error "docker-compose.yml 文件不存在"
        exit 1
    fi
    
    # 构建并启动服务
    log_info "构建 Docker 镜像..."
    docker compose build --no-cache
    
    log_info "启动所有服务..."
    docker compose up -d
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 10
    
    # 检查服务状态
    log_step "检查服务状态..."
    docker compose ps
    
    # 检查健康状态
    log_info "检查服务健康状态..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            log_info "后端服务启动成功"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "后端服务启动失败"
            docker compose logs backend
            exit 1
        fi
        sleep 2
    done
    
    for i in {1..30}; do
        if curl -s http://localhost > /dev/null 2>&1; then
            log_info "前端服务启动成功"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "前端服务启动失败"
            docker compose logs frontend
            exit 1
        fi
        sleep 2
    done
    
    log_step "所有服务启动成功！"
    echo "前端地址: http://localhost"
    echo "后端API: http://localhost:8000"
    echo "API文档: http://localhost:8000/docs"
    echo "Flower监控: http://localhost:5555 (admin:admin123)"
    echo ""
    echo "查看日志: docker compose logs -f"
    echo "停止服务: docker compose down"
}

# 开发模式启动
start_dev() {
    log_step "使用开发模式启动服务..."
    
    # 检查依赖
    check_dependencies
    
    cd "$PROJECT_ROOT"
    
    # 启动后端
    log_step "启动后端服务..."
    cd backend
    
    # 检查虚拟环境
    if [ ! -d "venv" ]; then
        log_info "创建虚拟环境..."
        python3 -m venv venv
    fi
    
    # 激活虚拟环境并安装依赖
    source venv/bin/activate
    
    if [ ! -f "venv/.deps_installed" ]; then
        log_info "安装Python依赖..."
        pip install --upgrade pip
        pip install -r requirements.txt
        touch venv/.deps_installed
    fi
    
    # 检查数据库
    log_info "初始化数据库..."
    python init_db.py || log_warn "数据库初始化失败，请检查数据库连接"
    
    # 启动后端服务
    log_info "启动后端API服务..."
    nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 \
        > "$LOG_DIR/backend.log" 2>&1 &
    echo $! > "$PID_DIR/backend.pid"
    
    # 启动 Celery Worker
    log_info "启动 Celery Worker..."
    nohup celery -A app.tasks.celery_app worker --loglevel=info \
        > "$LOG_DIR/celery-worker.log" 2>&1 &
    echo $! > "$PID_DIR/celery-worker.pid"
    
    # 启动 Celery Beat
    log_info "启动 Celery Beat..."
    nohup celery -A app.tasks.celery_app beat --loglevel=info \
        > "$LOG_DIR/celery-beat.log" 2>&1 &
    echo $! > "$PID_DIR/celery-beat.pid"
    
    cd "$PROJECT_ROOT"
    
    # 启动前端
    log_step "启动前端服务..."
    cd frontend
    
    # 检查 Node.js 依赖
    if [ ! -d "node_modules" ] || [ ! -f ".deps_installed" ]; then
        log_info "安装前端依赖..."
        npm install
        touch .deps_installed
    fi
    
    # 构建前端
    log_info "构建前端..."
    npm run build
    
    # 启动前端服务
    log_info "启动前端服务..."
    nohup npm run preview --port 80 \
        > "$LOG_DIR/frontend.log" 2>&1 &
    echo $! > "$PID_DIR/frontend.pid"
    
    cd "$PROJECT_ROOT"
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 5
    
    # 检查服务状态
    check_services_status
}

# 检查依赖
check_dependencies() {
    log_step "检查系统依赖..."
    
    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装"
        exit 1
    fi
    
    # 检查 Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js 未安装"
        exit 1
    fi
    
    # 检查 npm
    if ! command -v npm &> /dev/null; then
        log_error "npm 未安装"
        exit 1
    fi
    
    # 检查 PostgreSQL 或 Redis（如果使用）
    log_info "系统依赖检查完成"
}

# 检查服务状态
check_services_status() {
    log_step "检查服务状态..."
    
    local all_ok=true
    
    # 检查后端
    for i in {1..15}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            log_info "✅ 后端服务运行正常 (http://localhost:8000)"
            break
        fi
        if [ $i -eq 15 ]; then
            log_error "❌ 后端服务启动失败"
            all_ok=false
        fi
        sleep 2
    done
    
    # 检查前端
    for i in {1..15}; do
        if curl -s http://localhost > /dev/null 2>&1; then
            log_info "✅ 前端服务运行正常 (http://localhost)"
            break
        fi
        if [ $i -eq 15 ]; then
            log_error "❌ 前端服务启动失败"
            all_ok=false
        fi
        sleep 2
    done
    
    if [ "$all_ok" = true ]; then
        log_step "🎉 所有服务启动成功！"
        echo ""
        echo "🌐 前端地址: http://localhost"
        echo "🔧 后端API: http://localhost:8000"
        echo "📚 API文档: http://localhost:8000/docs"
        echo ""
        echo "📋 管理命令:"
        echo "  查看状态: ./status.sh"
        echo "  停止服务: ./stop.sh"
        echo "  查看日志: tail -f logs/*.log"
    else
        log_error "部分服务启动失败，请检查日志文件"
        echo "日志位置: $LOG_DIR/"
    fi
}

# 显示帮助信息
show_help() {
    echo "SDHZ 快递管理系统一键启动脚本"
    echo ""
    echo "使用方法:"
    echo "  $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --docker    使用 Docker Compose 启动 (推荐)"
    echo "  --dev       使用开发模式启动"
    echo "  --help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 --docker    # Docker 模式启动"
    echo "  $0 --dev       # 开发模式启动"
    echo "  $0             # 默认使用 Docker 模式"
}

# 主函数
main() {
    echo "🚀 SDHZ 快递管理系统启动脚本"
    echo "================================"
    
    # 停止已运行的服务
    stop_existing_services
    
    case "${1:-}" in
        --docker)
            start_docker
            ;;
        --dev)
            start_dev
            ;;
        --help|-h)
            show_help
            ;;
        "")
            log_info "使用默认 Docker 模式启动"
            start_docker
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"