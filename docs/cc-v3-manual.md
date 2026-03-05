# 🤖 Command Center v3.0 - 使用手册

## 角色定位

### 我 = 指挥中心 (Command Center)
- 🎯 任务分析与路由决策
- 📊 监控10个小弟状态  
- 🔒 安全策略制定与审计
- 📡 结果汇总与飞书通知

### 10个小弟 = 执行节点 (Worker Nodes)
每个小弟可以独立：
- ✅ 安装安全的skill
- ✅ 使用工具完成任务
- ✅ 独立决策执行路径
- ✅ 报告进度和结果

## 10个小弟分工

| 节点 | 模型 | 角色 | 主要职责 |
|------|------|------|----------|
| **NB01** | Step | fast_executor | 快速执行简单任务 |
| **NB02** | Step | data_collector | 数据收集、网络爬虫 |
| **NB03** | Step | content_generator | 内容生成、模板填充 |
| **NB04** | Step | api_caller | API调用、外部集成 |
| **NB05** | Step | monitor | 监控检查、状态报告 |
| **NB06** | DeepSeek | deep_analyzer | 深度分析、问题诊断 |
| **NB07** | DeepSeek | code_reviewer | 代码审查、Bug检测 |
| **NB08** | DeepSeek | complex_solver | 复杂问题求解 |
| **NB09** | DeepSeek | strategy_planner | 策略规划、架构设计 |
| **NB10** | DeepSeek | quality_assurance | 质量保证、测试验证 |

## 快速命令

### 1. 查看小弟状态
```bash
# 列出所有小弟
./scripts/cc-node list

# 查看特定小弟详情
./scripts/cc-node status NB01
```

### 2. 命令小弟安装skill
```bash
# 查看允许安装的skill
./scripts/cc-node skills

# 命令NB01安装web_search
./scripts/cc-node install NB01 web_search

# 命令NB02安装agent_reach
./scripts/cc-node install NB02 agent_reach

# 查看NB01已安装的skill
./scripts/cc-node skills --node NB01
```

### 3. 分配任务给小弟
```bash
# 自动选择小弟执行任务
./scripts/cc-task "搜索最新的AI论文"

# 指定NB02执行任务
./scripts/cc-task "收集这10个网站的数据" --to NB02

# 广播到所有10个小弟
./scripts/cc-task "检查所有服务健康状态" --broadcast

# 并行分发给3个小弟
./scripts/cc-task "分析这段代码是否有bug" --parallel --count 3
```

## 允许安装的skill

| Skill | 描述 | 风险 |
|-------|------|------|
| web_search | 网络搜索 | 🟢 低 |
| web_fetch | 网页获取 | 🟢 低 |
| github | GitHub操作 | 🟢 低 |
| agent_reach | 多平台网络访问 | 🟡 中 |
| browser | 浏览器自动化 | 🟡 中 |
| docker_essentials | Docker基础 | 🟡 中 |
| summarize | 内容摘要 | 🟢 低 |
| video_frames | 视频帧提取 | 🟢 低 |
| fd_find | 文件查找 | 🟢 低 |
| bat_cat | 增强cat | 🟢 低 |

## 工作流程示例

### 场景1: 让小弟搜索资料
```bash
# 1. 确保小弟已安装skill
./scripts/cc-node install NB02 web_search
./scripts/cc-node install NB02 agent_reach

# 2. 分配搜索任务
./scripts/cc-task "搜索2025年最新的LLM论文，找到5篇重要的" --to NB02

# 3. 等待小弟完成 (实际执行需要启动执行环境)
```

### 场景2: 让小弟收集数据
```bash
# 1. 为多个小弟安装skill
./scripts/cc-node install NB01 web_search
./scripts/cc-node install NB02 web_search
./scripts/cc-node install NB03 web_search

# 2. 并行分发不同任务
./scripts/cc-task "收集A公司的财报数据" --to NB01
./scripts/cc-task "收集B公司的财报数据" --to NB02
./scripts/cc-task "收集C公司的财报数据" --to NB03

# 3. 等小弟完成后，我汇总分析
./scripts/cc-task "分析这三家公司的财务对比" --self
```

