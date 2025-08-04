#!/bin/bash

# SDHZ 快递管理系统停止脚本

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$PROJECT_ROOT/.pids"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# 停止 Docker 服务
stop_docker() {
    log_step "停止 Docker 服务..."
    
    cd "$PROJECT_ROOT"
    
    if [ -f "docker-compose.yml" ]; then
        docker compose down
        log_info "Docker 服务已停止"
    else
        log_warn "docker-compose.yml 文件不存在"
    fi
}

# 停止开发模式服务
stop_dev() {
    log_step "停止开发模式服务..."
    
    local stopped_count=0
    
    # 停止通过PID文件记录的进程
    if [ -d "$PID_DIR" ]; then
        for pid_file in "$PID_DIR"/*.pid; do
            if [ -f "$pid_file" ]; then
                local pid=$(cat "$pid_file" 2>/dev/null || echo "")
                local service_name=$(basename "$pid_file" .pid)
                
                if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
                    log_info "停止 $service_name (PID: $pid)"
                    kill -TERM "$pid" 2>/dev/null || true
                    
                    # 等待进程结束
                    for i in {1..10}; do
                        if ! kill -0 "$pid" 2>/dev/null; then
                            break
                        fi
                        sleep 1
                    done
                    
                    # 如果进程仍在运行，强制杀死
                    if kill -0 "$pid" 2>/dev/null; then
                        log_warn "强制停止 $service_name"
                        kill -KILL "$pid" 2>/dev/null || true
                    fi
                    
                    stopped_count=$((stopped_count + 1))
                else
                    log_warn "$service_name 进程不存在或已停止"
                fi
                
                rm -f "$pid_file"
            fi
        done
    fi
    
    # 停止可能遗漏的进程（通过端口）
    local ports=(8000 5173 80 5555)
    for port in "${ports[@]}"; do
        local pids=$(lsof -ti :$port 2>/dev/null || true)
        if [ -n "$pids" ]; then
            log_info "停止占用端口 $port 的进程"
            echo "$pids" | xargs -r kill -TERM 2>/dev/null || true
            sleep 2
            # 强制杀死未响应的进程
            pids=$(lsof -ti :$port 2>/dev/null || true)
            if [ -n "$pids" ]; then
                echo "$pids" | xargs -r kill -KILL 2>/dev/null || true
            fi
            stopped_count=$((stopped_count + 1))
        fi
    done
    
    # 停止 Celery 相关进程
    local celery_pids=$(pgrep -f "celery.*app.tasks.celery_app" 2>/dev/null || true)
    if [ -n "$celery_pids" ]; then
        log_info "停止 Celery 进程"
        echo "$celery_pids" | xargs -r kill -TERM 2>/dev/null || true
        sleep 2
        celery_pids=$(pgrep -f "celery.*app.tasks.celery_app" 2>/dev/null || true)
        if [ -n "$celery_pids" ]; then
            echo "$celery_pids" | xargs -r kill -KILL 2>/dev/null || true
        fi
        stopped_count=$((stopped_count + 1))
    fi
    
    # 停止 uvicorn 进程
    local uvicorn_pids=$(pgrep -f "uvicorn.*app.main:app" 2>/dev/null || true)
    if [ -n "$uvicorn_pids" ]; then
        log_info "停止 Uvicorn 进程"
        echo "$uvicorn_pids" | xargs -r kill -TERM 2>/dev/null || true
        sleep 2
        uvicorn_pids=$(pgrep -f "uvicorn.*app.main:app" 2>/dev/null || true)
        if [ -n "$uvicorn_pids" ]; then
            echo "$uvicorn_pids" | xargs -r kill -KILL 2>/dev/null || true
        fi
        stopped_count=$((stopped_count + 1))
    fi
    
    if [ $stopped_count -gt 0 ]; then
        log_info "已停止 $stopped_count 个服务"
    else
        log_warn "没有发现运行中的服务"
    fi
}

# 检查服务状态
check_status() {
    log_step "检查服务状态..."
    
    local running_services=0
    
    # 检查 Docker 服务
    if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
        local docker_services=$(docker compose ps --services --filter "status=running" 2>/dev/null | wc -l || echo "0")
        if [ "$docker_services" -gt 0 ]; then
            log_info "发现 $docker_services 个运行中的 Docker 服务"
            running_services=$((running_services + docker_services))
        fi
    fi
    
    # 检查端口占用
    local ports=(8000 5173 80 5555)
    for port in "${ports[@]}"; do
        if lsof -i :$port >/dev/null 2>&1; then
            local pid=$(lsof -ti :$port 2>/dev/null | head -1)
            log_info "端口 $port 被占用 (PID: $pid)"
            running_services=$((running_services + 1))
        fi
    done
    
    if [ $running_services -eq 0 ]; then
        log_info "✅ 所有服务已停止"
    else
        log_warn "⚠️ 发现 $running_services 个运行中的服务"
    fi
}

# 显示帮助信息
show_help() {
    echo "SDHZ 快递管理系统停止脚本"
    echo ""
    echo "使用方法:"
    echo "  $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --docker    停止 Docker 服务"
    echo "  --dev       停止开发模式服务"
    echo "  --all       停止所有服务 (默认)"
    echo "  --status    检查服务状态"
    echo "  --help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0           # 停止所有服务"
    echo "  $0 --docker  # 仅停止 Docker 服务"
    echo "  $0 --dev     # 仅停止开发模式服务"
    echo "  $0 --status  # 检查服务状态"
}

# 主函数
main() {
    echo "🛑 SDHZ 快递管理系统停止脚本"
    echo "================================"
    
    case "${1:-}" in
        --docker)
            stop_docker
            ;;
        --dev)
            stop_dev
            ;;
        --all|"")
            stop_docker
            stop_dev
            ;;
        --status)
            check_status
            ;;
        --help|-h)
            show_help
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
    
    # 最终状态检查
    if [ "${1:-}" != "--status" ]; then
        echo ""
        check_status
    fi
}

# 运行主函数
main "$@"