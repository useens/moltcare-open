FROM python:3.11-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    chromium \
    chromium-driver \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libgdk-pixbuf2.0-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制 requirements（先复制以利用缓存）
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 安装 Scrapling 和 Playwright
RUN pip install scrapling[all] && \
    python -m patchright install chromium

# 创建非 root 用户
RUN useradd -m -u 1000 agent && \
    mkdir -p /app/data /app/config /app/logs && \
    chown -R agent:agent /app

# 切换到非 root 用户
USER agent

# 设置环境变量
ENV PYTHONPATH=/app
ENV AGENT_REACH_HOME=/app/data
ENV PATH="/home/agent/.local/bin:${PATH}"

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

# 暴露端口
EXPOSE 8080

# 启动命令
CMD ["python", "-m", "agent_reach.server"]
