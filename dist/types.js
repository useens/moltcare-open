"use strict";
/**
 * MoltCare Core Type Definitions
 *
 * @version 1.0.0-alpha
 * @module moltcare/types
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.CONSTANTS = exports.MoltCareErrorCode = exports.MoltCareEventType = exports.PackStatus = exports.WorkflowStepType = exports.TriggerLayer = exports.ExpertRole = exports.Architecture = exports.OSType = exports.PackCategory = void 0;
// ============================================================================
// Core Enums
// ============================================================================
/**
 * 包分类
 */
var PackCategory;
(function (PackCategory) {
    PackCategory["FOUNDATION"] = "foundation";
    PackCategory["PROFESSIONAL"] = "professional";
    PackCategory["DOMAIN"] = "domain";
})(PackCategory || (exports.PackCategory = PackCategory = {}));
/**
 * 操作系统类型
 */
var OSType;
(function (OSType) {
    OSType["LINUX"] = "linux";
    OSType["MACOS"] = "macos";
    OSType["WINDOWS"] = "windows";
})(OSType || (exports.OSType = OSType = {}));
/**
 * 架构类型
 */
var Architecture;
(function (Architecture) {
    Architecture["AMD64"] = "amd64";
    Architecture["ARM64"] = "arm64";
})(Architecture || (exports.Architecture = Architecture = {}));
/**
 * 专家角色
 */
var ExpertRole;
(function (ExpertRole) {
    ExpertRole["RESEARCHER"] = "researcher";
    ExpertRole["ARCHITECT"] = "architect";
    ExpertRole["ENGINEER"] = "engineer";
    ExpertRole["CAPTAIN"] = "captain";
})(ExpertRole || (exports.ExpertRole = ExpertRole = {}));
/**
 * 触发策略层级
 */
var TriggerLayer;
(function (TriggerLayer) {
    TriggerLayer[TriggerLayer["FORCED"] = 0] = "FORCED";
    TriggerLayer[TriggerLayer["KEYWORD"] = 1] = "KEYWORD";
    TriggerLayer[TriggerLayer["AI_DETECTION"] = 2] = "AI_DETECTION";
    TriggerLayer[TriggerLayer["USER_PREFERENCE"] = 3] = "USER_PREFERENCE";
})(TriggerLayer || (exports.TriggerLayer = TriggerLayer = {}));
/**
 * 工作流步骤类型
 */
var WorkflowStepType;
(function (WorkflowStepType) {
    WorkflowStepType["BUILTIN"] = "builtin";
    WorkflowStepType["TEMPLATE"] = "template";
    WorkflowStepType["ACTION"] = "action";
    WorkflowStepType["CONDITION"] = "condition";
    WorkflowStepType["LOOP"] = "loop";
})(WorkflowStepType || (exports.WorkflowStepType = WorkflowStepType = {}));
/**
 * 包生命周期状态
 */
var PackStatus;
(function (PackStatus) {
    PackStatus["DISCOVERED"] = "discovered";
    PackStatus["LOADING"] = "loading";
    PackStatus["LOADED"] = "loaded";
    PackStatus["VALIDATING"] = "validating";
    PackStatus["READY"] = "ready";
    PackStatus["APPLYING"] = "applying";
    PackStatus["APPLIED"] = "applied";
    PackStatus["FAILED"] = "failed";
    PackStatus["UNLOADING"] = "unloading";
    PackStatus["UNLOADED"] = "unloaded";
})(PackStatus || (exports.PackStatus = PackStatus = {}));
/**
 * MoltCare事件类型
 */