### 场景3: 让小弟监控服务
```bash
# 1. 安装监控相关skill
./scripts/cc-node install NB05 docker_essentials

# 2. 分配监控任务
./scripts/cc-task "检查所有Docker容器状态" --to NB05

# 3. 设置定时监控 (需要配置cron)
```

### 场景4: 让小弟生成内容
```bash
# 1. 为内容生成节点安装skill
./scripts/cc-node install NB03 summarize

# 2. 分配内容生成任务
./scripts/cc-task "生成一份周报模板" --to NB03
```

## 安全边界

### 我可以做的
- ✅ 分析任务并分配给小弟
- ✅ 审计小弟安装的skill
- ✅ 监控小弟执行状态
- ✅ 制定安全策略
- ✅ 汇总结果上报

### 小弟可以做的
- ✅ 安装白名单中的skill
- ✅ 使用允许的工具
- ✅ 在自己的工作目录读写
- ✅ 访问外部网络
- ✅ 自主决策执行路径

### 禁止做的
- ❌ 小弟不能安装白名单外的skill
- ❌ 小弟不能访问其他小弟的目录
- ❌ 小弟不能执行rm -rf等危险命令
- ❌ 我不能直接执行工具(必须通过小弟)

## 目录结构

```
workspace/
├── nanobots/
│   ├── nb01/              # NB01工作目录
│   │   ├── skills/        # 安装的skill
│   │   ├── workspace/     # 工作文件
│   │   ├── data/          # 数据文件
│   │   ├── logs/          # 执行日志
│   │   ├── tmp/           # 临时文件
│   │   └── config/        # 配置文件
│   │       ├── identity.json    # 身份信息
│   │       └── security.json    # 安全策略
│   ├── nb02/              # NB02工作目录
│   ├── ...
│   └── nb10/              # NB10工作目录
├── config/
│   └── allowed_skills.json    # 允许安装的skill清单
├── scripts/
│   ├── cc-node            # 节点管理器
│   ├── cc-task            # 任务指挥官
│   └── cc-delegate        # 智能委托(旧版)
└── data/
    ├── task_queue.db      # 任务队列数据
    └── node_profiles.db   # 节点画像数据
```

## 进阶使用

### 批量安装skill
```bash
# 为所有Step组安装web_search
for node in NB01 NB02 NB03 NB04 NB05; do
    ./scripts/cc-node install $node web_search
done

# 为所有DeepSeek组安装github
for node in NB06 NB07 NB08 NB09 NB10; do
    ./scripts/cc-node install $node github
done
```

### 监控小弟执行
```bash
# 查看所有小弟的执行日志
for node in NB{01..10}; do
    echo "=== $node ==="
    tail -5 nanobots/${node,,}/logs/task_execution.log
done
```

### 查看小弟工作成果
```bash
# 查看NB02收集的数据
ls -la nanobots/nb02/workspace/

# 查看NB03生成的内容
cat nanobots/nb03/workspace/*.txt
```

## 故障排除

### 小弟不在线
```bash
# 检查节点状态
./scripts/cc-p0.sh status

# 重启节点
./scripts/nb-cluster.sh restart
```

### skill安装失败
```bash
# 检查是否在白名单中
./scripts/cc-node skills

# 查看审计日志
cat nanobots/nb01/logs/skill_audit.log
```

### 任务执行失败
```bash
# 查看任务日志
cat nanobots/nb01/logs/task_execution.log

# 查看任务脚本
ls nanobots/nb01/tmp/
```

## 下一步计划

### Phase 2: 小弟独立执行环境
- [ ] 启动小弟的执行进程
- [ ] 实现真正的skill加载
- [ ] 实现工具调用隔离

### Phase 3: 智能编排
- [ ] 自动任务分解
- [ ] 动态流水线
- [ ] 结果自动汇总

### Phase 4: 学习进化
- [ ] 小弟能力学习
- [ ] 任务匹配优化
- [ ] 性能持续改进

---

**版本**: v3.0 (角色重定义)
**更新时间**: 2026-03-06
**10个小弟状态**: ✅ 环境就绪，等待执行环境启动
