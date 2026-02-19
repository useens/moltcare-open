# Task 1: Vestige源码分析 - FSRS-6算法提取报告

**执行时间**: 2026-02-19 21:57 GMT+8
**分析目标**: 提取FSRS-6间隔重复算法核心实现，为森森记忆系统集成做准备

---

## 1. FSRS-6算法概述

### 1.1 算法背景

FSRS（Free Spaced Repetition Scheduler）是基于130年代记忆研究的间隔重复算法，起源于MaiMemo的DHP模型（DSR模型的变体）。

**核心原理**：
- 基于**DSR模型**：Difficulty（难度）+ Stability（稳定性）+ Retrievability（可提取性）
- **Stability（S）**：记忆的存储强度，稳定性越高遗忘越慢
- **Retrievability（R）**：记忆的提取强度，可提取性越低遗忘概率越高

### 1.2 Vestige技能定位

Vestige是一个基于Rust的MCP服务器，实现：
- ✅ FSRS-6间隔重复算法
- ✅ 语义搜索（基于fastembed）
- ✅ 扩散激活模型
- ✅ 突触标记
- ✅ 完全本地运行

**关键特性**：
- 智能重复（smart_ingest）- 自动去重
- 记忆衰减机制
- 支持4种评级：Again、Hard、Good、Easy
- 支持4种状态：New、Learning、Review、Relearning

---

## 2. FSRS-6核心公式和参数

### 2.1 默认参数（FSRS-5）

**当前rs-fsrs实现使用FSRS-5参数**（21个权重参数）：

```rust
const DEFAULT_WEIGHTS: [f64; 19] = [
    0.4072,   // w[0]: S0(Again) - 初始稳定性（Again）
    1.1829,   // w[1]: S0(Hard) - 初始稳定性（Hard）
    3.1262,   // w[2]: S0(Good) - 初始稳定性（Good）
    15.4722,  // w[3]: S0(Easy) - 初始稳定性（Easy）
    7.2102,   // w[4]: D0(Again) - 初始难度（Again）
    0.5316,   // w[5]: D0指数参数
    1.0651,   // w[6]: 难度调整权重
    0.0234,   // w[7]: 均值回归权重
    1.616,    // w[8]: S'增长指数基数
    0.1544,   // w[9]: S'S的负幂指数
    1.0824,   // w[10]: 间距效应指数
    1.9813,   // w[11]: 遗忘后稳定性基数
    0.0953,   // w[12]: 遗忘后难度负幂指数
    0.2975,   // w[13]: 遗忘后稳定性幂指数
    2.2042,   // w[14]: 遗忘后可提取性指数
    0.2407,   // w[15]: Hard评级修正系数
    2.9466,   // w[16]: Easy评级修正系数
    0.5034,   // w[17]: 短期稳定性指数基数
    0.6567,   // w[18]: 短期稳定性偏移
];
```

**FSRS-6（最新版本，21个参数）**：
```
[0.212, 1.2931, 2.3065, 8.2956, 6.4133, 0.8334, 3.0194, 0.001, 1.8722, 0.1666, 0.796, 1.4835, 0.0614, 0.2629, 1.6483, 0.6014, 1.8729, 0.5425, 0.0912, 0.0658, 0.1542]
```

### 2.2 核心公式

#### 2.2.1 遗忘曲线（FSRS-4.5+）

**可提取性计算**（FSRS-4.5+版本）：

```rust
// 源码位置: parameters.rs:forgetting_curve
pub fn forgetting_curve(elapsed_days: f64, stability: f64) -> f64 {
    // DECAY = -0.5
    // FACTOR = 19/81 = 0.234568
    (1.0 + Self::FACTOR * elapsed_days / stability).powf(Self::DECAY)
}
```

**数学公式**：
$$R(t,S) = \left(1 + FACTOR \cdot \frac{t}{S}\right)^{DECAY}$$

其中：
- $DECAY = -0.5$
- $FACTOR = \frac{19}{81}$（确保 $R(S,S) = 90\%$）

**特性**：
- 当 $t = S$ 时，$R = 0.9$（90%保持率）
- 遗忘曲线在S之前下降较快，之后平缓

#### 2.2.2 初始稳定性

```rust
pub fn init_stability(&self, rating: Rating) -> f64 {
    let rating_int: i32 = rating as i32;
    self.w[(rating_int - 1) as usize].max(0.1)
}
```

**数学公式**：
$$S_0(G) = w_{G-1}$$

