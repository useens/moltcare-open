# Self-Diagnosis System v5.0
# 自我诊断系统 v5.0

## 系统概述

这是一个全面的自我诊断系统，包含以下核心模块：

### 1. 推理质量深度分析 (advanced_diagnosis.py)
- **幻觉检测**: 检测AI回答中的虚构信息、无来源数字、不可验证声明
- **逻辑一致性检测**: 验证推理逻辑链条、条件语句一致性、因果关系合理性
- **意图理解检测**: 分析是否误解用户意图、回应适当性
- **质量评分报告**: 生成综合质量评估报告

### 2. 预测性故障检测 (predictive_monitor.py)
- **磁盘空间预测**: 基于趋势预测磁盘满的时间点
- **内存压力预测**: 检测内存泄漏、预测OOM风险
- **GitHub同步延迟**: 预测同步延迟问题
- **API限流风险**: 预测API配额耗尽时间

### 3. 智能降级策略 (smart_degrade.py)
- **质量降级**: 推理质量下降时自动切换到简化模式
- **资源降级**: 资源紧张时关闭非核心功能
- **离线模式**: 网络中断时启用离线模式
- **自动恢复**: 条件满足时自动恢复正常模式

### 4. 自优化建议 (self_optimization.py)
- **日志分析**: 分析日志找出优化点
- **配置优化**: 检查并建议配置改进
- **性能分析**: 识别性能瓶颈
- **自动执行**: 低风险优化自动执行

### 5. 集成服务 (diagnosis_integration.py / diagnosis_service.py)
- 统一协调所有模块
- 提供HTTP API接口
- 生成综合诊断报告

## 快速开始

### 启动服务

```bash
# 使用控制脚本
./scripts/diagnosis_control.sh start

# 或直接启动
python3 scripts/diagnosis_service.py --start

# 启动并启用HTTP API
python3 scripts/diagnosis_service.py --start --http
```

### 检查状态

```bash
./scripts/diagnosis_control.sh status
```

### 生成报告

```bash
./scripts/diagnosis_control.sh report
```

### 运行健康检查

```bash
./scripts/diagnosis_control.sh check
```

## 模块使用

### 1. 分析交互质量

```python
from scripts.diagnosis_integration import analyze_response

result = await analyze_response(
    session_id="session-001",
    user_query="请解释Python的GIL",
    ai_response="Python的GIL是..."
)

print(f"整体评分: {result['quality_scores']['overall']}")
print(f"发现{result['issues_found']}个问题")
print(f"建议: {result['suggestions']}")
```

### 2. 检查系统健康

```python
from scripts.diagnosis_integration import check_system_health

health = await check_system_health()
print(json.dumps(health, indent=2))
```

### 3. 检查功能可用性

```python
from scripts.diagnosis_integration import is_feature_available

if is_feature_available('web_search'):
    # 执行搜索
    pass
```

### 4. 获取降级规则

```python
from scripts.diagnosis_integration import get_degrade_rules

rules = get_degrade_rules()
max_length = rules.get('max_response_length', 5000)
```

## HTTP API

启动HTTP服务后，可使用以下API：

### 获取状态
```bash
curl http://localhost:8765/status
```

### 获取健康仪表盘
```bash
curl http://localhost:8765/health
```

### 分析交互
```bash
curl -X POST http://localhost:8765/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-001",
    "query": "请解释Python的GIL",
    "response": "Python的GIL是..."
  }'
```

### 获取报告
```bash
curl http://localhost:8765/report?format=markdown
```

## 配置文件

### 智能降级配置

在 `smart_degrade.py` 中可配置：

```python
# 阈值配置
self.thresholds = {
    'memory': {'light': 70, 'medium': 80, 'severe': 90},
    'cpu': {'light': 75, 'medium': 85, 'severe': 95},
    'disk': {'light': 80, 'medium': 90, 'severe': 95}
}
```

### 功能注册

```python
# 注册功能
smart_degrade.register_feature(
    name='my_feature',
    category='enhancement',  # core, enhancement, optional, experimental
    priority=5,  # 1-10, 越低越核心
    degrade_level=DegradeLevel.MEDIUM,  # 在此级别被禁用
    handler=feature_handler  # 启用/禁用回调
)
```

## 日志和监控

### 日志文件
- `/root/.openclaw/workspace/logs/advanced_diagnosis.log` - 质量分析日志
- `/root/.openclaw/workspace/logs/predictive_monitor.log` - 预测监控日志
- `/root/.openclaw/workspace/logs/smart_degrade.log` - 降级策略日志
- `/root/.openclaw/workspace/logs/self_optimization.log` - 自优化日志
- `/root/.openclaw/workspace/logs/diagnosis_service.log` - 服务日志

### 数据存储
- `/root/.openclaw/workspace/data/diagnosis/` - 诊断数据存储

## 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    Diagnosis Service                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ Quality Analysis │  │ Predictive       │                │
│  │ (Hallucination,  │  │ Monitoring       │                │
│  │  Logic, Intent)  │  │ (Disk, Memory,   │                │
│  │                  │  │  API, Network)   │                │
│  └────────┬─────────┘  └────────┬─────────┘                │
│           │                     │                           │
│           └──────────┬──────────┘                           │
│                      │                                      │
│           ┌──────────▼──────────┐                          │
│           │  Smart Degrade      │                          │
│           │  (Auto downgrade/   │                          │
│           │   recovery)         │                          │
│           └──────────┬──────────┘                          │
│                      │                                      │
│           ┌──────────▼──────────┐                          │
│           │  Self Optimization  │                          │
│           │  (Log analysis,     │                          │
│           │   Auto execution)   │                          │
│           └─────────────────────┘                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 注意事项

1. **首次运行**: 系统需要收集一段时间的数据才能进行准确预测
2. **资源消耗**: 质量分析模块对长文本可能消耗较多计算资源
3. **自动执行**: 只有标记为 `auto_executable` 且风险等级为 `low` 的优化才会自动执行
4. **降级策略**: 核心功能永远不会被禁用，确保系统基本运行

## 版本历史

### v5.0 (2026-02-11)
- 初始发布
- 集成四大诊断模块
- 实现智能降级策略
- 添加预测性监控
- 支持自动优化
