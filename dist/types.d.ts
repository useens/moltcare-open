/**
 * MoltCare Core Type Definitions
 *
 * @version 1.0.0-alpha
 * @module moltcare/types
 */
/**
 * 包分类
 */
export declare enum PackCategory {
    FOUNDATION = "foundation",
    PROFESSIONAL = "professional",
    DOMAIN = "domain"
}
/**
 * 操作系统类型
 */
export declare enum OSType {
    LINUX = "linux",
    MACOS = "macos",
    WINDOWS = "windows"
}
/**
 * 架构类型
 */
export declare enum Architecture {
    AMD64 = "amd64",
    ARM64 = "arm64"
}
/**
 * 专家角色
 */
export declare enum ExpertRole {
    RESEARCHER = "researcher",
    ARCHITECT = "architect",
    ENGINEER = "engineer",
    CAPTAIN = "captain"
}
/**
 * 触发策略层级
 */
export declare enum TriggerLayer {
    FORCED = 0,// 强制触发
    KEYWORD = 1,// 关键词触发
    AI_DETECTION = 2,// AI检测触发
    USER_PREFERENCE = 3
}
/**
 * 工作流步骤类型
 */
export declare enum WorkflowStepType {
    BUILTIN = "builtin",
    TEMPLATE = "template",
    ACTION = "action",
    CONDITION = "condition",
    LOOP = "loop"
}
/**
 * 包生命周期状态
 */
export declare enum PackStatus {
    DISCOVERED = "discovered",
    LOADING = "loading",
    LOADED = "loaded",
    VALIDATING = "validating",
    READY = "ready",
    APPLYING = "applying",
    APPLIED = "applied",
    FAILED = "failed",
    UNLOADING = "unloading",
    UNLOADED = "unloaded"
}
/**
 * MoltCare事件类型
 */
export declare enum MoltCareEventType {
    PACK_DISCOVERED = "pack:discovered",
    PACK_LOADED = "pack:loaded",
    PACK_APPLIED = "pack:applied",
    PACK_FAILED = "pack:failed",
    PACK_UNLOADED = "pack:unloaded",
    CONFIG_CHANGED = "config:changed",
    CONFIG_SYNCED = "config:synced",
    CONFIG_ROLLBACK = "config:rollback",
    EXPERT_TRIGGERED = "expert:triggered",
    EXPERT_STARTED = "expert:started",
    EXPERT_COMPLETED = "expert:completed",
    EXPERT_FAILED = "expert:failed",
    SYSTEM_ERROR = "system:error",
    SYSTEM_WARNING = "system:warning"
}
/**
 * 多语言文本
 */
export type I18nText = {
    [lang: string]: string;
};
/**
 * 版本号
 */
export type Version = string;
/**
 * 包ID
 */
export type PackId = string;
/**
 * 时间戳 (毫秒)
 */
export type Timestamp = number;
/**
 * pack.yaml 根结构
 */
export interface PackManifest {
    /** MoltCare兼容版本 */
    moltcareVersion: Version;
    /** 包定义 */
    pack: PackDefinition;
    /** 签名 (可选) */
    signature?: string;
}
/**
 * 包定义
 */
export interface PackDefinition {
    /** 唯一标识符 */
    id: PackId;
    /** 多语言名称 */
    name: I18nText;
    /** 版本号 */
    version: Version;
    /** 多语言描述 */
    description: I18nText;
    /** 作者 */
    author: string;
    /** 许可证 */
    license: string;
    /** 包分类 */
    category: PackCategory;
    /** 领域标签 */
    domain: string[];
    /** 依赖管理 */
    requires?: PackRequirements;
    /** 兼容性 */
    compatibility?: PackCompatibility;
    /** 入口点 */
    entry?: PackEntry;
    /** 触发配置 */
    triggers?: PackTriggers;
    /** 资源声明 */
    resources?: PackResources;
}
/**
 * 包依赖
 */
export interface PackRequirements {
    /** MoltCare版本要求 */
    moltcare?: string;
    /** 依赖的其他包 */
    packs?: PackDependency[];
    /** 需要的系统工具 */
    tools?: string[];
}
/**
 * 包依赖项
 */
export interface PackDependency {
    id: PackId;
    version?: string;
    optional?: boolean;
}
/**
 * 包兼容性
 */
