#!/bin/bash

# SDHZ 数据库初始化脚本
# 自动初始化数据库并创建管理员用户

set -e

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

# 等待数据库就绪
wait_for_db() {
    local max_attempts=30
    local attempt=1
    
    log_step "等待数据库就绪..."
    
    while [ $attempt -le $max_attempts ]; do
        if docker compose exec -T postgres pg_isready -U postgres -d delivery_receipt > /dev/null 2>&1; then
            log_info "数据库已就绪"
            return 0
        fi
        
        log_info "等待数据库启动... ($attempt/$max_attempts)"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log_error "数据库启动超时"
    return 1
}

# 等待后端服务就绪
wait_for_backend() {
    local max_attempts=30
    local attempt=1
    
    log_step "等待后端服务就绪..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            log_info "后端服务已就绪"
            return 0
        fi
        
        log_info "等待后端服务启动... ($attempt/$max_attempts)"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log_error "后端服务启动超时"
    return 1
}

# 运行数据库迁移
run_migrations() {
    log_step "运行数据库迁移..."
    
    if docker compose exec -T backend alembic upgrade head; then
        log_info "数据库迁移完成"
    else
        log_error "数据库迁移失败"
        return 1
    fi
}

# 创建管理员用户
create_admin_user() {
    log_step "创建管理员用户..."
    
    if docker compose exec -T backend python create_admin_user.py; then
        log_info "管理员用户创建完成"
    else
        log_warn "管理员用户可能已存在或创建失败"
    fi
}

# 获取本机IP地址
get_local_ip() {
    # 尝试多种方法获取本机IP
    local ip=""
    
    # 方法1: 使用ip命令
    if command -v ip > /dev/null 2>&1; then
        ip=$(ip route get 1.1.1.1 2>/dev/null | grep -oP 'src \K\S+' | head -1)
    fi
    
    # 方法2: 使用hostname命令
    if [ -z "$ip" ] && command -v hostname > /dev/null 2>&1; then
        ip=$(hostname -I 2>/dev/null | awk '{print $1}')
    fi
    
    # 方法3: 使用ifconfig命令
    if [ -z "$ip" ] && command -v ifconfig > /dev/null 2>&1; then
        ip=$(ifconfig 2>/dev/null | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1' | head -1)
    fi
    
    # 默认使用localhost
    if [ -z "$ip" ]; then
        ip="localhost"
    fi
    
    echo "$ip"
}

# 显示访问信息
show_access_info() {
    local ip=$(get_local_ip)
    
    echo ""
    echo "🎉 SDHZ 快递管理系统部署完成！"
    echo "=================================="
    echo ""
    echo "📱 访问地址:"
    echo "  本地访问: http://localhost"
    if [ "$ip" != "localhost" ]; then
        echo "  网络访问: http://$ip"
    fi
    echo ""
    echo "🔧 管理地址:"
    echo "  后端API: http://localhost:8000"
    if [ "$ip" != "localhost" ]; then
        echo "           http://$ip:8000"
    fi
    echo "  API文档: http://localhost:8000/docs"
    echo "  任务监控: http://localhost:5555"
    echo ""
    echo "👤 管理员登录:"
    echo "  用户名: admin"
    echo "  密码: admin123"
    echo ""
    echo "⚠️  安全提醒:"
    echo "  - 请及时修改默认管理员密码"
    echo "  - 生产环境请修改数据库密码"
    echo "  - 建议配置防火墙限制访问"
    echo ""
    echo "🔍 管理命令:"
    echo "  查看状态: docker compose ps"
    echo "  查看日志: docker compose logs -f"
    echo "  停止服务: docker compose down"
    echo "  重启服务: docker compose restart"
    echo ""
}

# 主函数
main() {
    echo "🚀 SDHZ 数据库初始化脚本"
    echo "========================"
    echo ""
    
    # 检查Docker Compose是否运行
    if ! docker compose ps > /dev/null 2>&1; then
        log_error "Docker Compose 服务未运行，请先启动服务"
        echo "运行命令: docker compose up -d"
        exit 1
    fi
    
    # 等待数据库就绪
    if ! wait_for_db; then
        log_error "数据库未就绪，初始化失败"
        exit 1
    fi
    
    # 等待后端服务就绪
    if ! wait_for_backend; then
        log_error "后端服务未就绪，初始化失败"
        exit 1
    fi
    
    # 运行数据库迁移
    if ! run_migrations; then
        log_error "数据库迁移失败"
        exit 1
    fi
    
    # 创建管理员用户
    create_admin_user
    
    # 显示访问信息
    show_access_info
    
    log_step "✅ 初始化完成！"
}

# 运行主函数
main "$@"