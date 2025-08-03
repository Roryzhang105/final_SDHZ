#!/bin/bash

echo "🔧 Docker 状态检查"
echo "=================="

# 检查用户是否在 docker 组中
if groups $USER | grep -q 'docker'; then
    echo "✅ 用户在 docker 组中"
else
    echo "❌ 用户不在 docker 组中"
    echo "解决方法: sudo usermod -aG docker $USER"
    echo "然后重新登录或运行: newgrp docker"
fi

# 检查 Docker 权限
echo ""
echo "🧪 测试 Docker 权限..."
if docker version >/dev/null 2>&1; then
    echo "✅ Docker 权限正常"
    docker --version
else
    echo "❌ Docker 权限问题"
    echo "错误信息:"
    docker version 2>&1 | head -3
fi

echo ""
echo "💡 如果 Docker 有问题，请使用系统 PostgreSQL:"
echo "   ./install_system_postgres.sh"