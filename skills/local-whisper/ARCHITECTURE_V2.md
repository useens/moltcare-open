# Local-Whisper 语音转录技能 - 架构优化方案

> 状态: 草案  
> 版本: v2.0  
> 日期: 2025-02-09

---

## 1. 当前状态分析

### 1.1 现状
| 指标 | 当前值 |
|------|--------|
| 模型 | base (74MB) |
| 转录速度 | 10:1 (比实时快10倍) |
| 加载时间 | ~2-3秒 (每次调用) |
| 并发支持 | 无 (单进程阻塞) |
| 缓存策略 | 无 |

### 1.2 瓶颈识别
1. **模型重复加载**: 每次调用都重新加载模型，耗时 2-3秒
2. **无状态设计**: 无法复用已加载模型
3. **阻塞式处理**: 单线程，无法并发处理多个请求
4. **固定模型**: 无法根据场景自动选择模型

---

## 2. 优化方案总览

### 2.1 目标架构

```
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway                            │
│                   (FastAPI + Uvicorn)                       │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   模型管理器  │    │   任务队列   │    │   缓存层     │
│ ModelManager │    │ TaskQueue    │    │  LRU Cache   │
└──────────────┘    └──────────────┘    └──────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Whisper 模型池                           │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐         │
│  │  tiny   │  │  base   │  │  small  │  │  turbo  │         │
│  │ (39MB)  │  │ (74MB)  │  │ (244MB) │  │ (809MB) │         │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘         │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 核心优化点

| 优化项 | 当前 | 优化后 | 预期收益 |
|--------|------|--------|----------|
| 模型加载 | 每次调用 | 常驻内存 | 节省 2-3s/请求 |
| 并发处理 | 单线程 | 多worker | 支持 4-8 并发 |
| 缓存策略 | 无 | LRU + 预热 | 命中率 >80% |
| 模型选择 | 固定 | 自适应 | 按需选择最优模型 |

---

## 3. 详细设计方案

### 3.1 模型缓存策略 (Model Pool)

#### 3.1.1 LRU 缓存实现
```python
class ModelPool:
    """Whisper 模型池 - 多模型LRU缓存"""
    
    def __init__(self, max_models: int = 2, device: str = "cpu"):
        self.max_models = max_models
        self.device = device
        self._cache: OrderedDict[str, whisper.Whisper] = OrderedDict()
        self._lock = asyncio.Lock()
    
    async def get(self, model_name: str) -> whisper.Whisper:
        """获取模型，自动加载和缓存"""
        async with self._lock:
            if model_name in self._cache:
                # 移到最近使用
                self._cache.move_to_end(model_name)
                return self._cache[model_name]
            
            # 清理最久未使用的
            while len(self._cache) >= self.max_models:
                old_model, _ = self._cache.popitem(last=False)
                logger.info(f"Evicted model: {old_model}")
            
            # 加载新模型
            model = await asyncio.to_thread(whisper.load_model, model_name)
            self._cache[model_name] = model
            return model
```

#### 3.1.2 预热策略
- **启动时预热**: 默认加载 base 模型
- **延迟预热**: 根据历史使用记录预加载高频模型
- **智能切换**: 检测到模型切换趋势时提前加载

### 3.2 异步架构设计

#### 3.2.1 FastAPI 服务架构
```python
from fastapi import FastAPI, File, UploadFile, BackgroundTasks
import asyncio
from concurrent.futures import ProcessPoolExecutor

app = FastAPI()
model_pool = ModelPool(max_models=2)
executor = ProcessPoolExecutor(max_workers=4)

@app.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    model: str = "base",
    language: Optional[str] = None,
    timestamps: bool = False
):
    """异步转录接口"""
    # 1. 保存上传文件
    temp_path = await save_upload(file)
    
    # 2. 获取模型 (从缓存或加载)
    whisper_model = await model_pool.get(model)
    
    # 3. 在进程池中执行转录 (CPU密集型)
    result = await asyncio.get_event_loop().run_in_executor(
        executor,
        lambda: whisper_model.transcribe(temp_path, language=language)
    )
    
    # 4. 清理临时文件
    await cleanup_async(temp_path)
    
    return {"text": result["text"], "language": result.get("language")}
