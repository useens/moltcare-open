# Tools - 环境工具清单

> 🔧 **本地工具与环境配置** | 与 OpenClaw TOOLS.md 对应

---

## 🏠 工作环境

### 主机信息
| 属性 | 值 |
|------|-----|
| **主机名** | {{HOSTNAME}} |
| **操作系统** | {{OS}} |
| **架构** | {{ARCH}} |
| **工作目录** | {{WORKSPACE_DIR}} |

### Shell 环境
| 属性 | 值 |
|------|-----|
| **Shell** | {{SHELL}} |
| **终端** | {{TERMINAL}} |
| **编辑器** | {{EDITOR}} |

---

## 🔌 已配置工具

### 核心工具（必需）
| 工具 | 版本 | 用途 | 状态 |
|------|------|------|------|
| Python | {{PYTHON_VERSION}} | 脚本运行 | ✅ |
| Node.js | {{NODE_VERSION}} | 前端/工具 | {{STATUS}} |
| Git | {{GIT_VERSION}} | 版本控制 | ✅ |

### OpenClaw 特定工具
| 工具 | 状态 | 说明 |
|------|------|------|
| **read** | ✅ | 读取文件内容 |
| **edit** | ✅ | 编辑文件 |
| **write** | ✅ | 创建新文件 |
| **exec** | ✅ | 执行 shell 命令 |
| **memory_search** | ✅ | 语义检索记忆 |
| **sessions_spawn** | ✅ | 创建子代理 |
| **web_search** | {{STATUS}} | 网络搜索 |
| **browser** | {{STATUS}} | 浏览器控制 |

### 编程语言支持
| 语言 | 版本 | 包管理器 | 状态 |
|------|------|----------|------|
| Python | {{VERSION}} | pip/uv | ✅ |
| JavaScript | {{VERSION}} | npm/pnpm | {{STATUS}} |
| TypeScript | {{VERSION}} | npm/pnpm | {{STATUS}} |
| Go | {{VERSION}} | go mod | {{STATUS}} |
| Rust | {{VERSION}} | cargo | {{STATUS}} |

---

## 🔑 API Keys 与凭证

### 已配置的 API Keys
| 服务 | 状态 | 用途 | 备注 |
|------|------|------|------|
| GitHub | {{STATUS}} | 代码仓库 | {{NOTE}} |
| OpenAI | {{STATUS}} | AI 服务 | {{NOTE}} |
| Anthropic | {{STATUS}} | AI 服务 | {{NOTE}} |
| Other | {{STATUS}} | {{PURPOSE}} | {{NOTE}} |

### 凭证管理
```bash
# 凭证存储位置
~/.config/moltcare/credentials/
~/.env
~/.ssh/
```

**安全提示**：凭证文件已添加到 .gitignore，不会意外提交

---

## 📦 常用依赖

### Python 包
```
# requirements.txt 核心依赖
pyyaml
requests
pytest
black
mypy
```

### Node.js 包
```
# 全局安装
typescript
prettier
eslint
```

### 工具版本锁定
| 工具 | 当前版本 | 锁定版本 | 备注 |
|------|----------|----------|------|
| {{TOOL}} | {{CURRENT}} | {{LOCKED}} | {{NOTE}} |

---

## 🌐 网络配置

### 代理设置
| 类型 | 地址 | 状态 |
|------|------|------|
| HTTP_PROXY | {{URL}} | {{STATUS}} |
| HTTPS_PROXY | {{URL}} | {{STATUS}} |
| NO_PROXY | {{DOMAINS}} | {{STATUS}} |

### 常用端口
| 端口 | 服务 | 状态 |
|------|------|------|
| 3000 | 开发服务器 | {{STATUS}} |
| 8000 | API 服务 | {{STATUS}} |
| 8080 | 备用服务 | {{STATUS}} |

---

## 📝 工具使用习惯

### 常用命令速查
```bash
# 项目启动
{{START_COMMAND}}

# 测试运行
{{TEST_COMMAND}}

# 代码格式化
{{FORMAT_COMMAND}}

# 依赖安装
{{INSTALL_COMMAND}}
```

### 别名设置
```bash
# .bashrc/.zshrc 中定义的别名
alias {{ALIAS}}='{{COMMAND}}'
```

---

## 🔧 待配置工具

| 工具 | 用途 | 优先级 | 计划时间 |
|------|------|--------|----------|
| {{TOOL}} | {{PURPOSE}} | {{PRIORITY}} | {{DATE}} |

---

## 🔄 工具更新日志

| 日期 | 工具 | 变更 | 影响 |
|------|------|------|------|
| {{DATE}} | {{TOOL}} | {{CHANGE}} | {{IMPACT}} |

---

*此文件由 Agent 根据环境自动更新*
*使用 `exec` 工具获取实际版本信息*
*配合 OpenClaw TOOLS.md 使用*
