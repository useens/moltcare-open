# TOOLS.md - 高级工具配置

## 🏠 工作环境

**主机**: 生产环境服务器  
**OpenClaw版本**: v2.x  
**模型**: kimi-coding/k2p5  
**工作目录**: `/root/.openclaw/workspace`

---

## 🔌 API 连接配置

### 搜索API

| 服务 | 状态 | 配置 |
|------|------|------|
| **Brave Search** | ✅ 已配置 | API Key: `${BRAVE_API_KEY}` |
| **Google Search** | ⏸️ 待配置 | - |
| **Bing Search** | ⏸️ 待配置 | - |

### AI模型API

| 服务 | 状态 | 模型 |
|------|------|------|
| **Kimi** | ✅ 已配置 | kimi-coding/k2p5 |
| **OpenAI** | ✅ 已配置 | gpt-4o |
| **Claude** | ⏸️ 待配置 | - |
| **GLM-5** | ✅ 已配置 | step-3.5-flash |

### 存储API

| 服务 | 状态 | 用途 |
|------|------|------|
| **GitHub** | ✅ 已配置 | 代码托管 |
| **Redis** | ✅ 已配置 | 缓存/消息队列 |
| **飞书** | ✅ 已配置 | 文档/协作 |

---

## 🛠️ 工具分类

### 文件操作工具

| 工具 | 用途 | 使用频率 |
|------|------|----------|
| `read` | 读取文件内容 | 高频 |
| `write` | 写入文件 | 高频 |
| `edit` | 精确编辑文件 | 高频 |
| `exec` | 执行shell命令 | 中频 |

### 网络工具

| 工具 | 用途 | 注意事项 |
|------|------|----------|
| `web_search` | 网络搜索 | 使用Brave API |
| `web_fetch` | 获取网页 | 注意反爬 |
| `browser` | 浏览器控制 | 微信文章用camoufox |

### 系统工具

| 工具 | 用途 | 安全级别 |
|------|------|----------|
| `process` | 进程管理 | 中 |
| `nodes` | 节点管理 | 高 |
| `message` | 消息发送 | 高 |
| `subagents` | 子代理管理 | 高 |

---

## 📝 使用规则

### 工具选择决策树

```
需要操作文件？
    ├── 是 → 使用 read/write/edit
    └── 否 → 需要网络数据？
            ├── 是 → 需要JS渲染？
            │       ├── 是 → 使用 browser
            │       └── 否 → 使用 web_fetch
            └── 否 → 需要系统操作？
                    ├── 是 → 使用 exec/process
                    └── 否 → 需要管理子代理？
                            ├── 是 → 使用 subagents
                            └── 否 → 使用其他工具
```

### 工具调用优先级

1. **文件优先** - 优先使用文件操作工具
2. **缓存优先** - 优先使用已缓存数据
3. **并行优先** - 独立任务并行执行
4. **安全优先** - 高危操作需确认

### 强制规则

| 场景 | 必须使用 | 禁止尝试 |
|------|----------|----------|
| 微信文章 | **camoufox** | web_fetch, browser |
| 大量文件 | **subagents** | 串行执行 |
| 敏感操作 | **二次确认** | 自动执行 |

---

## 🛡️ 安全策略

### 高危命令白名单

**禁止自动执行**：
```bash
rm -rf /
mkfs.*
dd if=/dev/zero
> /etc/passwd
```

### 敏感文件保护

**访问需授权**：
- `.env` - 环境变量
- `*.key`, `*.pem` - 密钥
- `id_rsa` - SSH私钥
- `*.password` - 密码文件

### 网络访问限制

**外部访问需确认**：
- 发送邮件
- 发布帖子
- 创建GitHub Issue/PR
- 发送即时消息

---

## 📊 工具性能

| 工具 | 平均响应 | 成功率 | 备注 |
|------|----------|--------|------|
| read | 10ms | 99.9% | - |
| write | 20ms | 99.9% | - |
| web_search | 2s | 95% | 受API限制 |
| browser | 5s | 90% | 受页面复杂度影响 |
| exec | 500ms | 98% | 取决于命令 |

---

## 🔧 自定义脚本

### 脚本位置

```
scripts/
├── check-system.sh      # 系统检查
├── backup-config.sh     # 配置备份
├── update-deps.sh       # 依赖更新
├── security-audit.sh    # 安全审计
└── performance-test.sh  # 性能测试
```

### 常用命令

```bash
# 系统检查
./scripts/check-system.sh

# 创建备份
./scripts/backup-config.sh

# 更新依赖
./scripts/update-deps.sh

# 安全审计
./scripts/security-audit.sh
```

---

*高级工具配置 v2.0 | 2026-03-11*