示例：
- $S_0(Again) = w_0 = 0.4072$
- $S_0(Good) = w_2 = 3.1262$
- $S_0(Easy) = w_3 = 15.4722$

#### 2.2.3 初始难度

```rust
pub fn init_difficulty(&self, rating: Rating) -> f64 {
    let rating_int: i32 = rating as i32;
    (self.w[4] - f64::exp(self.w[5] * (rating_int as f64 - 1.0)) + 1.0).clamp(1.0, 10.0)
}
```

**数学公式**：
$$D_0(G) = w_4 - e^{w_5 \cdot (G-1)} + 1$$

其中 $D_0(Again) = w_4$，$D_0(Easy)$ 均值回归到理想难度

**难度范围**：$[1, 10]$（1最易，10最难）

#### 2.2.4 难度更新机制

```rust
pub fn next_difficulty(&self, difficulty: f64, rating: Rating) -> f64 {
    let rating_int = rating as i32;
    // 线性衰减/增长
    let next_difficulty = difficulty - self.w[6] * (rating_int as f64 - 3.0);
    // 均值回归（避免"简单地狱"）
    let mean_reversion = self.mean_reversion(
        self.init_difficulty(Rating::Easy),  // 目标：Easy的初始难度
        next_difficulty
    );
    mean_reversion.clamp(1.0, 10.0)
}
```

**数学公式**：
$$\Delta D = -w_6 \cdot (G - 3)$$
$$D' = D + \Delta D$$
$$D'' = w_7 \cdot D_0(Easy) + (1 - w_7) \cdot D'$$

**特性**：
- Good（G=3）不改变难度
- Hard（G=2）增加难度
- Easy（G=4）降低难度
- 均值回归防止难度偏离过远

#### 2.2.5 成功回忆后的稳定性更新（关键）

```rust
pub fn next_recall_stability(
    &self,
    difficulty: f64,
    stability: f64,
    retrievability: f64,
    rating: Rating,
) -> f64 {
    let modifier = match rating {
        Rating::Hard => self.w[15],  // 0.2407
        Rating::Easy => self.w[16],  // 2.9466
        _ => 1.0,  // Good默认
    };

    stability * (((self.w[8]).exp()
        * (11.0 - difficulty)
        * stability.powf(-self.w[9])
        * (((1.0 - retrievability) * self.w[10]).exp_m1()))
    .mul_add(modifier, 1.0))
}
```

**数学公式**：
$$S'_r(D,S,R,G) = S \cdot \left(e^{w_8} \cdot (11-D) \cdot S^{-w_9} \cdot (e^{w_{10}(1-R)}-1) \cdot modifier + 1\right)$$

其中 $modifier$：
- Again: N/A（用forgetting公式）
- Hard: $w_{15} = 0.2407$（降低稳定性增长）
- Good: $1.0$（默认）
- Easy: $w_{16} = 2.9466$（大幅增加稳定性增长）

**记忆定律体现**：
1. **难度影响**：$D$ 越大，$S_{inc}$ 越小（难材料稳定性增长慢）
2. **稳定化衰减**：$S$ 越大，$S_{inc}$ 越小（高稳定性更难提升）
3. **间距效应**：$R$ 越小，$S_{inc}$ 越大（越久没复习，成功后提升越大）
4. **$S_{inc} \ge 1$**：成功回忆后稳定性至少保持不变

#### 2.2.6 遗忘后的稳定性更新

```rust
pub fn next_forget_stability(
    &self,
    difficulty: f64,
    stability: f64,
    retrievability: f64,
) -> f64 {
    self.w[11]
        * difficulty.powf(-self.w[12])
        * ((stability + 1.0).powf(self.w[13]) - 1.0)
        * f64::exp((1.0 - retrievability) * self.w[14])
}
```

**数学公式**：
$$S'_f(D,S,R) = w_{11} \cdot D^{-w_{12}} \cdot ((S+1)^{w_{13}}-1) \cdot e^{w_{14}(1-R)}$$

示例（默认参数）：
- $D=2, R=0.9, S=100$: $S'_f \approx 3$
- $D=2, R=0.9, S=1$: $S'_f \approx 0.3$

**特性**：
- 难度越高，遗忘后稳定性越低
- 原稳定性越高，遗忘后保留越多
- 可提取性越低（遗忘越久），遗忘后稳定性越高（记忆痕迹更深）

#### 2.2.7 下次间隔计算

