# 部署指南

## 环境要求

### 硬件
- CPU: 2核+
- 内存: 4GB+
- 磁盘: 10GB+

### 软件
- Node.js 18+
- npm 9+
- Git (可选)

## 安装步骤

### 1. 安装依赖
```bash
cd vector-memory
npm install
```

### 2. 初始化索引
```bash
node vector_memory_local.js --sync
```

### 3. 验证安装
```bash
node vector_memory_local.js --status
```
