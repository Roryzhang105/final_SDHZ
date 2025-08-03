# Docker 权限问题解决指南

## 🔍 问题诊断

你遇到的错误：
```
permission denied while trying to connect to the Docker daemon socket
```

这表示当前用户无法访问 Docker 守护进程。

## ✅ 已确认工作的部分
- ✅ Docker 客户端已安装 (v28.3.2)
- ✅ Docker Compose 已安装 (v2.38.2)  
- ✅ docker-compose.yml 已修复（移除过时的 version 字段）

## 🔧 解决方案

### 方案1：修复 Docker 权限（推荐）

```bash
# 1. 添加用户到 docker 组
sudo usermod -aG docker $USER

# 2. 重新登录或刷新组权限
newgrp docker
# 或者注销重新登录

# 3. 验证权限
docker run hello-world

# 4. 启动 PostgreSQL
docker-compose up -d postgres redis
```

### 方案2：使用 sudo 运行 Docker

```bash
# 启动 PostgreSQL
sudo docker-compose up -d postgres redis

# 检查状态
sudo docker-compose ps

# 停止服务
sudo docker-compose down
```

### 方案3：安装系统 PostgreSQL（如果 Docker 问题持续）

```bash
# 使用我们准备的安装脚本
./install_system_postgres.sh

# 或手动安装
sudo apt update
sudo apt install -y postgresql postgresql-contrib
sudo systemctl start postgresql
```

## 🚀 下一步操作

### 如果 Docker 权限修复成功：

```bash
# 1. 启动服务
docker-compose up -d postgres redis

# 2. 等待服务启动（约10-15秒）
sleep 15

# 3. 检查服务状态
docker-compose ps

# 4. 迁移数据
source venv/bin/activate
python scripts/migrate_to_postgres.py --sqlite-path ./delivery_receipt.db
```

### 如果使用系统 PostgreSQL：

```bash
# 1. 安装 PostgreSQL
./install_system_postgres.sh

# 2. 测试连接
source venv/bin/activate
python test_postgres_connection.py

# 3. 迁移数据
python scripts/migrate_to_postgres.py --sqlite-path ./delivery_receipt.db
```

## 🔍 验证步骤

### 验证 Docker 权限：
```bash
docker run --rm hello-world
```

### 验证 PostgreSQL 连接：
```bash
source venv/bin/activate
python test_postgres_connection.py
```

### 验证数据迁移：
```bash
python scripts/migrate_to_postgres.py --help
```

## 💡 常见问题

### 1. Docker 权限问题持续存在
- 确保完全注销并重新登录
- 或重启系统
- 检查 Docker 服务：`sudo systemctl status docker`

### 2. PostgreSQL 连接失败
- 确保容器正在运行：`docker-compose ps`
- 检查端口：`netstat -tlnp | grep 5432`
- 查看日志：`docker-compose logs postgres`

### 3. 数据迁移失败
- 检查 SQLite 文件存在：`ls -la delivery_receipt.db`
- 确保虚拟环境激活：`which python`
- 查看详细错误：`python scripts/migrate_to_postgres.py --sqlite-path ./delivery_receipt.db`

## 📞 获取帮助

如果问题持续存在：
1. 查看 `POSTGRESQL_MIGRATION.md` 获取详细指南
2. 运行 `python test_postgres_connection.py` 获取具体错误信息
3. 检查 `migration.log` 文件（如果存在）