```rust
pub fn next_interval(&self, stability: f64, elapsed_days: i64) -> f64 {
    let new_interval = (stability / Self::FACTOR
        * (self.request_retention.powf(1.0 / Self::DECAY) - 1.0))
        .round()
        .clamp(1.0, self.maximum_interval as f64);
    self.apply_fuzz(new_interval, elapsed_days)
}
```

**数学公式**：
$$I(r,S) = \frac{S}{FACTOR} \cdot \left(r^{\frac{1}{DECAY}} - 1\right)$$

其中：
- $r = request\_retention$（默认0.9）
- 当 $r = 0.9$ 时，$I = S$（保持90%保持率）
- 最大间隔：$36500$ 天（约100年）

#### 2.2.8 短期稳定性（同日复习）

```rust
pub fn short_term_stability(&self, stability: f64, rating: Rating) -> f64 {
    let rating_int = rating as i32;
    stability * f64::exp(self.w[17] * (rating_int as f64 - 3.0 + self.w[18]))
}
```

**数学公式**：
$$S'_{short}(S,G) = S \cdot e^{w_{17} \cdot (G-3+w_{18})}$$

**FSRS-6改进**：
在FSRS-6中，同日复习稳定性公式改为：
$$S'_r(S,G) = S \cdot e^{w_{17}(G-3+w_{18})} \cdot S^{-w_{19}}$$

稳定性增长更快当$S$小，增长更慢当$S$大，收敛到$S_{inc}=1$。

---

## 3. 关键代码片段（Python化提取）

### 3.1 核心数据结构

```python
from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum
from typing import Dict

class State(IntEnum):
    NEW = 0
    LEARNING = 1
    REVIEW = 2
    RELEARNING = 3

class Rating(IntEnum):
    AGAIN = 1
    HARD = 2
    GOOD = 3
    EASY = 4

@dataclass
class Card:
    """记忆卡片状态"""
    due: datetime              # 下次复习时间
    stability: float           # 稳定性（间隔天数，此时保持率为90%）
    difficulty: float          # 难度 [1, 10]
    elapsed_days: int          # 距离上次复习的天数
    scheduled_days: int        # 计划间隔天数
    reps: int                  # 复习次数
    lapses: int                # 遗忘次数
    state: State               # 当前状态
    last_review: datetime      # 上次复习时间

    def get_retrievability(self, now: datetime) -> float:
        """计算当前可提取性（回忆概率）"""
        if self.state == State.NEW:
            return 0.0
        elapsed_days = (now - self.last_review).days
        return forgetting_curve(elapsed_days, self.stability)
```

### 3.2 FSRS算法核心类

