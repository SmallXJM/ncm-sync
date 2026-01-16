# =============================
# Stage 1: 前端构建
# =============================
FROM node:20-alpine AS frontend

# 设置工作目录
WORKDIR /app/web

# 先拷贝依赖描述文件，利用 Docker 缓存加速构建
COPY web/package*.json ./

# 安装前端依赖（ci 更干净，锁定 package-lock.json）
RUN npm ci

# 拷贝前端源码
COPY web/ .

# 构建前端产物，默认输出到 web/dist
RUN npm run build


# =============================
# Stage 2: Python 后端 + 静态资源
# =============================
FROM python:3.11-slim

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    LANG=C.UTF-8 \
    TZ=Asia/Shanghai

WORKDIR /app

# 安装系统依赖（可根据需要启用）
# 注意：安装完后清理 apt 缓存，减少镜像体积
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     ffmpeg \
#  && rm -rf /var/lib/apt/lists/*

# 拷贝 Python 依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 拷贝后端源码
COPY ncm ./ncm

# 拷贝入口文件 main.py
COPY main.py ./

# 拷贝前端构建产物到后端服务目录
# 最终容器里的静态文件路径： /app/web/dist
COPY --from=frontend /app/web/dist ./web/dist

# 开放服务端口
EXPOSE 8000

# 容器启动命令：运行现有 main.py（main.py 内部已经调用 uvicorn）
CMD ["python", "main.py"]
