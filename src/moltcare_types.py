"""
MoltCare Core Type Definitions (Python)

@version 1.0.0-alpha
@module moltcare/types
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any, Union, Callable, Literal
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto

# ============================================================================
# Core Enums
# ============================================================================

class PackCategory(str, Enum):
    """包分类"""
    FOUNDATION = "foundation"
    PROFESSIONAL = "professional"
    DOMAIN = "domain"


class OSType(str, Enum):
    """操作系统类型"""
    LINUX = "linux"
    MACOS = "macos"
    WINDOWS = "windows"


class Architecture(str, Enum):
    """架构类型"""
    AMD64 = "amd64"
    ARM64 = "arm64"


class ExpertRole(str, Enum):
    """专家角色"""
    RESEARCHER = "researcher"
    ARCHITECT = "architect"
    ENGINEER = "engineer"
    CAPTAIN = "captain"


class TriggerLayer(int, Enum):
    """触发策略层级"""
    FORCED = 0      # 强制触发
    KEYWORD = 1     # 关键词触发
    AI_DETECTION = 2  # AI检测触发
    USER_PREFERENCE = 3  # 用户偏好触发


class WorkflowStepType(str, Enum):
    """工作流步骤类型"""
    BUILTIN = "builtin"
    TEMPLATE = "template"
    ACTION = "action"
    CONDITION = "condition"
    LOOP = "loop"


class PackStatus(str, Enum):
    """包生命周期状态"""
    DISCOVERED = "discovered"
    LOADING = "loading"
    LOADED = "loaded"
    VALIDATING = "validating"
    READY = "ready"
    APPLYING = "applying"
    APPLIED = "applied"
    FAILED = "failed"
    UNLOADING = "unloading"
    UNLOADED = "unloaded"


class MoltCareEventType(str, Enum):
    """MoltCare事件类型"""
    # 包生命周期
    PACK_DISCOVERED = "pack:discovered"
    PACK_LOADED = "pack:loaded"
    PACK_APPLIED = "pack:applied"
    PACK_FAILED = "pack:failed"
    PACK_UNLOADED = "pack:unloaded"
    
    # 配置事件
    CONFIG_CHANGED = "config:changed"
    CONFIG_SYNCED = "config:synced"
    CONFIG_ROLLBACK = "config:rollback"
    
    # 专家事件
    EXPERT_TRIGGERED = "expert:triggered"
    EXPERT_STARTED = "expert:started"
    EXPERT_COMPLETED = "expert:completed"
    EXPERT_FAILED = "expert:failed"
    
    # 系统事件
    SYSTEM_ERROR = "system:error"
    SYSTEM_WARNING = "system:warning"


class MoltCareErrorCode(str, Enum):
    """MoltCare错误码"""
    # 包错误
    PACK_NOT_FOUND = "PACK_NOT_FOUND"
    PACK_INVALID = "PACK_INVALID"
    PACK_INCOMPATIBLE = "PACK_INCOMPATIBLE"
    PACK_CORRUPTED = "PACK_CORRUPTED"
    PACK_SIGNATURE_INVALID = "PACK_SIGNATURE_INVALID"
    
    # 依赖错误
    DEPENDENCY_MISSING = "DEPENDENCY_MISSING"
    DEPENDENCY_CONFLICT = "DEPENDENCY_CONFLICT"
    
    # 执行错误
    EXECUTION_TIMEOUT = "EXECUTION_TIMEOUT"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    SANDBOX_VIOLATION = "SANDBOX_VIOLATION"
    
    # 配置错误
    CONFIG_INVALID = "CONFIG_INVALID"
    CONFIG_SYNC_FAILED = "CONFIG_SYNC_FAILED"
    
    # 系统错误
    SYSTEM_ERROR = "SYSTEM_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    STORAGE_ERROR = "STORAGE_ERROR"


# ============================================================================
# Basic Types
# ============================================================================

I18nText = Dict[str, str]
Version = str
PackId = str
Timestamp = int


# ============================================================================
# Pack Types
# ============================================================================

@dataclass
class PackDependency:
    """包依赖项"""
    id: PackId
    version: Optional[str] = None
    optional: bool = False


@dataclass
class PackRequirements:
    """包依赖"""
    moltcare: Optional[str] = None
    packs: List[PackDependency] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)


@dataclass
class PackCompatibility:
    """包兼容性"""
    os: List[OSType] = field(default_factory=list)
    openclaw: Optional[str] = None


@dataclass
class PackEntry:
    """包入口点"""
    bootstrap: Optional[str] = None
    default: Optional[str] = None


@dataclass
class PackTriggers:
    """包触发配置"""
    keywords: List[str] = field(default_factory=list)
    auto_apply: bool = False


@dataclass
class PackResources:
    """包资源声明"""
    memory: Optional[str] = None
    disk: Optional[str] = None


@dataclass
class PackDefinition:
    """包定义"""
    id: PackId
    name: I18nText
    version: Version
    description: I18nText
    author: str
    license: str
    category: PackCategory
    domain: List[str] = field(default_factory=list)
    requires: Optional[PackRequirements] = None
    compatibility: Optional[PackCompatibility] = None
    entry: Optional[PackEntry] = None
    triggers: Optional[PackTriggers] = None
    resources: Optional[PackResources] = None


@dataclass
class PackManifest:
    """pack.yaml 根结构"""
    moltcare_version: Version
    pack: PackDefinition
    signature: Optional[str] = None


@dataclass
class PackInfo:
    """包信息 (运行时)"""
    id: PackId
    name: I18nText
    version: Version
    description: I18nText
    category: PackCategory
    status: PackStatus
    path: str
    installed_at: Optional[Timestamp] = None
    updated_at: Optional[Timestamp] = None


@dataclass
class LoadedPack(PackInfo):
    """加载的包"""
    manifest: PackManifest = field(default_factory=lambda: PackManifest(
        moltcare_version="",
        pack=PackDefinition(id="", name={}, version="", description={}, author="", license="", category=PackCategory.FOUNDATION)
    ))
    content_path: str = ""


# ============================================================================
# Workflow Types
# ============================================================================

@dataclass
class WorkflowVariable:
    """工作流变量"""
    name: str
    type: Literal["string", "number", "boolean", "object", "array"]
    default: Any = None
    required: bool = False
    description: Optional[str] = None


@dataclass
class WorkflowAction:
    """工作流动作"""
    action: str
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowStep:
    """工作流步骤"""
    id: str
    name: str
    type: WorkflowStepType
    action: Optional[str] = None
    template: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    condition: Optional[str] = None
    input: Optional[str] = None
    output: Optional[str] = None
    on_true: List[WorkflowAction] = field(default_factory=list)
    on_false: List[WorkflowAction] = field(default_factory=list)
    timeout: Optional[int] = None
    retries: int = 0


@dataclass
class WorkflowDefinition:
    """工作流定义"""
    name: str
    version: Version
    description: str
    steps: List[WorkflowStep] = field(default_factory=list)
    variables: List[WorkflowVariable] = field(default_factory=list)


@dataclass
class StepResult:
    """步骤执行结果"""
    step_id: str
    status: Literal["pending", "running", "success", "failed", "skipped"]
    output: Any = None
    error: Optional[ErrorInfo] = None
    start_time: Optional[Timestamp] = None
    end_time: Optional[Timestamp] = None
    duration: Optional[float] = None


@dataclass
class WorkflowContext:
    """工作流执行上下文"""
    workflow_id: str
    variables: Dict[str, Any] = field(default_factory=dict)
    steps: Dict[str, StepResult] = field(default_factory=dict)
    start_time: Timestamp = field(default_factory=lambda: int(datetime.now().timestamp() * 1000))


# ============================================================================
# Multi-Expert Types
# ============================================================================

@dataclass
class CodeChange:
    """代码变更"""
    file: str
    additions: int
    deletions: int
    type: Literal["add", "modify", "delete"]


@dataclass
class DecisionHistory:
    """历史决策"""
    type: str
    triggered: bool
    timestamp: Timestamp


@dataclass
class DecisionContext:
    """决策上下文"""
    input: str
    context: Dict[str, Any] = field(default_factory=dict)
    changes: List[CodeChange] = field(default_factory=list)
    history: List[DecisionHistory] = field(default_factory=list)


@dataclass
class TriggerResult:
    """触发结果"""
    should_trigger: bool
    layer: TriggerLayer
    score: float
    reason: str
    confidence: float


@dataclass
class Expert:
    """专家"""
    role: ExpertRole
    name: str
    description: str
    system_prompt: str


@dataclass
class ExpertOpinion:
    """专家意见"""
    role: ExpertRole
    content: str
    confidence: float
    key_points: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    timestamp: Timestamp = field(default_factory=lambda: int(datetime.now().timestamp() * 1000))


@dataclass
class DebateRequest:
    """辩论请求"""
    topic: str
    context: DecisionContext
    experts: List[ExpertRole] = field(default_factory=list)
    timeout: Optional[int] = None


@dataclass
class DebateResult:
    """辩论结果"""
    debate_id: str
    topic: str
    experts: List[ExpertOpinion]
    final_decision: ExpertOpinion
    consensus: bool
    confidence: float
    timestamp: Timestamp
    duration: float


# ============================================================================
# Bootstrap Types
# ============================================================================

@dataclass
class OpenClawInfo:
    """OpenClaw信息"""
    gateway_version: Version
    agent_version: Version
    available_tools: List[str] = field(default_factory=list)
    existing_skills: List[str] = field(default_factory=list)
    config_path: str = ""


@dataclass
class UserInfo:
    """用户信息"""
    primary_language: str
    profession_hint: Optional[str] = None
    workflow_preference: Optional[str] = None
    experience_level: Optional[Literal["beginner", "intermediate", "advanced"]] = None


@dataclass
class EnvironmentInfo:
    """环境检测结果"""
    os: OSType
    arch: Architecture
    shell: str
    openclaw: OpenClawInfo
    user: UserInfo
    detected_at: Timestamp = field(default_factory=lambda: int(datetime.now().timestamp() * 1000))


@dataclass
class UserPreferences:
    """用户偏好"""
    language: str
    theme: Optional[Literal["light", "dark", "auto"]] = None
    auto_apply_packs: bool = False
    expert_threshold: float = 7.0
    notification_level: Literal["all", "important", "none"] = "important"


@dataclass
class AgentConfig:
    """Agent配置"""
    version: Version
    generated_at: Timestamp
    environment: EnvironmentInfo
    preferences: UserPreferences
    applied_packs: List[PackId] = field(default_factory=list)
    custom_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EnvironmentProfile:
    """环境画像"""
    risk_level: Literal["low", "medium", "high"]
    capabilities: List[str] = field(default_factory=list)
    recommended_packs: List[PackId] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)


@dataclass
class BootstrapOptions:
    """初始化选项"""
    skip_detection: bool = False
    force: bool = False
    packs: List[PackId] = field(default_factory=list)


@dataclass
class BootstrapResult:
    """初始化结果"""
    success: bool
    environment: EnvironmentInfo
    config: AgentConfig
    applied_packs: List[PackId]
    duration: float
    error: Optional[ErrorInfo] = None


# ============================================================================
# Error Types
# ============================================================================

@dataclass
class ErrorInfo:
    """错误信息"""
    code: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    stack: Optional[str] = None
    timestamp: Timestamp = field(default_factory=lambda: int(datetime.now().timestamp() * 1000))


# ============================================================================
# Event Types
# ============================================================================

@dataclass
class MoltCareEvent:
    """基础事件"""
    type: MoltCareEventType
    timestamp: Timestamp
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConfigChange:
    """配置变更"""
    path: str
    old_value: Any
    new_value: Any


@dataclass
class PackEvent(MoltCareEvent):
    """包事件"""
    pack_id: PackId
    pack_version: Version
    duration: Optional[float] = None
    error: Optional[ErrorInfo] = None


@dataclass
class ConfigEvent(MoltCareEvent):
    """配置事件"""
    config_version: Version
    changes: List[ConfigChange] = field(default_factory=list)


@dataclass
class ExpertEvent(MoltCareEvent):
    """专家事件"""
    debate_id: str
    topic: str
    experts: List[ExpertRole] = field(default_factory=list)
    duration: Optional[float] = None
    result: Optional[DebateResult] = None
    error: Optional[ErrorInfo] = None


# 事件处理器类型
EventHandler = Callable[[MoltCareEvent], None]


# ============================================================================
# Security Types
# ============================================================================

@dataclass
class FilesystemSandbox:
    """文件系统沙箱"""
    read: List[str] = field(default_factory=list)
    write: List[str] = field(default_factory=list)
    forbidden: List[str] = field(default_factory=list)


@dataclass
class NetworkSandbox:
    """网络沙箱"""
    mode: Literal["allowlist", "denylist", "none"] = "allowlist"
    allowed_domains: List[str] = field(default_factory=list)
    denied_domains: List[str] = field(default_factory=list)


@dataclass
class ProcessSandbox:
    """进程沙箱"""
    max_memory: str = "100MB"
    max_cpu_percent: float = 50.0
    timeout: str = "30s"


@dataclass
class SystemCallSandbox:
    """系统调用沙箱"""
    mode: Literal["allowlist", "denylist"] = "allowlist"
    allowed: List[str] = field(default_factory=list)
    denied: List[str] = field(default_factory=list)


@dataclass
class SandboxConfig:
    """沙箱配置"""
    filesystem: FilesystemSandbox = field(default_factory=FilesystemSandbox)
    network: NetworkSandbox = field(default_factory=NetworkSandbox)
    process: ProcessSandbox = field(default_factory=ProcessSandbox)
    system_calls: SystemCallSandbox = field(default_factory=SystemCallSandbox)


# ============================================================================
# Adapter Types
# ============================================================================

@dataclass
class AdapterAuth:
    """Adapter认证"""
    type: Literal["token", "basic", "none"] = "none"
    token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


@dataclass
class AdapterConfig:
    """Adapter配置"""
    gateway_url: str
    timeout: int = 30000
    retries: int = 3
    auth: Optional[AdapterAuth] = None


@dataclass
class ApplyOptions:
    """应用选项"""
    force: bool = False
    skip_validation: bool = False
    variables: Dict[str, Any] = field(default_factory=dict)
    timeout: Optional[int] = None


@dataclass
class ApplyResult:
    """应用结果"""
    success: bool
    pack_id: PackId
    version: Version
    duration: float
    changes: List[ConfigChange] = field(default_factory=list)
    error: Optional[ErrorInfo] = None


@dataclass
class SyncResult:
    """同步结果"""
    success: bool
    synced_at: Timestamp
    changes: List[ConfigChange] = field(default_factory=list)
    error: Optional[ErrorInfo] = None


# ============================================================================
# Manager Interfaces (Abstract Base Classes)
# ============================================================================

from abc import ABC, abstractmethod


class IPackManager(ABC):
    """Pack管理器接口"""
    
    @abstractmethod
    async def discover(self, paths: List[str]) -> List[PackInfo]:
        """发现包"""
        pass
    
    @abstractmethod
    async def load(self, pack_id: PackId) -> LoadedPack:
        """加载包"""
        pass
    
    @abstractmethod
    async def apply(self, pack_id: PackId, options: Optional[ApplyOptions] = None) -> ApplyResult:
        """应用包"""
        pass
    
    @abstractmethod
    async def unload(self, pack_id: PackId) -> None:
        """卸载包"""
        pass
    
    @abstractmethod
    async def list(self, category: Optional[PackCategory] = None) -> List[PackInfo]:
        """列出包"""
        pass
    
    @abstractmethod
    async def get(self, pack_id: PackId) -> Optional[PackInfo]:
        """获取包信息"""
        pass


class IMultiExpertEngine(ABC):
    """多专家引擎接口"""
    
    @abstractmethod
    async def should_trigger(self, context: DecisionContext) -> TriggerResult:
        """检测是否应该触发专家"""
        pass
    
    @abstractmethod
    async def debate(self, request: DebateRequest) -> DebateResult:
        """执行专家辩论"""
        pass
    
    @abstractmethod
    def register_expert(self, expert: Expert) -> None:
        """注册专家"""
        pass
    
    @abstractmethod
    def get_experts(self) -> List[Expert]:
        """获取专家列表"""
        pass


class IAgentBootstrap(ABC):
    """初始化模块接口"""
    
    @abstractmethod
    async def detect_environment(self) -> EnvironmentInfo:
        """检测环境"""
        pass
    
    @abstractmethod
    async def analyze_environment(self, env: EnvironmentInfo) -> EnvironmentProfile:
        """分析环境"""
        pass
    
    @abstractmethod
    async def generate_config(self, profile: EnvironmentProfile) -> AgentConfig:
        """生成配置"""
        pass
    
    @abstractmethod
    async def recommend_packs(self, config: AgentConfig) -> List[PackId]:
        """推荐包"""
        pass
    
    @abstractmethod
    async def initialize(self, options: Optional[BootstrapOptions] = None) -> BootstrapResult:
        """执行初始化"""
        pass


class IEventBus(ABC):
    """事件总线接口"""
    
    @abstractmethod
    def on(self, event: MoltCareEventType, handler: EventHandler) -> None:
        """订阅事件"""
        pass
    
    @abstractmethod
    def off(self, event: MoltCareEventType, handler: EventHandler) -> None:
        """取消订阅"""
        pass
    
    @abstractmethod
    def emit(self, event: MoltCareEvent) -> None:
        """发布事件"""
        pass
    
    @abstractmethod
    def once(self, event: MoltCareEventType, handler: EventHandler) -> None:
        """一次性订阅"""
        pass


class IOpenClawAdapter(ABC):
    """OpenClaw适配器接口"""
    
    @abstractmethod
    async def initialize(self, config: AdapterConfig) -> None:
        """初始化"""
        pass
    
    @abstractmethod
    async def sync_config(self, config: AgentConfig) -> SyncResult:
        """同步配置"""
        pass
    
    @abstractmethod
    async def get_current_config(self) -> AgentConfig:
        """获取当前配置"""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """关闭连接"""
        pass


# ============================================================================
# Constants
# ============================================================================

class Constants:
    """常量定义"""
    
    # 默认超时时间 (毫秒)
    DEFAULT_TIMEOUT = 30000
    
    # 默认重试次数
    DEFAULT_RETRIES = 3
    
    # 专家触发阈值
    EXPERT_TRIGGER_THRESHOLD = 7.0
    
    # 关键词匹配阈值
    KEYWORD_MATCH_THRESHOLD = 0.8
    
    # 支持的语言
    SUPPORTED_LANGUAGES = ['en', 'zh', 'ja', 'ko', 'de', 'fr', 'es', 'ru', 'ar']
    
    # 包文件名称
    PACK_MANIFEST_FILENAME = 'pack.yaml'
    
    # 包Schema文件名
    PACK_SCHEMA_FILENAME = 'schema.json'


# Type aliases for common patterns
Result = Union[
    Dict[str, Any],  # Success with data
    ErrorInfo,       # Error
]
