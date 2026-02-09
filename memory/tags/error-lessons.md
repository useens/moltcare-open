# Error Lessons 错误教训记录

## 2026-02-08

### 教训 #1: Memory Search 配置缺失
**错误**: memory_search 工具需要 API key 但未配置  
**影响**: 无法执行语义搜索，只能依赖文件系统读取  
**解决**: 使用 exec + grep 或直接文件读取作为替代  
**预防**: 考虑安装本地向量存储 skill 或配置 API

### 教训 #2: Web Search API 未配置
**错误**: ddgr search API key 缺失  
**影响**: 无法执行网络搜索，信息获取受限  
**解决**: 使用 curl 直接访问已知 URL，或使用 gh API  
**预防**: 配置 DDGR_SEARCH 或安装替代搜索 skill

### 教训 #3: awesome-openclaw-skills 仓库访问失败
**错误**: 404 Not Found - 仓库可能不存在或权限不足  
**影响**: 无法批量获取官方技能列表  
**解决**: 使用 clawhub search 作为替代  
**预防**: 确认官方仓库地址，或通过 clawhub 获取技能信息

### 教训 #4: 记忆文件不同步
**错误**: skills-installed.md 显示 4 个技能，实际有 22 个  
**影响**: 决策基于过时信息  
**解决**: 定期同步实际安装状态到记忆文件  
**预防**: 进化循环中增加"记忆文件同步"步骤

---

*记录原则：每个错误只记录一次，但需链接到具体场景*