var MoltCareEventType;
(function (MoltCareEventType) {
    // 包生命周期
    MoltCareEventType["PACK_DISCOVERED"] = "pack:discovered";
    MoltCareEventType["PACK_LOADED"] = "pack:loaded";
    MoltCareEventType["PACK_APPLIED"] = "pack:applied";
    MoltCareEventType["PACK_FAILED"] = "pack:failed";
    MoltCareEventType["PACK_UNLOADED"] = "pack:unloaded";
    // 配置事件
    MoltCareEventType["CONFIG_CHANGED"] = "config:changed";
    MoltCareEventType["CONFIG_SYNCED"] = "config:synced";
    MoltCareEventType["CONFIG_ROLLBACK"] = "config:rollback";
    // 专家事件
    MoltCareEventType["EXPERT_TRIGGERED"] = "expert:triggered";
    MoltCareEventType["EXPERT_STARTED"] = "expert:started";
    MoltCareEventType["EXPERT_COMPLETED"] = "expert:completed";
    MoltCareEventType["EXPERT_FAILED"] = "expert:failed";
    // 系统事件
    MoltCareEventType["SYSTEM_ERROR"] = "system:error";
    MoltCareEventType["SYSTEM_WARNING"] = "system:warning";
})(MoltCareEventType || (exports.MoltCareEventType = MoltCareEventType = {}));
/**
 * MoltCare错误码
 */
var MoltCareErrorCode;
(function (MoltCareErrorCode) {
    // 包错误
    MoltCareErrorCode["PACK_NOT_FOUND"] = "PACK_NOT_FOUND";
    MoltCareErrorCode["PACK_INVALID"] = "PACK_INVALID";
    MoltCareErrorCode["PACK_INCOMPATIBLE"] = "PACK_INCOMPATIBLE";
    MoltCareErrorCode["PACK_CORRUPTED"] = "PACK_CORRUPTED";
    MoltCareErrorCode["PACK_SIGNATURE_INVALID"] = "PACK_SIGNATURE_INVALID";
    // 依赖错误
    MoltCareErrorCode["DEPENDENCY_MISSING"] = "DEPENDENCY_MISSING";
    MoltCareErrorCode["DEPENDENCY_CONFLICT"] = "DEPENDENCY_CONFLICT";
    // 执行错误
    MoltCareErrorCode["EXECUTION_TIMEOUT"] = "EXECUTION_TIMEOUT";
    MoltCareErrorCode["EXECUTION_FAILED"] = "EXECUTION_FAILED";
    MoltCareErrorCode["SANDBOX_VIOLATION"] = "SANDBOX_VIOLATION";
    // 配置错误
    MoltCareErrorCode["CONFIG_INVALID"] = "CONFIG_INVALID";
    MoltCareErrorCode["CONFIG_SYNC_FAILED"] = "CONFIG_SYNC_FAILED";
    // 系统错误
    MoltCareErrorCode["SYSTEM_ERROR"] = "SYSTEM_ERROR";
    MoltCareErrorCode["NETWORK_ERROR"] = "NETWORK_ERROR";
    MoltCareErrorCode["STORAGE_ERROR"] = "STORAGE_ERROR";
})(MoltCareErrorCode || (exports.MoltCareErrorCode = MoltCareErrorCode = {}));
// ============================================================================
// Constants
// ============================================================================
/**
 * 常量定义
 */
exports.CONSTANTS = {
    /** 默认超时时间 (毫秒) */
    DEFAULT_TIMEOUT: 30000,
    /** 默认重试次数 */
    DEFAULT_RETRIES: 3,
    /** 专家触发阈值 */
    EXPERT_TRIGGER_THRESHOLD: 7.0,
    /** 关键词匹配阈值 */
    KEYWORD_MATCH_THRESHOLD: 0.8,
    /** 支持的语言 */
    SUPPORTED_LANGUAGES: ['en', 'zh', 'ja', 'ko', 'de', 'fr', 'es', 'ru', 'ar'],
    /** 包文件名称 */
    PACK_MANIFEST_FILENAME: 'pack.yaml',
    /** 包Schema文件名 */
    PACK_SCHEMA_FILENAME: 'schema.json',
};
exports.default = {
    PackCategory,
    OSType,
    Architecture,
    ExpertRole,
    TriggerLayer,
    WorkflowStepType,
    PackStatus,
    MoltCareEventType,
    MoltCareErrorCode,
    CONSTANTS: exports.CONSTANTS,
};
//# sourceMappingURL=types.js.map