```

#### 3.2.2 任务队列 (可选增强)
对于大量转录任务，引入任务队列:

```python
from asyncio import Queue

class TranscriptionQueue:
    """批量转录任务队列"""
    
    def __init__(self, max_workers: int = 4):
        self.queue = Queue(maxsize=100)
        self.max_workers = max_workers
        self.results = {}
    
    async def submit(self, task_id: str, audio_path: str, **options) -> str:
        """提交任务，返回 task_id"""
        await self.queue.put({"id": task_id, "path": audio_path, "options": options})
        return task_id
    
    async def worker(self):
        """工作协程"""
        while True:
            task = await self.queue.get()
            try:
                result = await self.process(task)
                self.results[task["id"]] = {"status": "completed", "result": result}
            except Exception as e:
                self.results[task["id"]] = {"status": "failed", "error": str(e)}
            finally:
                self.queue.task_done()
```

### 3.3 自适应模型选择

根据音频特征自动选择最优模型:

```python
class AdaptiveModelSelector:
    """自适应模型选择器"""
    
    # 模型特性矩阵
    MODEL_PROFILES = {
        "tiny": {
            "size_mb": 39,
            "speed_factor": 32,  # 比实时快32倍
            "wer_en": 18.6,      # 词错误率
            "memory_mb": 200,
            "best_for": ["short", "clear", "realtime"]
        },
        "base": {
            "size_mb": 74,
            "speed_factor": 16,
            "wer_en": 14.6,
            "memory_mb": 350,
            "best_for": ["general", "mixed_quality"]
        },
        "small": {
            "size_mb": 244,
            "speed_factor": 6,
            "wer_en": 10.3,
            "memory_mb": 1000,
            "best_for": ["long_form", "noisy", "important"]
        },
        "turbo": {
            "size_mb": 809,
            "speed_factor": 8,
            "wer_en": 6.7,
            "memory_mb": 2500,
            "best_for": ["high_quality", "multilingual"]
        }
    }
    
    def select(self, audio_info: AudioInfo, requirements: Requirements) -> str:
        """
        根据音频信息和需求选择模型
        
        决策逻辑:
        1. 音频长度 < 10s + 实时性要求 → tiny
        2. 音频长度 10s-2min + 一般质量 → base
        3. 音频长度 > 2min + 重要内容 → small
        4. 多语言/高质量要求 → turbo
        """
        duration = audio_info.duration
        
        if requirements.realtime and duration < 10:
            return "tiny"
        elif duration < 120 and not requirements.high_quality:
            return "base" 
        elif requirements.high_quality or audio_info.has_multiple_speakers:
            return "turbo"
        else:
            return "small"
