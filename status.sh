#!/bin/bash

# SDHZ 快递管理系统状态检查脚本

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$PROJECT_ROOT/.pids"
LOG_DIR="$PROJECT_ROOT/logs"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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

log_service() {
    echo -e "${CYAN}$1${NC}"
}

# 检查 Docker 服务状态
check_docker_status() {
    log_step "检查 Docker 服务状态..."
    
    cd "$PROJECT_ROOT"
    
    if [ ! -f "docker-compose.yml" ]; then
        log_warn "docker-compose.yml 文件不存在"
        return
    fi
    
    if ! command -v docker &> /dev/null; then
        log_warn "Docker 未安装"
        return
    fi
    
    local services=$(docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "")
    
    if [ -n "$services" ]; then
        echo "$services"
        echo ""
        
        # 检查具体服务健康状态
        local running_services=$(docker compose ps --services --filter "status=running" 2>/dev/null || echo "")
        if [ -n "$running_services" ]; then
            log_info "运行中的 Docker 服务: $(echo "$running_services" | tr '\n' ' ')"
        else
            log_warn "没有运行中的 Docker 服务"
        fi
    else
        log_info "没有 Docker 服务运行"
    fi
}

# 检查开发模式服务状态
check_dev_status() {
    log_step "检查开发模式服务状态..."
    
    local services_found=false
    
    # 检查 PID 文件记录的服务
    if [ -d "$PID_DIR" ]; then
        for pid_file in "$PID_DIR"/*.pid; do
            if [ -f "$pid_file" ]; then
                local pid=$(cat "$pid_file" 2>/dev/null || echo "")
                local service_name=$(basename "$pid_file" .pid)
                
                if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
                    local cmd=$(ps -p "$pid" -o cmd --no-headers 2>/dev/null || echo "未知命令")
                    log_service "✅ $service_name (PID: $pid) - 运行中"
                    echo "   命令: $cmd"
                    services_found=true
                else
                    log_service "❌ $service_name - 已停止 (PID文件存在但进程不存在)"
                    rm -f "$pid_file"
                fi
            fi
        done
    fi
    
    # 检查端口占用情况
    local ports=(8000 3000 80 5555)
    local port_services=("后端API" "前端开发" "前端生产" "Flower监控")
    
    for i in "${!ports[@]}"; do
        local port=${ports[$i]}
        local service_name=${port_services[$i]}
        
        if lsof -i :$port >/dev/null 2>&1; then
            local pid=$(lsof -ti :$port 2>/dev/null | head -1)
            local cmd=$(ps -p "$pid" -o cmd --no-headers 2>/dev/null || echo "未知命令")
            log_service "✅ $service_name (端口: $port, PID: $pid) - 运行中"
            echo "   命令: $cmd"
            services_found=true
        fi
    done
    
    if [ "$services_found" = false ]; then
        log_info "没有开发模式服务运行"
    fi
}

# 检查系统资源
check_system_resources() {
    log_step "检查系统资源..."
    
    # CPU 使用率
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    echo "CPU 使用率: ${cpu_usage}%"
    
    # 内存使用情况
    local memory_info=$(free -h | grep "Mem:")
    echo "内存使用: $memory_info"
    
    # 磁盘使用情况
    local disk_usage=$(df -h . | tail -1 | awk '{print "使用: " $3 "/" $2 " (" $5 ")"}')
    echo "磁盘使用: $disk_usage"
    
    echo ""
}

# 检查日志文件
check_logs() {
    log_step "检查日志文件..."
    
    if [ ! -d "$LOG_DIR" ]; then
        log_info "日志目录不存在: $LOG_DIR"
        return
    fi
    
    local log_files=$(find "$LOG_DIR" -name "*.log" -type f 2>/dev/null || true)
    
    if [ -n "$log_files" ]; then
        echo "日志文件:"
        while IFS= read -r log_file; do
            local size=$(du -h "$log_file" | cut -f1)
            local modified=$(stat -c %y "$log_file" | cut -d' ' -f1,2 | cut -d'.' -f1)
            echo "  $(basename "$log_file"): $size (修改时间: $modified)"
        done <<< "$log_files"
        
        echo ""
        echo "查看日志命令:"
        echo "  tail -f logs/*.log    # 实时查看所有日志"
        echo "  tail -f logs/backend.log    # 查看后端日志"
        echo "  tail -f logs/frontend.log   # 查看前端日志"
    else
        log_info "没有找到日志文件"
    fi
    
    echo ""
}

# 检查网络连通性
check_network() {
    log_step "检查服务连通性..."
    
    local endpoints=(
        "http://localhost:8000/health|后端健康检查"
        "http://localhost:8000/docs|API文档"
        "http://localhost|前端服务"
        "http://localhost:5555|Flower监控"
    )
    
    for endpoint_info in "${endpoints[@]}"; do
        local url=$(echo "$endpoint_info" | cut -d'|' -f1)
        local name=$(echo "$endpoint_info" | cut -d'|' -f2)
        
        if curl -s --max-time 5 "$url" > /dev/null 2>&1; then
            log_service "✅ $name ($url) - 可访问"
        else
            log_service "❌ $name ($url) - 不可访问"
        fi
    done
    
    echo ""
}

# 显示快速操作命令
show_quick_commands() {
    log_step "快速操作命令:"
    
    echo "启动服务:"
    echo "  ./start.sh --docker    # Docker 模式启动"
    echo "  ./start.sh --dev       # 开发模式启动"
    echo ""
    echo "停止服务:"
    echo "  ./stop.sh              # 停止所有服务"
    echo "  ./stop.sh --docker     # 仅停止 Docker 服务"
    echo ""
    echo "Docker 管理:"
    echo "  docker compose logs -f # 查看 Docker 日志"
    echo "  docker compose restart # 重启 Docker 服务"
    echo "  docker compose down -v # 停止并删除数据卷"
    echo ""
    echo "开发调试:"
    echo "  tail -f logs/*.log     # 查看开发模式日志"
    echo "  ps aux | grep -E '(uvicorn|celery|node)' # 查看相关进程"
}

# 显示帮助信息
show_help() {
    echo "SDHZ 快递管理系统状态检查脚本"
    echo ""
    echo "使用方法:"
    echo "  $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --docker    仅检查 Docker 服务状态"
    echo "  --dev       仅检查开发模式服务状态"
    echo "  --logs      仅检查日志文件"
    echo "  --network   仅检查网络连通性"
    echo "  --system    仅检查系统资源"
    echo "  --help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0           # 检查所有状态"
    echo "  $0 --docker  # 仅检查 Docker 状态"
    echo "  $0 --logs    # 仅检查日志文件"
}

# 主函数
main() {
    echo "📊 SDHZ 快递管理系统状态检查"
    echo "================================"
    echo ""
    
    case "${1:-}" in
        --docker)
            check_docker_status
            ;;
        --dev)
            check_dev_status
            ;;
        --logs)
            check_logs
            ;;
        --network)
            check_network
            ;;
        --system)
            check_system_resources
            ;;
        --help|-h)
            show_help
            ;;
        "")
            check_docker_status
            echo ""
            check_dev_status
            echo ""
            check_system_resources
            check_logs
            check_network
            show_quick_commands
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