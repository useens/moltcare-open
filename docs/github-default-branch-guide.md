# GitHub 默认分支设置指南

## 如何找到 Default branch 设置

### 步骤

1. **打开仓库页面**
   ```
   https://github.com/linlinofVM/sensen-backup
   ```

2. **点击 Settings（设置）**
   - 在仓库页面顶部导航栏
   - 在最右边，图标是 ⚙️
   
   ![位置] 导航栏: Code | Issues | Pull requests | **Settings**

3. **在 Settings 页面左侧菜单**
   - 找到 **General**（一般设置，通常默认就是）
   - 向下滚动到 **Default branch** 部分
   
   ![位置] 页面左侧: General | Access | Code and automation | ...

4. **找到 Default branch 区域**
   ```
   Default branch
   ─────────────────────────────────────
   The default branch is considered the "base" branch ...
   
   [main]  [🔃 切换图标]
   ```

5. **切换默认分支**
   - 点击 🔃 图标
   - 选择 **main**
   - 点击 "Update"
   - 确认 "I understand, update the default branch"

### 快速链接

直接访问:
```
https://github.com/linlinofVM/sensen-backup/settings
```

然后向下滚动找到 "Default branch" 部分。

### 截图示意

```
┌─────────────────────────────────────────────────────────┐
│  useens / linlin-backup      ⭐ Star    ⚙️ Settings      │
│─────────────────────────────────────────────────────────│
│  Code  Issues  Pull requests  Actions  Projects  Wiki   │
│                                                         │
│  ⚠️ 你的默认分支已过时                                     │
│                                                         │
│  📁 文件列表...                                          │
│                                                         │
│  [页面左侧菜单]                                           │
│  ├─ General ← 点击这里                                    │
│  ├─ Access                                               │
│  ├─ Code and automation                                  │
│  └─ ...                                                  │
│                                                         │
│  [General 页面内容]                                       │
│  ├─ Repository name                                      │
│  ├─ Default branch  ← 找到这里！                          │
│  │   ┌───────────────────────────────────────┐          │
│  │   │ master  [🔃]                          │          │
│  │   └───────────────────────────────────────┘          │
│  │   点击 🔃 切换为 main                                │
│  └─ ...                                                  │
└─────────────────────────────────────────────────────────┘
```

### 切换后

切换完成后告诉我，我会删除远程的 master 分支。
