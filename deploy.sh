#!/bin/bash

# SDHZ 快递管理系统一键部署脚本
# 完整的Docker部署流程，包含数据库初始化和IP自动配置

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

log_success() {
    echo -e "${PURPLE}[SUCCESS]${NC} $1"
}

log_header() {
    echo -e "${CYAN}$1${NC}"
}

# 检查系统要求
check_requirements() {
    log_step "检查系统要求..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装"
        echo "请先安装Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! docker compose version &> /dev/null; then
        log_error "Docker Compose 未安装或版本过低"
        echo "请确保Docker Compose版本 >= 2.0"
        exit 1
    fi
    
    # 检查端口占用
    local ports=(80 5432 6379 8000 5555)
    local occupied_ports=()
    
    for port in "${ports[@]}"; do
        if lsof -i :$port >/dev/null 2>&1; then
            occupied_ports+=($port)
        fi
    done
    
    if [ ${#occupied_ports[@]} -gt 0 ]; then
        log_warn "以下端口被占用: ${occupied_ports[*]}"
        echo "部署可能会失败，是否继续？(y/N)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            log_info "部署已取消"
            exit 0
        fi
    fi
    
    log_success "系统要求检查通过"
}

# 获取本机IP地址
get_local_ip() {
    local ip=""
    
    # 尝试多种方法获取本机IP
    if command -v ip > /dev/null 2>&1; then
        ip=$(ip route get 1.1.1.1 2>/dev/null | grep -oP 'src \K\S+' | head -1)
    fi
    
    if [ -z "$ip" ] && command -v hostname > /dev/null 2>&1; then
        ip=$(hostname -I 2>/dev/null | awk '{print $1}')
    fi
    
    if [ -z "$ip" ] && command -v ifconfig > /dev/null 2>&1; then
        ip=$(ifconfig 2>/dev/null | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1' | head -1)
    fi
    
    # 默认使用localhost
    if [ -z "$ip" ]; then
        ip="localhost"
    fi
    
    echo "$ip"
}

# 停止现有服务
stop_existing_services() {
    log_step "停止现有服务..."
    
    if docker compose ps -q > /dev/null 2>&1; then
        log_info "停止现有Docker Compose服务"
        docker compose down --remove-orphans
    fi
    
    # 清理悬空容器和镜像
    log_info "清理Docker资源..."
    docker system prune -f > /dev/null 2>&1 || true
    
    log_success "现有服务已停止"
}

# 构建和启动服务
build_and_start_services() {
    log_step "构建和启动服务..."
    
    cd "$PROJECT_ROOT"
    
    # 构建服务
    log_info "构建Docker镜像..."
    if ! docker compose build --no-cache; then
        log_error "Docker镜像构建失败"
        exit 1
    fi
    
    # 启动服务
    log_info "启动所有服务..."
    if ! docker compose up -d; then
        log_error "服务启动失败"
        docker compose logs
        exit 1
    fi
    
    log_success "服务启动完成"
}

# 等待服务就绪
wait_for_services() {
    log_step "等待服务就绪..."
    
    # 等待数据库
    log_info "等待数据库启动..."
    local max_attempts=60
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker compose exec -T postgres pg_isready -U postgres -d delivery_receipt > /dev/null 2>&1; then
            log_success "数据库已就绪"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            log_error "数据库启动超时"
            docker compose logs postgres
            exit 1
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    # 等待后端服务
    log_info "等待后端服务启动..."
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            log_success "后端服务已就绪"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            log_error "后端服务启动超时"
            docker compose logs backend
            exit 1
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    # 等待前端服务
    log_info "等待前端服务启动..."
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost/ > /dev/null 2>&1; then
            log_success "前端服务已就绪"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            log_error "前端服务启动超时"
            docker compose logs frontend
            exit 1
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
}

# 初始化数据库
initialize_database() {
    log_step "初始化数据库..."
    
    # 运行数据库迁移
    log_info "运行数据库迁移..."
    if ! docker compose exec -T backend alembic upgrade head; then
        log_error "数据库迁移失败"
        docker compose logs backend
        exit 1
    fi
    
    # 创建管理员用户
    log_info "创建管理员用户..."
    if ! docker compose exec -T backend python create_admin_user.py; then
        log_warn "管理员用户创建失败或已存在"
    fi
    
    log_success "数据库初始化完成"
}

# 验证部署
verify_deployment() {
    log_step "验证部署..."
    
    local all_ok=true
    
    # 检查服务状态
    log_info "检查Docker服务状态..."
    if ! docker compose ps --format table; then
        log_error "无法获取服务状态"
        all_ok=false
    fi
    
    # 检查健康状态
    local services=("backend:8000/health" "frontend:80/")
    
    for service_info in "${services[@]}"; do
        IFS=':' read -r service_name port_path <<< "$service_info"
        local url="http://localhost:$port_path"
        
        if curl -s "$url" > /dev/null 2>&1; then
            log_success "✅ $service_name 服务正常"
        else
            log_error "❌ $service_name 服务异常"
            all_ok=false
        fi
    done
    
    if [ "$all_ok" = true ]; then
        log_success "部署验证通过"
        return 0
    else
        log_error "部署验证失败"
        return 1
    fi
}

# 显示部署结果
show_deployment_result() {
    local ip=$(get_local_ip)
    
    echo ""
    log_header "🎉 SDHZ 快递管理系统部署成功！"
    echo "========================================"
    echo ""
    echo "📱 访问地址:"
    echo "  本地访问: http://localhost"
    if [ "$ip" != "localhost" ]; then
        echo "  网络访问: http://$ip"
    fi
    echo ""
    echo "🔧 管理面板:"
    echo "  后端API: http://localhost:8000"
    if [ "$ip" != "localhost" ]; then
        echo "           http://$ip:8000"
    fi
    echo "  API文档: http://localhost:8000/docs"
    echo "  接口测试: http://localhost:8000/redoc"
    echo "  任务监控: http://localhost:5555"
    echo ""
    echo "👤 默认管理员账号:"
    echo "  用户名: admin"
    echo "  密码: admin123"
    echo ""
    echo "🔍 常用管理命令:"
    echo "  查看服务状态: docker compose ps"
    echo "  查看服务日志: docker compose logs -f [服务名]"
    echo "  重启服务: docker compose restart [服务名]"
    echo "  停止所有服务: docker compose down"
    echo "  停止并删除数据: docker compose down -v"
    echo ""
    echo "⚠️  安全提醒:"
    echo "  - 首次登录后请立即修改管理员密码"
    echo "  - 生产环境请修改数据库默认密码"
    echo "  - 建议配置防火墙和HTTPS"
    echo "  - 定期备份数据库数据"
    echo ""
    log_success "部署完成！现在可以访问系统了。"
}

# 错误处理
cleanup_on_error() {
    log_error "部署过程中发生错误"
    echo ""
    echo "🔍 故障排除建议:"
    echo "1. 检查Docker服务是否正常运行"
    echo "2. 确保端口没有被占用"
    echo "3. 检查磁盘空间是否充足"
    echo "4. 查看详细错误日志:"
    echo "   docker compose logs"
    echo ""
    echo "🔄 重新部署:"
    echo "   $0 --force"
    echo ""
}

# 显示帮助信息
show_help() {
    echo "SDHZ 快递管理系统一键部署脚本"
    echo ""
    echo "使用方法:"
    echo "  $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --force     强制重新部署，清理所有数据"
    echo "  --help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0          # 正常部署"
    echo "  $0 --force  # 强制重新部署"
    echo ""
}

# 主函数
main() {
    local force_deploy=false
    
    # 解析参数
    case "${1:-}" in
        --force)
            force_deploy=true
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        "")
            # 默认部署
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
    
    # 设置错误处理
    trap cleanup_on_error ERR
    
    # 显示开始信息
    echo ""
    log_header "🚀 SDHZ 快递管理系统一键部署"
    log_header "================================"
    echo ""
    
    if [ "$force_deploy" = true ]; then
        log_warn "强制部署模式：将清理所有现有数据"
        echo "继续？(y/N)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            log_info "部署已取消"
            exit 0
        fi
    fi
    
    # 执行部署步骤
    check_requirements
    stop_existing_services
    build_and_start_services
    wait_for_services
    initialize_database
    
    if verify_deployment; then
        show_deployment_result
    else
        log_error "部署失败，请检查错误信息"
        exit 1
    fi
}

# 运行主函数
main "$@"