export interface PackCompatibility {
    /** 支持的操作系统 */
    os?: OSType[];
    /** OpenClaw版本要求 */
    openclaw?: string;
}
/**
 * 包入口点
 */
export interface PackEntry {
    /** 初始化入口 */
    bootstrap?: string;
    /** 默认入口 */
    default?: string;
}
/**
 * 包触发配置
 */
export interface PackTriggers {
    /** 触发关键词 */
    keywords?: string[];
    /** 是否自动应用 */
    autoApply?: boolean;
}
/**
 * 包资源声明
 */
export interface PackResources {
    /** 预估内存占用 */
    memory?: string;
    /** 磁盘占用 */
    disk?: string;
}
/**
 * 包信息 (运行时)
 */
export interface PackInfo {
    id: PackId;
    name: I18nText;
    version: Version;
    description: I18nText;
    category: PackCategory;
    status: PackStatus;
    path: string;
    installedAt?: Timestamp;
    updatedAt?: Timestamp;
}
/**
 * 加载的包
 */
export interface LoadedPack extends PackInfo {
    manifest: PackManifest;
    contentPath: string;
}
/**
 * 工作流定义
 */
export interface WorkflowDefinition {
    name: string;
    version: Version;
    description: string;
    steps: WorkflowStep[];
    variables?: WorkflowVariable[];
}
/**
 * 工作流变量
 */
export interface WorkflowVariable {
    name: string;
    type: 'string' | 'number' | 'boolean' | 'object' | 'array';
    default?: any;
    required?: boolean;
    description?: string;
}
/**
 * 工作流步骤
 */
export interface WorkflowStep {
    id: string;
    name: string;
    type: WorkflowStepType;
    action?: string;
    template?: string;
    context?: Record<string, any>;
    condition?: string;
    input?: string;
    output?: string;
    onTrue?: WorkflowAction[];
    onFalse?: WorkflowAction[];
    timeout?: number;
    retries?: number;
}
/**
 * 工作流动作
 */
export interface WorkflowAction {
    action: string;
    params?: Record<string, any>;
}
/**
 * 工作流执行上下文
 */
export interface WorkflowContext {
    workflowId: string;
    variables: Record<string, any>;
    steps: Record<string, StepResult>;
    startTime: Timestamp;
}
/**
 * 步骤执行结果
 */
export interface StepResult {
    stepId: string;
    status: 'pending' | 'running' | 'success' | 'failed' | 'skipped';
    output?: any;
    error?: ErrorInfo;
    startTime?: Timestamp;
    endTime?: Timestamp;
    duration?: number;
}
/**
 * 决策上下文
 */
export interface DecisionContext {
    /** 输入文本 */
    input: string;
    /** 上下文信息 */
    context?: Record<string, any>;
    /** 代码变更信息 */
    changes?: CodeChange[];
    /** 历史决策 */
    history?: DecisionHistory[];
}
/**
 * 代码变更
 */
export interface CodeChange {
    file: string;
    additions: number;
    deletions: number;
    type: 'add' | 'modify' | 'delete';
}
/**
 * 历史决策
 */
export interface DecisionHistory {
    type: string;
    triggered: boolean;
    timestamp: Timestamp;
}
/**
 * 触发结果
 */
export interface TriggerResult {
    shouldTrigger: boolean;
    layer: TriggerLayer;
    score: number;
    reason: string;
    confidence: number;
}
/**
 * 专家
 */
export interface Expert {
    role: ExpertRole;
    name: string;
    description: string;
    systemPrompt: string;
}
/**
 * 辩论请求
 */
export interface DebateRequest {
    topic: string;
    context: DecisionContext;
    experts?: ExpertRole[];
    timeout?: number;
}
/**
 * 辩论结果
 */
export interface DebateResult {
    debateId: string;
    topic: string;
    experts: ExpertOpinion[];
    finalDecision: ExpertOpinion;
    consensus: boolean;
    confidence: number;
    timestamp: Timestamp;
    duration: number;
}
/**
 * 专家意见
 */
export interface ExpertOpinion {
    role: ExpertRole;
    content: string;
    confidence: number;
    keyPoints: string[];
    recommendations: string[];
    timestamp: Timestamp;
}
/**
 * 环境检测结果
 */
