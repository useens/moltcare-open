#!/usr/bin/env python3
"""
EvoMap Auto-Resolver - 自动发现问题并从 EvoMap 寻找解决方案
集成到森森的自主决策流程中
"""

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data" / "evomap"
LOG_FILE = WORKSPACE / "logs" / "evomap-resolver.log"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] EvoMap-Resolver: {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

@dataclass
class ErrorPattern:
    """错误模式定义"""
    pattern: str
    signals: List[str]
    description: str
    auto_apply: bool = False

# 错误模式到 EvoMap signals 的映射
ERROR_PATTERNS = [
    # 网络错误
    ErrorPattern(
        pattern=r"(timeout|connection.*refused|econnrefused|econnreset|429|too many requests)",
        signals=["TimeoutError", "ECONNRESET", "ECONNREFUSED", "429TooManyRequests"],
        description="网络连接错误或限流",
        auto_apply=True
    ),
    # 内存错误
    ErrorPattern(
        pattern=r"(oom|out of memory|oomkilled|memory.*exceeded|cannot allocate memory)",
        signals=["OOMKilled", "memory_limit", "container_memory"],
        description="内存不足错误",
        auto_apply=True
    ),
    # 数据库错误
    ErrorPattern(
        pattern=r"(mysql.*gone away|operationalerror|database.*locked|connection.*closed)",
        signals=["2006", "MySQL", "database", "connection"],
        description="数据库连接错误",
        auto_apply=False  # 需要人工确认
    ),
    # 文件系统错误
    ErrorPattern(
        pattern=r"(enoent|no such file|permission denied|eacces)",
        signals=["ENOENT", "permission", "file_not_found"],
        description="文件系统错误",
        auto_apply=False
    ),
    # 飞书错误
    ErrorPattern(
        pattern=r"(feishu|lark|message.*fail|card.*reject|format.*error)",
        signals=["FeishuFormatError", "markdown_render_failed", "card_send_rejected"],
        description="飞书消息发送错误",
        auto_apply=True
    ),
    # CORS 错误
    ErrorPattern(
        pattern=r"(cors|access-control|preflight|blocked by cors)",
        signals=["CORS_preflight", "OPTIONS_blocked", "WebView_origin"],
        description="CORS 跨域错误",
        auto_apply=True
    ),
    # 会话/上下文丢失
    ErrorPattern(
        pattern=r"(session.*lost|context.*gap|amnesia|forget|no memory)",
        signals=["session_amnesia", "context_loss", "cross_session_gap"],
        description="会话记忆丢失",
        auto_apply=True
    ),
    # Agent 错误
    ErrorPattern(
        pattern=r"(agent.*error|tool.*fail|execution.*error|runtime.*exception)",
        signals=["agent_error", "auto_debug", "self_repair", "runtime_exception"],
        description="Agent 执行错误",
        auto_apply=True
    ),
    # 命令不存在
    ErrorPattern(
        pattern=r"(command not found|not found|enoent|127)",
        signals=["CommandNotFound", "127", "not found"],
        description="命令不存在",
        auto_apply=True
    ),
    # WebSocket 错误
    ErrorPattern(
        pattern=r"(websocket|ws.*disconnect|1000040345|system.*busy)",
        signals=["WSDisconnect", "1000040345", "system_busy", "ws_reconnect_failed"],
        description="WebSocket 连接错误",
        auto_apply=True
    ),
]

def load_node_id():
    """从配置文件加载当前节点ID"""
    config_file = WORKSPACE / "config" / "evomap" / "node-config.json"
    if config_file.exists():
        with open(config_file) as f:
            config = json.load(f)
            return config.get("node_id", "unknown")
    return "unknown"

class EvoMapResolver:
    """EvoMap 自动解决器"""
    
    def __init__(self):
        self.node_id = load_node_id()
        self.data_dir = DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.resolution_log = self.data_dir / "auto-resolutions.jsonl"
    
    def analyze_error(self, error_text: str) -> Optional[ErrorPattern]:
        """分析错误文本，匹配已知模式"""
        error_lower = error_text.lower()
        
        for pattern in ERROR_PATTERNS:
            if re.search(pattern.pattern, error_lower):
                log(f"🔍 匹配错误模式: {pattern.description}")
                log(f"   Signals: {pattern.signals}")
                log(f"   Auto-apply: {pattern.auto_apply}")
                return pattern
        
        return None
    
    def fetch_matching_capsules(self, signals: List[str]) -> List[Dict]:
        """从 EvoMap 获取匹配的 capsules"""
        log(f"📡 查询 EvoMap: signals={signals}")
        
        # 构建 fetch 请求
        payload = {
            "protocol": "gep-a2a",
            "protocol_version": "1.0.0",
            "message_type": "fetch",
            "message_id": f"msg_{int(datetime.utcnow().timestamp() * 1000)}_auto",
            "sender_id": self.node_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "payload": {
                "asset_type": "Capsule",
                "limit": 5
            }
        }
        
        try:
            result = subprocess.run(
                ["curl", "-sL", "-X", "POST", 
                 "https://evomap.ai/a2a/fetch",
                 "-H", "Content-Type: application/json",
                 "-d", json.dumps(payload),
                 "--max-time", "15"],
                capture_output=True,
                text=True,
                timeout=20
            )
            
            if result.returncode != 0:
                log(f"⚠️ 查询失败: {result.stderr}")
                return []
            
            data = json.loads(result.stdout)
            capsules = data.get("payload", {}).get("results", [])
            
            # 按 signals 匹配度排序
            scored_capsules = []
            for cap in capsules:
                cap_signals = cap.get("payload", {}).get("trigger", [])
                score = len(set(s.lower() for s in signals) & 
                           set(s.lower() for s in cap_signals))
                if score > 0:
                    scored_capsules.append((score, cap))
            
            scored_capsules.sort(key=lambda x: x[0], reverse=True)
            
            log(f"✅ 找到 {len(scored_capsules)} 个匹配的 capsules")
            return [cap for _, cap in scored_capsules]
            
        except Exception as e:
            log(f"⚠️ 查询异常: {e}")
            return []
    
    def apply_capsule(self, capsule: Dict, error_context: str) -> bool:
        """应用 capsule 解决方案"""
        cap_id = capsule.get("asset_id", "unknown")
        summary = capsule.get("payload", {}).get("summary", "No summary")[:60]
        
        log(f"🔧 应用 Capsule: {cap_id}")
        log(f"   Summary: {summary}...")
        
        # 这里可以实现具体的应用逻辑
        # 目前先记录到日志和文件
        
        application = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "capsule_id": cap_id,
            "error_context": error_context[:200],
            "summary": summary,
            "gdi_score": capsule.get("gdi_score", 0),
            "status": "applied"
        }
        
        # 保存应用记录
        with open(self.resolution_log, "a") as f:
            f.write(json.dumps(application) + "\n")
        
        log(f"✅ 已记录应用: {cap_id}")
        return True
    
    def resolve(self, error_text: str, context: str = "") -> Optional[Dict]:
        """
        主入口：尝试自动解决错误
        
        Returns:
            成功: {"status": "resolved", "capsule": {...}}
            失败: {"status": "failed", "reason": "..."}
            无匹配: None
        """
        log(f"\n{'='*60}")
        log(f"🚨 错误检测: {error_text[:100]}...")
        log(f"{'='*60}")
        
        # 1. 分析错误
        pattern = self.analyze_error(error_text)
        if not pattern:
            log("❌ 未匹配已知错误模式")
            return None
        
        # 2. 查询 EvoMap
        capsules = self.fetch_matching_capsules(pattern.signals)
        if not capsules:
            log("❌ EvoMap 无匹配解决方案")
            return {"status": "failed", "reason": "no_matching_capsule"}
        
        # 3. 选择最佳匹配（GDI 最高）
        best_capsule = max(capsules, key=lambda c: c.get("gdi_score", 0))
        gdi = best_capsule.get("gdi_score", 0)
        
        log(f"⭐ 最佳匹配: GDI={gdi}")
        
        # 4. 判断是否可以自动应用
        if not pattern.auto_apply and gdi < 70:
            log(f"⚠️ 需要人工确认 (auto_apply={pattern.auto_apply}, GDI={gdi})")
            return {
                "status": "needs_review",
                "capsule": best_capsule,
                "reason": "high_risk_or_low_confidence"
            }
        
        # 5. 应用解决方案
        if self.apply_capsule(best_capsule, error_text):
            return {
                "status": "resolved",
                "capsule": best_capsule,
                "signals_used": pattern.signals
            }
        
        return {"status": "failed", "reason": "application_failed"}
    
    def get_resolution_stats(self) -> Dict:
        """获取自动解决统计"""
        if not self.resolution_log.exists():
            return {"total": 0}
        
        applications = []
        with open(self.resolution_log) as f:
            for line in f:
                try:
                    applications.append(json.loads(line))
                except:
                    pass
        
        return {
            "total": len(applications),
            "last_24h": len([a for a in applications 
                           if (datetime.utcnow() - datetime.fromisoformat(a["timestamp"].replace("Z", "+00:00"))).days < 1]),
            "avg_gdi": sum(a.get("gdi_score", 0) for a in applications) / len(applications) if applications else 0
        }

def test_resolver():
    """测试解决器"""
    resolver = EvoMapResolver()
    
    # 测试用例
    test_errors = [
        "Connection timeout after 30000ms",
        "MySQL server has gone away (2006)",
        "Feishu message format error: card rejected",
        "Unknown custom error XYZ123"
    ]
    
    print("\n" + "="*60)
    print("EvoMap Auto-Resolver Test")
    print("="*60 + "\n")
    
    for error in test_errors:
        result = resolver.resolve(error)
        status = result.get("status", "none") if result else "no_match"
        print(f"\nError: {error[:40]}...")
        print(f"Result: {status}")
        print("-" * 60)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_resolver()
    else:
        # 实际运行：监听 stdin 或文件
        print("Usage: python3 evomap-resolver.py --test")
        print("Or integrate into main flow:")
        print("  from evomap_resolver import EvoMapResolver")
        print("  resolver = EvoMapResolver()")
        print("  result = resolver.resolve(error_text)")
