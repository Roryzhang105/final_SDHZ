# 使用Python 3.12作为基础镜像
FROM python:3.12-slim as base

# 设置环境变量
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 创建应用用户
RUN groupadd --gid 1000 app \
    && useradd --uid 1000 --gid app --shell /bin/bash --create-home app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    # 编译依赖
    gcc \
    g++ \
    libpq-dev \
    # 运行时依赖
    libzbar0 \
    libzbar-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    # 网络工具
    curl \
    netcat-openbsd \
    # Chrome依赖
    wget \
    gnupg \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# 安装Chrome浏览器 (使用新的GPG密钥)
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/googlechrome-linux-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/googlechrome-linux-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# 升级pip
RUN pip install --upgrade pip setuptools wheel

# 设置工作目录
WORKDIR /app

# 复制requirements文件并安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY --chown=app:app . .

# 创建必要的目录
RUN mkdir -p uploads/codes uploads/receipts uploads/screenshots \
    && chown -R app:app /app

# 切换到应用用户
USER app

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]