export interface EnvironmentInfo {
    /** 操作系统 */
    os: OSType;
    /** 架构 */
    arch: Architecture;
    /** Shell类型 */
    shell: string;
    /** OpenClaw信息 */
    openclaw: OpenClawInfo;
    /** 用户信息 */
    user: UserInfo;
    /** 检测时间 */
    detectedAt: Timestamp;
}
/**
 * OpenClaw信息
 */
export interface OpenClawInfo {
    gatewayVersion: Version;
    agentVersion: Version;
    availableTools: string[];
    existingSkills: string[];
    configPath: string;
}
/**
 * 用户信息
 */
export interface UserInfo {
    primaryLanguage: string;
    professionHint?: string;
    workflowPreference?: string;
    experienceLevel?: 'beginner' | 'intermediate' | 'advanced';
}
/**
 * Agent配置
 */
export interface AgentConfig {
    version: Version;
    generatedAt: Timestamp;
    environment: EnvironmentInfo;
    preferences: UserPreferences;
    appliedPacks: PackId[];
    customSettings?: Record<string, any>;
}
/**
 * 用户偏好
 */
export interface UserPreferences {
    language: string;
    theme?: 'light' | 'dark' | 'auto';
    autoApplyPacks?: boolean;
    expertThreshold?: number;
    notificationLevel?: 'all' | 'important' | 'none';
}
/**
 * 基础事件
 */
export interface MoltCareEvent {
    type: MoltCareEventType;
    timestamp: Timestamp;
    source: string;
    metadata?: Record<string, any>;
}
/**
 * 包事件
 */
export interface PackEvent extends MoltCareEvent {
    type: MoltCareEventType.PACK_DISCOVERED | MoltCareEventType.PACK_LOADED | MoltCareEventType.PACK_APPLIED | MoltCareEventType.PACK_FAILED | MoltCareEventType.PACK_UNLOADED;
    packId: PackId;
    packVersion: Version;
    duration?: number;
    error?: ErrorInfo;
}
/**
 * 配置事件
 */
export interface ConfigEvent extends MoltCareEvent {
    type: MoltCareEventType.CONFIG_CHANGED | MoltCareEventType.CONFIG_SYNCED | MoltCareEventType.CONFIG_ROLLBACK;
    configVersion: Version;
    changes?: ConfigChange[];
}
/**
 * 配置变更
 */
export interface ConfigChange {
    path: string;
    oldValue: any;
    newValue: any;
}
/**
 * 专家事件
 */
export interface ExpertEvent extends MoltCareEvent {
    type: MoltCareEventType.EXPERT_TRIGGERED | MoltCareEventType.EXPERT_STARTED | MoltCareEventType.EXPERT_COMPLETED | MoltCareEventType.EXPERT_FAILED;
    debateId: string;
    topic: string;
    experts: ExpertRole[];
    duration?: number;
    result?: DebateResult;
    error?: ErrorInfo;
}
/**
 * 事件处理器
 */
export type EventHandler = (event: MoltCareEvent) => void | Promise<void>;
/**
 * Adapter配置
 */
export interface AdapterConfig {
    /** Gateway地址 */
    gatewayUrl: string;
    /** 超时时间 */
    timeout?: number;
    /** 重试次数 */
    retries?: number;
    /** 认证信息 */
    auth?: AdapterAuth;
}
/**
 * Adapter认证
 */
export interface AdapterAuth {
    type: 'token' | 'basic' | 'none';
    token?: string;
    username?: string;
    password?: string;
}
/**
 * 应用选项
 */
export interface ApplyOptions {
    /** 强制重新应用 */
    force?: boolean;
    /** 跳过验证 */
    skipValidation?: boolean;
    /** 自定义变量 */
    variables?: Record<string, any>;
    /** 超时时间 */
    timeout?: number;
}
/**
 * 应用结果
 */
export interface ApplyResult {
    success: boolean;
    packId: PackId;
    version: Version;
    duration: number;
    changes: ConfigChange[];
    error?: ErrorInfo;
}
/**
 * 同步结果
 */
export interface SyncResult {
    success: boolean;
    syncedAt: Timestamp;
    changes: ConfigChange[];
    error?: ErrorInfo;
}
/**
 * 错误信息
 */