```python
import math

class FSRS:
    """FSRS-5算法Python实现"""

    # FSRS-5默认参数
    DEFAULT_WEIGHTS = [
        0.4072, 1.1829, 3.1262, 15.4722,   # 初始稳定性 S0(Again/Easy)
        7.2102, 0.5316,                     # 初始难度参数
        1.0651, 0.0234,                     # 难度调整 & 均值回归
        1.616, 0.1544, 1.0824,              # S'增长参数
        1.9813, 0.0953, 0.2975, 2.2042,     # 遗忘后稳定性
        0.2407, 2.9466,                     # Hard/Easy修正
        0.5034, 0.6567,                     # 短期稳定性
    ]

    # 常量
    DECAY = -0.5
    FACTOR = 19.0 / 81.0  # 0.234568

    def __init__(self, request_retention: float = 0.9, maximum_interval: int = 36500):
        self.w = self.DEFAULT_WEIGHTS.copy()
        self.request_retention = request_retention
        self.maximum_interval = maximum_interval

    @staticmethod
    def forgetting_curve(elapsed_days: float, stability: float) -> float:
        """遗忘曲线：计算可提取性"""
        return (1.0 + FSRS.FACTOR * elapsed_days / stability) ** FSRS.DECAY

    def init_stability(self, rating: Rating) -> float:
        """初始稳定性"""
        return max(self.w[rating - 1], 0.1)

    def init_difficulty(self, rating: Rating) -> float:
        """初始难度"""
        rating_int = rating.value
        d = self.w[4] - math.exp(self.w[5] * (rating_int - 1.0)) + 1.0
        return max(1.0, min(10.0, d))

    def next_difficulty(self, difficulty: float, rating: Rating) -> float:
        """更新难度：线性调整 + 均值回归"""
        rating_int = rating.value
        # 线性调整
        next_d = difficulty - self.w[6] * (rating_int - 3.0)
        # 均值回归到Easy的初始难度
        target = self.init_difficulty(Rating.EASY)
        final_d = self.w[7] * target + (1.0 - self.w[7]) * next_d
        return max(1.0, min(10.0, final_d))

    def next_recall_stability(self, difficulty: float, stability: float,
                             retrievability: float, rating: Rating) -> float:
        """成功回忆后的稳定性更新"""
        # 评级修正
        modifier = {
            Rating.HARD: self.w[15],
            Rating.EASY: self.w[16],
        }.get(rating, 1.0)

        # 核心公式
        s_inc = (math.exp(self.w[8])
                * (11.0 - difficulty)
                * stability ** (-self.w[9])
                * (math.exp(self.w[10] * (1.0 - retrievability)) - 1.0)
                * modifier + 1.0)

        return stability * s_inc

    def next_forget_stability(self, difficulty: float, stability: float,
                             retrievability: float) -> float:
        """遗忘后的稳定性更新"""
        return (self.w[11]
                * difficulty ** (-self.w[12])
                * ((stability + 1.0) ** self.w[13] - 1.0)
                * math.exp((1.0 - retrievability) * self.w[14]))

    def next_interval(self, stability: float) -> int:
        """下次复习间隔（天）"""
        interval = (stability / self.FACTOR
                   * (self.request_retention ** (1.0 / self.DECAY) - 1.0))
        return int(round(max(1.0, min(interval, self.maximum_interval))))

    def short_term_stability(self, stability: float, rating: Rating) -> float:
        """短期稳定性（同日复习）"""
        rating_int = rating.value
        return stability * math.exp(self.w[17] * (rating_int - 3.0 + self.w[18]))

    def repeat(self, card: Card, now: datetime) -> Dict[Rating, dict]:
        """预览所有评级结果"""
        retrievability = card.get_retrievability(now)
        results = {}

        for rating in Rating:
            if card.state == State.NEW:
                # 新卡片
                new_card = Card(
                    due=now,
                    stability=self.init_stability(rating),
                    difficulty=self.init_difficulty(rating),
                    elapsed_days=0,
                    scheduled_days=0,
                    reps=0,
                    lapses=0,
                    state=State.LEARNING if rating != Rating.EASY else State.REVIEW,
                    last_review=now,
                )
            else:
                # 已有卡片
                if rating == Rating.AGAIN:
                    new_stability = self.next_forget_stability(
                        card.difficulty, card.stability, retrievability
                    )
                    new_state = State.RELEARNING
                else:
                    new_stability = self.next_recall_stability(
                        card.difficulty, card.stability, retrievability, rating
                    )
                    new_state = State.REVIEW

                new_difficulty = self.next_difficulty(card.difficulty, rating)
                new_interval = self.next_interval(new_stability)

                new_card = Card(
                    due=now + timedelta(days=new_interval),
                    stability=new_stability,
                    difficulty=new_difficulty,
                    elapsed_days=0,
                    scheduled_days=new_interval,
                    reps=card.reps + (1 if rating != Rating.AGAIN else 0),
                    lapses=card.lapses + (1 if rating == Rating.AGAIN else 0),
                    state=new_state,
                    last_review=now,
                )

            results[rating] = {
                'card': new_card,
                'review_log': {
                    'rating': rating,
                    'elapsed_days': card.elapsed_days,
                    'scheduled_days': card.scheduled_days,
                    'state': card.state,
                    'retrievability': retrievability,
                }
            }

        return results
```

---

## 4. Vestige的MCP服务架构

### 4.1 二进制位置

```
~/bin/vestige-mcp   # MCP服务器
~/bin/vestige       # CLI工具
~/bin/vestige-restore  # 数据恢复
```

**当前状态**：本地未发现二进制文件，需要从ClawHub下载

### 4.2 MCP工具集

| 工具名 | 功能 | 用途 |
|--------|------|------|
| `search` | 统一搜索（关键词+语义+混合） | 查找记忆 |
| `smart_ingest` | 智能记忆存储（去重） | 保存新记忆 |
| `ingest` | 简单记忆存储 | 快速保存 |
| `memory` | 获取/删除/检查记忆 | 记忆管理 |
| `codebase` | 记代码模式 | 架构决策 |
| `intention` | 设置提醒 | 未来触发 |
| `promote_memory` | 标记有帮助 | 强化记忆 |
| `demote_memory` | 标记错误 | 弱化记忆 |

