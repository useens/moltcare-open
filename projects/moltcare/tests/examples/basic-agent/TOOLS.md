# TOOLS.md - 基础工具配置

## 工作环境

**主机**: 本地开发环境
**OpenClaw版本**: v2.x
**工作目录**: ~/.openclaw/workspace

## 可用工具

### 文件操作
- `read` - 读取文件内容
- `write` - 写入文件
- `edit` - 编辑文件
- `exec` - 执行命令

### 网络工具
- `web_search` - 网络搜索
- `web_fetch` - 获取网页内容
- `browser` - 浏览器控制

### 系统工具
- `process` - 进程管理
- `nodes` - 节点管理
- `message` - 消息发送

## API配置

### 搜索API
- 服务: Brave Search
- 状态: [待配置]
- API Key: [待配置]

### 模型API
- 服务: OpenAI/Claude
- 状态: [待配置]
- API Key: [待配置]

## 使用规则

### 工具优先级
1. 优先使用文件操作工具
2. 需要网络时使用web_search
3. 复杂操作使用browser
4. 系统级操作使用exec

### 安全限制
- 高危命令需确认
- 敏感文件需授权
- 外部通信需审核
- 系统修改需备份

## 自定义脚本

### 常用脚本位置
- `scripts/` - 项目脚本
- `tools/` - 自定义工具

### 脚本命名规范
- `check-*.sh` - 检查脚本
- `backup-*.sh` - 备份脚本
- `setup-*.sh` - 设置脚本