export interface ErrorInfo {
    code: string;
    message: string;
    details?: Record<string, any>;
    stack?: string;
    timestamp: Timestamp;
}
/**
 * MoltCare错误码
 */
export declare enum MoltCareErrorCode {
    PACK_NOT_FOUND = "PACK_NOT_FOUND",
    PACK_INVALID = "PACK_INVALID",
    PACK_INCOMPATIBLE = "PACK_INCOMPATIBLE",
    PACK_CORRUPTED = "PACK_CORRUPTED",
    PACK_SIGNATURE_INVALID = "PACK_SIGNATURE_INVALID",
    DEPENDENCY_MISSING = "DEPENDENCY_MISSING",
    DEPENDENCY_CONFLICT = "DEPENDENCY_CONFLICT",
    EXECUTION_TIMEOUT = "EXECUTION_TIMEOUT",
    EXECUTION_FAILED = "EXECUTION_FAILED",
    SANDBOX_VIOLATION = "SANDBOX_VIOLATION",
    CONFIG_INVALID = "CONFIG_INVALID",
    CONFIG_SYNC_FAILED = "CONFIG_SYNC_FAILED",
    SYSTEM_ERROR = "SYSTEM_ERROR",
    NETWORK_ERROR = "NETWORK_ERROR",
    STORAGE_ERROR = "STORAGE_ERROR"
}
/**
 * 沙箱配置
 */
export interface SandboxConfig {
    filesystem: FilesystemSandbox;
    network: NetworkSandbox;
    process: ProcessSandbox;
    systemCalls: SystemCallSandbox;
}
/**
 * 文件系统沙箱
 */
export interface FilesystemSandbox {
    read: string[];
    write: string[];
    forbidden: string[];
}
/**
 * 网络沙箱
 */
export interface NetworkSandbox {
    mode: 'allowlist' | 'denylist' | 'none';
    allowedDomains?: string[];
    deniedDomains?: string[];
}
/**
 * 进程沙箱
 */
export interface ProcessSandbox {
    maxMemory: string;
    maxCpuPercent: number;
    timeout: string;
}
/**
 * 系统调用沙箱
 */
export interface SystemCallSandbox {
    mode: 'allowlist' | 'denylist';
    allowed?: string[];
    denied?: string[];
}
/**
 * Pack管理器接口
 */
export interface IPackManager {
    /** 发现包 */
    discover(paths: string[]): Promise<PackInfo[]>;
    /** 加载包 */
    load(packId: PackId): Promise<LoadedPack>;
    /** 应用包 */
    apply(packId: PackId, options?: ApplyOptions): Promise<ApplyResult>;
    /** 卸载包 */
    unload(packId: PackId): Promise<void>;
    /** 列出包 */
    list(category?: PackCategory): Promise<PackInfo[]>;
    /** 获取包信息 */
    get(packId: PackId): Promise<PackInfo | null>;
}
/**
 * 多专家引擎接口
 */
export interface IMultiExpertEngine {
    /** 检测是否应该触发专家 */
    shouldTrigger(context: DecisionContext): Promise<TriggerResult>;
    /** 执行专家辩论 */
    debate(request: DebateRequest): Promise<DebateResult>;
    /** 注册专家 */
    registerExpert(expert: Expert): void;
    /** 获取专家列表 */
    getExperts(): Expert[];
}
/**
 * 初始化模块接口
 */
export interface IAgentBootstrap {
    /** 检测环境 */
    detectEnvironment(): Promise<EnvironmentInfo>;
    /** 分析环境 */
    analyzeEnvironment(env: EnvironmentInfo): Promise<EnvironmentProfile>;
    /** 生成配置 */
    generateConfig(profile: EnvironmentProfile): Promise<AgentConfig>;
    /** 推荐包 */
    recommendPacks(config: AgentConfig): Promise<PackId[]>;
    /** 执行初始化 */
    initialize(options?: BootstrapOptions): Promise<BootstrapResult>;
}
/**
 * 环境画像
 */
export interface EnvironmentProfile {
    riskLevel: 'low' | 'medium' | 'high';
    capabilities: string[];
    recommendedPacks: PackId[];
    constraints: string[];
}
/**
 * 初始化选项
 */