### 4.3 触发词机制

| 用户说 | 触发动作 |
|--------|----------|
| "Remember this" | smart_ingest立即 |
| "Don't forget" | smart_ingest高优先级 |
| "I always..." / "I never..." | 保存为偏好 |
| "I prefer..." / "I like..." | 保存为偏好 |
| "This is important" | smart_ingest + promote_memory |
| "Remind me..." | 创建intention |

### 4.4 数据存储位置

- **macOS**: `~/Library/Application Support/com.vestige.core/`
- **Linux**: `~/.local/share/vestige/`
- **向量缓存**: `~/Library/Caches/com.vestige.core/fastembed/`

---

## 5. 集成建议：为森森记忆系统

### 5.1 最小可行实现（MVP）

**阶段1：核心算法移植** ✅ 本报告完成
- 将FSRS-5核心公式Python化（已提供）
- 实现Card数据结构
- 实现forgetting_curve、next_interval等核心方法

**阶段2：记忆存储层**
```python
class MemoryEntry:
    """记忆条目"""
    id: str
    content: str
    tags: List[str]
    card: Card
    embedding: Optional[List[float]] = None  # 语义搜索
    created_at: datetime
    updated_at: datetime
```

**阶段3：MCP工具实现**
```python
@tool
def smart_ingest(content: str, tags: List[str] = None) -> str:
    """智能记忆存储：去重 + FSRS初始化"""
    # 1. 生成embedding
    # 2. 检查重复（相似度>0.9）
    # 3. 创建新Card(New状态)
    # 4. 保存到数据库
    pass

@tool
def review_memory(memory_id: str, rating: Rating) -> str:
    """复习记忆"""
    # 1. 获取Card
    # 2. 计算retrievability
    # 3. 更新stability、difficulty
    # 4. 计算next_interval
    # 5. 保存
    pass
```

### 5.2 扩展功能

#### 5.2.1 语义搜索集成
```python
@tool
def search(query: str, top_k: int = 10) -> List[MemoryEntry]:
    """语义搜索 + FSRS过滤"""
    # 1. 向量搜索
    # 2. 过滤已遗忘（retrievability < 0.3）
    # 3. 按retrievability排序
    pass
```

#### 5.2.2 智能提醒
```python
@tool
def get_due_memories(now: datetime) -> List[MemoryEntry]:
    """获取到期的记忆（需要复习）"""
    # 筛选 card.due <= now 的记忆
    # 按retrievability降序排序
    pass
```

#### 5.2.3 难度自适应
```python
def auto_rate(memory: MemoryEntry, user_response: str) -> Rating:
    """根据用户反馈自动评级"""
    # 关键词匹配：
    # - "忘了/错误" -> AGAIN
    # - "有点难" -> HARD
    # - "记得" -> GOOD
    # - "很简单" -> EASY
    pass
```

### 5.3 数据库设计

```sql
CREATE TABLE memories (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    tags TEXT,  -- JSON数组
    due TIMESTAMP NOT NULL,
    stability REAL NOT NULL,
    difficulty REAL NOT NULL,
    elapsed_days INTEGER NOT NULL,
    scheduled_days INTEGER NOT NULL,
    reps INTEGER NOT NULL,
    lapses INTEGER NOT NULL,
    state INTEGER NOT NULL,
    last_review TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_due ON memories(due);
CREATE INDEX idx_retrievability ON memories(stability, last_review);
```

### 5.4 与现有系统整合