```

---

## 4. 模型对比评估

### 4.1 性能基准测试

| 模型 | 大小 | 加载时间 | 转录速度 | WER (en) | 内存占用 | 推荐场景 |
|------|------|----------|----------|----------|----------|----------|
| tiny | 39MB | ~1s | 32x | 18.6% | ~200MB | 实时草稿、快速预览 |
| base | 74MB | ~2s | 16x | 14.6% | ~350MB | 通用场景、平衡选择 |
| small | 244MB | ~4s | 6x | 10.3% | ~1GB | 长音频、重要内容 |
| turbo | 809MB | ~8s | 8x | 6.7% | ~2.5GB | 高质量、多语言 |

### 4.2 模型选择建议

#### 场景匹配矩阵

| 使用场景 | 推荐模型 | 理由 |
|----------|----------|------|
| 语音助手/实时交互 | tiny | 最低延迟，可接受一定错误率 |
| 会议记录/笔记 | base | 速度与质量平衡 |
| 播客/访谈转录 | small | 长音频处理更好 |
| 法律/医疗记录 | turbo | 最高准确度要求 |
| 多语言内容 | turbo | 多语言支持最佳 |

### 4.3 内存与并发权衡

假设系统内存 4GB:

```
模型配置方案:
┌────────────────────────────────────────────────┐
│ 方案A: 单大模型                                 │
│   - 常驻 turbo (2.5GB)                         │
│   - 并发: 1, 平均延迟: 中等                     │
│   - 适合: 高质量要求场景                        │
├────────────────────────────────────────────────┤
│ 方案B: 双模型缓存                               │
│   - 常驻 base (350MB) + 按需 small (1GB)       │
│   - 并发: 2-3, 平均延迟: 低                     │
│   - 适合: 通用场景 (推荐)                       │
├────────────────────────────────────────────────┤
│ 方案C: 轻量级                                   │
│   - 常驻 tiny (200MB) + 按需 base (350MB)      │
│   - 并发: 4+, 平均延迟: 极低                    │
│   - 适合: 高并发、可接受草稿质量                │
└────────────────────────────────────────────────┘
```

**推荐**: 方案B (base + small) 作为默认配置

---

## 5. 实现路线图

### Phase 1: 基础优化 (1-2周)

```
□ 实现 ModelPool LRU缓存
  ├─ 多模型管理
  ├─ 自动加载/卸载
  └─ 内存上限控制

□ 创建 FastAPI 服务封装
  ├─ /transcribe 端点
  ├─ /health 健康检查
  └─ /models 模型列表

□ 添加基础配置
  └─ 环境变量支持 (MODEL_CACHE_SIZE, MAX_WORKERS)
```

### Phase 2: 并发与队列 (2-3周)

```
□ 进程池集成
  ├─ ProcessPoolExecutor
  ├─ 可配置worker数量
  └─ 优雅关闭

□ 任务队列 (可选)
  ├─ 异步任务提交
  ├─ 进度查询接口
  └─ 结果回调机制

□ 批量处理支持
  └─ 多文件并行转录
```

### Phase 3: 智能化 (3-4周)

```
□ 自适应模型选择
  ├─ 音频特征分析
  ├─ 模型推荐算法
  └─ 用户偏好学习

□ 性能监控
  ├─ 转录耗时统计
  ├─ 模型命中率
  └─ 内存使用监控

□ 优化预热策略
  ├─ 启动预热
  ├─ 预测性加载
  └─ 闲时缓存维护
```

### Phase 4: 生产就绪 (2周)

```
□ 完整测试覆盖
  ├─ 单元测试
  ├─ 集成测试
  └─ 压力测试

□ 文档完善
  ├─ API文档
  ├─ 部署指南
  └─ 性能调优手册

□ 容器化支持
  └─ Dockerfile + docker-compose
```

---

## 6. 技术实现细节

### 6.1 目录结构

```
skills/local-whisper-v2/
├── SKILL.md
├── _meta.json
├── requirements.txt          # 依赖清单
├── docker-compose.yml        # 可选容器部署
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI入口
│   ├── config.py            # 配置管理
│   ├── models/
│   │   ├── __init__.py
│   │   ├── pool.py          # 模型池实现
│   │   └── selector.py      # 模型选择器
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py        # API路由
│   │   └── schemas.py       # Pydantic模型
│   ├── core/
│   │   ├── __init__.py
│   │   ├── transcriber.py   # 转录核心
│   │   └── queue.py         # 任务队列
│   └── utils/
│       ├── __init__.py
│       ├── audio.py         # 音频处理
│       └── cache.py         # 缓存工具
├── scripts/
│   ├── server.py            # 服务启动脚本
│   ├── client.py            # CLI客户端
│   └── transcribe.py        # 原脚本(兼容)
└── tests/
    ├── test_pool.py
    ├── test_api.py
    └── benchmark.py
```

### 6.2 配置文件示例

```yaml
# config.yaml
whisper:
  default_model: base
  cache_size: 2              # 同时缓存的模型数
  device: cpu                # cpu / cuda
  compute_type: int8         # 量化类型

