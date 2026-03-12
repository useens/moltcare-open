# 部署指南

> MoltCare deploy-pack 自动生成

## 🐳 Docker 部署

### 快速开始

```bash
# 构建镜像
docker build -t myapp:latest .

# 运行容器
docker run -d -p 8000:8000 myapp:latest

# 查看日志
docker logs -f <container_id>
```

### Docker Compose (推荐)

```bash
# 启动所有服务
docker-compose up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f app

# 停止服务
docker-compose down

# 完全清理（包括数据）
docker-compose down -v
```

## 🚀 CI/CD 部署

### GitHub Actions 自动部署

已配置工作流：
- **Build**: 每次推送到 main 分支或标签时构建 Docker 镜像
- **Deploy Staging**: 自动部署到预发布环境
- **Deploy Production**: 标签推送时部署到生产环境

### 环境配置

在 GitHub 设置中添加 Secrets：
- `STAGING_HOST`: 预发布服务器地址
- `STAGING_SSH_KEY`: SSH 私钥
- `PRODUCTION_HOST`: 生产服务器地址
- `PRODUCTION_SSH_KEY`: SSH 私钥

## 📋 生产环境检查清单

- [ ] 使用非 root 用户运行容器
- [ ] 配置健康检查
- [ ] 设置资源限制 (CPU/内存)
- [ ] 配置日志收集
- [ ] 设置监控告警
- [ ] 配置备份策略
- [ ] 启用 HTTPS
- [ ] 配置防火墙规则
- [ ] 设置环境变量 (非硬编码)

---

*此指南由 MoltCare deploy-pack 自动生成*