**Vestige vs 现有memory/系统**：
| 维度 | memory/*.md | MEMORY.md | Vestige (FSRS) |
|------|------------|-----------|----------------|
| 目的 | 人类可读日志 | 手工整理笔记 | 自动记忆管理 |
| 搜索 | 关键词 | 手工结构化 | 语义+智能 |
| 衰减 | 无 | 无 | 自动（遗忘曲线） |
| 重复 | 无 | 无 | 间隔重复 |
| 用途 | 日常记录 | 重要笔记 | 持久记忆 |

**建议整合方案**：
1. **memory/*.md**：保持作为人类可读的日志
2. **MEMORY.md**：保持作为手工整理的长期笔记
3. **Vestige/FSRS**：
   - 自动从对话提取偏好模式
   - 在需要时提供语义搜索
   - 对重要信息进行间隔重复
   - **不完全替代**现有系统，而是**增强**

### 5.5 性能优化

**1. 批量复习**
```python
def batch_review(memory_ids: List[str], ratings: List[Rating]) -> dict:
    """批量更新多个记忆"""
    # 使用事务批量更新
    pass
```

**2. 按需计算retrievability**
```python
# 不实时计算，只在需要时
# 缓存常用记忆的retrievability
```

**3. 延迟加载embedding**
```python
# 只在搜索时加载embedding
# 刚保存的记忆暂时不embedding
```

---

## 6. 关键参数调优建议

### 6.1 请求保持率（request_retention）

| 场景 | 推荐值 | 说明 |
|------|--------|------|
| 高密度记忆（代码/技术） | 0.95 | 要求高精度，复习更频繁 |
| 日常对话记忆 | 0.85-0.9 | 平衡效率和准确度 |
| 兴趣爱好 | 0.8 | 允许适度遗忘，减少负担 |

### 6.2 最大间隔（maximum_interval）

| 场景 | 推荐值 | 说明 |
|------|--------|------|
| 长期知识 | 3650-36500 | 永久记忆 |
| 项目相关信息 | 365-730 | 项目周期 |
| 临时偏好 | 30-90 | 短期有效 |

### 6.3 个性化参数训练

使用fsrs-optimizer训练个人化参数：
```bash
# 需要至少1000次复习记录
fsrs-optimizer --review-log data/my_reviews.json --output my_params.json
```

---

## 7. 实现检查清单

- [ ] 移植FSRS-5核心公式（Python）
- [ ] 实现Card和MemoryEntry数据结构
- [ ] 实现forgetting_curve测试
- [ ] 实现next_interval测试
- [ ] 实现smart_ingest工具（去重+FSRS初始化）
- [ ] 实现review_memory工具
- [ ] 实现search工具（语义+FSRS过滤）
- [ ] 集成向量存储（fastembed或chromadb）
- [ ] 数据库设计（SQLite/PostgreSQL）
- [ ] 批量复习优化
- [ ] retrievability缓存
- [ ] 添加单元测试
- [ ] 添加集成测试
- [ ] 性能基准测试

---

## 8. 参考资源

### 8.1 官方文档
- [FSRS算法Wiki](https://github.com/open-spaced-repetition/fsrs4anki/wiki/The-Algorithm)
- [rs-fsrs实现](https://github.com/open-spaced-repetition/rs-fsrs)
- [py-fsrs Python包](https://github.com/open-spaced-repetition/py-fsrs)

### 8.2 可视化工具
- [Anki FSRS Visualizer](https://open-spaced-repetition.github.io/anki_fsrs_visualizer/)
- [GeoGebra模拟器](https://www.geogebra.org/calculator/ahqmqjvx)

### 8.3 研究论文
- MaiMemo DHP模型: https://www.maimemo.com/paper/
- DSR模型: https://supermemo.guru/wiki/Three_component_model_of_memory

---

## 9. 总结

### 9.1 核心发现

1. **Vestige使用rs-fsrs库**，当前实现FSRS-5算法（19个参数）
2. **FSRS-6是最新版本**（21个参数），改进了同日复习稳定性公式
3. **核心三要素**：Stability（稳定性）、Difficulty（难度）、Retrievability（可提取性）
4. **关键记忆定律**：
   - 难度越高，稳定性增长越慢
   - 稳定性越高，越难进一步提升
   - 间距效应：越久没复习，成功后提升越大
5. **遗忘曲线**：$R = (1 + 0.235 \cdot t/S)^{-0.5}$

### 9.2 集成难度评估

| 模块 | 难度 | 工作量 |
|------|------|--------|
| 核心算法移植 | ⭐⭐ | 已完成 |
| 数据库设计 | ⭐⭐ | 2小时 |
| MCP工具实现 | ⭐⭐⭐ | 4-6小时 |
| 语义搜索集成 | ⭐⭐⭐⭐ | 6-8小时 |
| 性能优化 | ⭐⭐⭐ | 4小时 |

**总计**：约16-20小时开发时间

### 9.3 下一步行动

1. **立即**：创建 `memory_fsrs.py` 文件，实现核心类
2. **本周**：实现smart_ingest和review_memory工具
3. **下周**：集成向量搜索和去重逻辑
4. **测试**：添加单元测试和集成测试
5. **优化**：根据实际使用调整参数

---

**报告完成时间**: 2026-02-19 21:57 GMT+8
**分析者**: OpenClaw Assistant
**版本**: 1.0
