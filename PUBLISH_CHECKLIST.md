# MoltCare-Open Skill 发布清单

## 发布前检查

### ✅ 必需文件
- [x] SKILL.md - Skill 定义文件
- [x] 有效的前置元数据 (name, description)
- [x] 打包后的 .skill 文件
- [x] 安装脚本

### ✅ Skill 内容验证
- [x] 名称: moltcare-open
- [x] 描述: 包含触发词和功能说明
- [x] 文件结构符合规范
- [x] 无符号链接 (symlinks)
- [x] 总大小 < 1MB (当前: 16KB)

### ✅ 功能测试
- [x] 安装脚本可执行
- [x] 模板文件完整
- [x] 文档清晰

---

## 发布步骤

### 1. 登录 ClawHub
```bash
# 方式1: 浏览器登录 (本地环境)
clawhub login

# 方式2: Token 登录 (远程/CI环境)
clawhub login --token YOUR_API_TOKEN
```

获取 API Token:
1. 访问 https://clawhub.com
2. 登录账户
3. 进入 Settings → API Tokens
4. 生成新 Token

### 2. 验证登录
```bash
clawhub whoami
```

### 3. 发布 Skill
```bash
cd ~/.openclaw/workspace/moltcare-open
clawhub publish skill/
```

### 4. 验证发布
```bash
clawhub search moltcare-open
clawhub inspect moltcare-open
```

---

## 发布后

### 安装测试
```bash
# 清理旧安装
rm -rf ~/.openclaw/skills/moltcare-open

# 从 ClawHub 安装
clawhub install moltcare-open

# 验证安装
ls -la ~/.openclaw/skills/moltcare-open/
```

### 更新 README
在 GitHub README 中添加安装说明：
```markdown
## 安装

### 通过 ClawHub (推荐)
```bash
clawhub install moltcare-open
```

### 手动安装
```bash
curl -fsSL .../install.sh | bash
```
```

---

## 版本管理

### 更新 Skill
1. 修改 skill/ 目录下的文件
2. 重新打包: `clawhub publish skill/`
3. ClawHub 会自动处理版本

### 版本号规则
- 遵循语义化版本: v3.1.0
- 在 SKILL.md 中更新版本说明
- Git tag 对应版本

---

## 状态

**当前状态**: 🟡 等待登录

**下一步**: 获取 ClawHub API Token 并登录
