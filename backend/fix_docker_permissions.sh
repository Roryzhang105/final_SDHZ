#!/bin/bash
# Docker 权限修复脚本

echo "🔧 Docker 权限修复指南"
echo "======================"

# 检查当前用户是否在 docker 组中
if groups $USER | grep -q '\bdocker\b'; then
    echo "✅ 用户 $USER 已在 docker 组中"
else
    echo "❌ 用户 $USER 不在 docker 组中"
    echo ""
    echo "请运行以下命令修复权限："
    echo "sudo usermod -aG docker $USER"
    echo ""
    echo "然后重新登录或运行："
    echo "newgrp docker"
    echo ""
fi

# 检查 Docker 服务状态
echo "🔍 检查 Docker 服务状态..."
if systemctl is-active --quiet docker; then
    echo "✅ Docker 服务正在运行"
elif systemctl is-enabled --quiet docker 2>/dev/null; then
    echo "⚠️  Docker 服务已安装但未运行"
    echo "启动 Docker: sudo systemctl start docker"
else
    echo "❌ Docker 服务未安装"
    echo ""
    echo "安装 Docker:"
    echo "curl -fsSL https://get.docker.com -o get-docker.sh"
    echo "sudo sh get-docker.sh"
fi

# 检查 Docker 权限
echo ""
echo "🧪 测试 Docker 权限..."
if docker version >/dev/null 2>&1; then
    echo "✅ Docker 权限正常"
    
    # 测试 Docker Compose
    if command -v docker-compose >/dev/null 2>&1; then
        echo "✅ Docker Compose 可用"
    elif docker compose version >/dev/null 2>&1; then
        echo "✅ Docker Compose (plugin) 可用"
    else
        echo "⚠️  Docker Compose 未安装"
        echo "安装: sudo apt install docker-compose-plugin"
    fi
else
    echo "❌ Docker 权限问题或服务未运行"
    echo ""
    echo "解决步骤："
    echo "1. sudo usermod -aG docker $USER"
    echo "2. 注销并重新登录，或运行: newgrp docker"
    echo "3. sudo systemctl start docker"
    echo "4. 测试: docker --version"
fi

echo ""
echo "📖 如果 Docker 权限问题持续存在，请使用系统 PostgreSQL："
echo "./install_system_postgres.sh"