# 多服务构建 Dockerfile
# 这个文件支持基于 --target 参数构建不同的服务

# 前端构建阶段
FROM node:22.12-alpine AS frontend-builder

# 安装必要的构建工具
RUN apk add --no-cache python3 make g++

WORKDIR /app
COPY frontend/package*.json ./
# 安装依赖（包括开发依赖用于构建）
RUN npm ci --include=dev --ignore-scripts
COPY frontend/ ./
RUN npm run build

# 前端生产镜像
FROM nginx:1.27-alpine AS frontend
COPY --from=frontend-builder /app/dist /usr/share/nginx/html
COPY <<EOF /etc/nginx/conf.d/default.conf
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/json;
}
EOF
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1
CMD ["nginx", "-g", "daemon off;"]

# 后端生产镜像
FROM python:3.12-slim AS backend
WORKDIR /app
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    netcat-openbsd \
    wget \
    gnupg \
    unzip \
    curl \
    libzbar0 \
    libzbar-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 安装Chrome浏览器 (使用新的GPG密钥)
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/googlechrome-linux-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/googlechrome-linux-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY backend/ ./
RUN mkdir -p uploads/codes uploads/receipts uploads/screenshots

RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]