server:
  host: 127.0.0.1
  port: 8000
  workers: 4
  max_file_size: 100MB
  timeout: 300

performance:
  enable_batch: true
  batch_size: 4
  adaptive_model: true
  preload_models:
    - base

monitoring:
  enabled: true
  prometheus_port: 9090
```

### 6.3 启动方式

```bash
# 方式1: 开发模式
uvicorn src.main:app --reload --port 8000

# 方式2: 生产模式 (多worker)
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4

# 方式3: 使用脚本
python scripts/server.py --config config.yaml

# 方式4: Docker
docker-compose up -d
```

---

## 7. 性能预期

### 7.1 优化前后对比

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 首请求延迟 | 2-3s | <100ms | 20-30x |
| 并发处理能力 | 1 | 4-8 | 4-8x |
| 吞吐量 (req/min) | ~20 | ~120 | 6x |
| 内存占用 (稳定) | 350MB | 500MB-1.5GB | 可控 |
| 模型切换时间 | 2-3s | <50ms (热缓存) | 40-60x |

### 7.2 压力测试目标

```bash
# 使用 wrk 或 locust 测试
# 目标: 100并发, 1000请求

# 预期结果:
- 成功率: >99.5%
- P99延迟: <5s
- 平均延迟: <1s (缓存命中)
- 内存稳定: 无泄漏
```

---

## 8. 风险评估

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| 内存泄漏 | 中 | 高 | 定期健康检查，设置内存上限 |
| 模型加载失败 | 低 | 高 | 重试机制，降级到更小模型 |
| 并发瓶颈 | 中 | 中 | 可配置worker数，监控告警 |
| 大文件OOM | 中 | 高 | 文件大小限制，流式处理 |
| 磁盘空间不足 | 低 | 中 | 临时文件自动清理 |

---

## 9. 结论与建议

### 9.1 核心建议

1. **立即实施**: Phase 1 的 ModelPool 缓存
   - 收益最大，实现相对简单
   - 可将首请求延迟从 2-3s 降至 <100ms

2. **推荐配置**:
   - 默认模型: base (74MB)
   - 缓存策略: LRU, 最多 2 个模型
   - Worker数: 4 (根据 CPU 核心调整)

3. **是否使用 tiny 模型**:
   - 适合场景: 实时交互、草稿转录
   - 不建议: 作为默认模型 (准确度下降明显)
   - 建议: 作为可选配置，让用户按需选择

### 9.2 决策矩阵

```
是否需要 tiny 模型?
├─ 是, 如果:
│   ├─ 实时性要求极高 (<200ms 延迟)
│   ├─ 可接受 20-30% 错误率
│   └─ 仅用于草稿/预览场景
│
└─ 否, 保持 base 作为默认:
    ├─ 准确度更重要
    ├─ 内存不是主要限制
    └─ 延迟 500ms-1s 可接受
```

### 9.3 下一步行动

1. [ ] 评审此架构文档
2. [ ] 创建 v2 分支
3. [ ] 实现 ModelPool 核心类
4. [ ] 搭建 FastAPI 基础框架
5. [ ] 性能基准测试
6. [ ] 逐步迁移并验证

---

## 附录

### A. 参考资源

- [Whisper 官方文档](https://github.com/openai/whisper)
- [FastAPI 性能优化](https://fastapi.tiangolo.com/advanced/performance/)
- [faster-whisper (CTranslate2)](https://github.com/SYSTRAN/faster-whisper) - 更快的推理

### B. 模型下载地址

```bash
# 预下载模型到缓存目录
~/.cache/whisper/
├── tiny.pt
├── base.pt
├── small.pt
└── turbo.pt
```

### C. 测试音频样本

```bash
# 生成测试音频
ffmpeg -f lavfi -i "sine=frequency=1000:duration=5" -ar 16000 test_5s.wav
ffmpeg -f lavfi -i "sine=frequency=1000:duration=60" -ar 16000 test_60s.wav
```