export interface BootstrapOptions {
    skipDetection?: boolean;
    force?: boolean;
    packs?: PackId[];
}
/**
 * 初始化结果
 */
export interface BootstrapResult {
    success: boolean;
    environment: EnvironmentInfo;
    config: AgentConfig;
    appliedPacks: PackId[];
    duration: number;
    error?: ErrorInfo;
}
/**
 * 事件总线接口
 */
export interface IEventBus {
    /** 订阅事件 */
    on(event: MoltCareEventType, handler: EventHandler): void;
    /** 取消订阅 */
    off(event: MoltCareEventType, handler: EventHandler): void;
    /** 发布事件 */
    emit(event: MoltCareEvent): void;
    /** 一次性订阅 */
    once(event: MoltCareEventType, handler: EventHandler): void;
}
/**
 * OpenClaw适配器接口
 */
export interface IOpenClawAdapter {
    /** 初始化 */
    initialize(config: AdapterConfig): Promise<void>;
    /** 同步配置 */
    syncConfig(config: AgentConfig): Promise<SyncResult>;
    /** 获取当前配置 */
    getCurrentConfig(): Promise<AgentConfig>;
    /** 关闭连接 */
    close(): Promise<void>;
}
/**
 * 结果类型
 */
export type Result<T, E = ErrorInfo> = {
    success: true;
    data: T;
    error?: never;
} | {
    success: false;
    data?: never;
    error: E;
};
/**
 * 异步结果
 */
export type AsyncResult<T, E = ErrorInfo> = Promise<Result<T, E>>;
/**
 * 可序列化对象
 */
export type Serializable = string | number | boolean | null | Serializable[] | {
    [key: string]: Serializable;
};
/**
 * DeepPartial工具类型
 */
export type DeepPartial<T> = {
    [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};
/**
 * DeepRequired工具类型
 */
export type DeepRequired<T> = {
    [P in keyof T]-?: T[P] extends object ? DeepRequired<T[P]> : T[P];
};
/**
 * 常量定义
 */
export declare const CONSTANTS: {
    /** 默认超时时间 (毫秒) */
    readonly DEFAULT_TIMEOUT: 30000;
    /** 默认重试次数 */
    readonly DEFAULT_RETRIES: 3;
    /** 专家触发阈值 */
    readonly EXPERT_TRIGGER_THRESHOLD: 7;
    /** 关键词匹配阈值 */
    readonly KEYWORD_MATCH_THRESHOLD: 0.8;
    /** 支持的语言 */
    readonly SUPPORTED_LANGUAGES: readonly ["en", "zh", "ja", "ko", "de", "fr", "es", "ru", "ar"];
    /** 包文件名称 */
    readonly PACK_MANIFEST_FILENAME: "pack.yaml";
    /** 包Schema文件名 */
    readonly PACK_SCHEMA_FILENAME: "schema.json";
};
declare const _default: {
    PackCategory: typeof PackCategory;
    OSType: typeof OSType;
    Architecture: typeof Architecture;
    ExpertRole: typeof ExpertRole;
    TriggerLayer: typeof TriggerLayer;
    WorkflowStepType: typeof WorkflowStepType;
    PackStatus: typeof PackStatus;
    MoltCareEventType: typeof MoltCareEventType;
    MoltCareErrorCode: typeof MoltCareErrorCode;
    CONSTANTS: {
        /** 默认超时时间 (毫秒) */
        readonly DEFAULT_TIMEOUT: 30000;
        /** 默认重试次数 */
        readonly DEFAULT_RETRIES: 3;
        /** 专家触发阈值 */
        readonly EXPERT_TRIGGER_THRESHOLD: 7;
        /** 关键词匹配阈值 */
        readonly KEYWORD_MATCH_THRESHOLD: 0.8;
        /** 支持的语言 */
        readonly SUPPORTED_LANGUAGES: readonly ["en", "zh", "ja", "ko", "de", "fr", "es", "ru", "ar"];
        /** 包文件名称 */
        readonly PACK_MANIFEST_FILENAME: "pack.yaml";
        /** 包Schema文件名 */
        readonly PACK_SCHEMA_FILENAME: "schema.json";
    };
};
export default _default;
//# sourceMappingURL=types.d.ts.map