#!/bin/bash
# deploy-pack 安装脚本

echo "🚀 配置部署环境..."

# 检查 Docker
if command -v docker &> /dev/null; then
    echo "✓ Docker 已安装"
else
    echo "⚠️  Docker 未安装，请访问 https://docs.docker.com/get-docker/"
fi

if command -v docker-compose &> /dev/null; then
    echo "✓ Docker Compose 已安装"
else
    echo "⚠️  Docker Compose 未安装"
fi

# 复制配置文件
cp Dockerfile Dockerfile 2>/dev/null || echo "✓ Dockerfile 已存在"
cp docker-compose.yml docker-compose.yml 2>/dev/null || echo "✓ docker-compose.yml 已存在"

# 创建 .dockerignore
cat > .dockerignore << 'EOF'
# Git
.git
.gitignore

# Python
__pycache__
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info
dist
build

# Virtual environments
venv/
.venv/
env/
ENV/

# IDE
.vscode
.idea
*.swp
*.swo

# Testing
.pytest_cache
.coverage
htmlcov
.tox

# Documentation
docs/
*.md

# Local env files
.env
.env.local
.env.*.local

# CI/CD
.github/
.gitlab-ci.yml
.travis.yml

# Other
*.log
.DS_Store
EOF
echo "✓ 创建 .dockerignore"

# 创建部署脚本目录
mkdir -p scripts/deploy

# 创建本地部署脚本
cat > scripts/deploy/local.sh << 'EOF'
#!/bin/bash
# 本地部署脚本

echo "🚀 本地部署..."

# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 等待服务启动
echo "等待服务启动..."
sleep 5

# 检查健康状态
if docker-compose ps | grep -q "Up (healthy)"; then
    echo "✅ 服务已启动并健康运行"
    echo "访问: http://localhost:8000"
else
    echo "⚠️  服务可能未完全启动，查看日志:"
    docker-compose logs
fi
EOF
chmod +x scripts/deploy/local.sh
echo "✓ 创建 scripts/deploy/local.sh"

# 创建停止脚本
cat > scripts/deploy/stop.sh << 'EOF'
#!/bin/bash
# 停止部署脚本

echo "🛑 停止服务..."
docker-compose down

echo "✅ 服务已停止"
EOF
chmod +x scripts/deploy/stop.sh
echo "✓ 创建 scripts/deploy/stop.sh"

# 复制 GitHub Actions 工作流
mkdir -p .github/workflows
cp deploy.yml .github/workflows/deploy.yml 2>/dev/null || echo "✓ 部署工作流已配置"

echo ""
echo "🎉 deploy-pack 配置完成!"
echo ""
echo "使用方法:"
echo "  ./scripts/deploy/local.sh   # 本地部署"
echo "  ./scripts/deploy/stop.sh    # 停止服务"
echo "  docker-compose logs -f      # 查看日志"
echo ""
echo "查看指南:"
echo "  cat DEPLOY_GUIDE.md"
