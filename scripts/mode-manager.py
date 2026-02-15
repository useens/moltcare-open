#!/usr/bin/env python3
"""
森森智能模式管理核心
自动根据任务复杂度、时间、成本预算切换运行模式
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

MODE_FILE = Path("/root/.openclaw/workspace/memory/current-mode.json")
COST_LOG = Path("/root/.openclaw/workspace/memory/cost-log.json")
MODE_HISTORY = Path("/root/.openclaw/workspace/memory/mode-history.json")

# 模式配置
MODES = {
    "performance": {
        "name": "🔥 性能模式",
        "thinking": "high",
        "max_tokens": 8192,
        "parallel_agents": 5,
        "cost_per_min": 1500,
        "desc": "深度学习、架构设计、竞品分析"
    },
    "balanced": {
        "name": "⚖️ 均衡模式",
        "thinking": "low", 
        "max_tokens": 4096,
        "parallel_agents": 2,
        "cost_per_min": 200,
        "desc": "日常任务、标准响应、默认模式"
    },
    "eco": {
        "name": "🌱 节能模式",
        "thinking": "off",
        "max_tokens": 1024,
        "parallel_agents": 1,
        "cost_per_min": 50,
        "desc": "心跳检查、简单确认、状态查询"
    },
    "frozen": {
        "name": "❄️ 冻结模式",
        "thinking": "none",
        "max_tokens": 0,
        "parallel_agents": 0,
        "cost_per_min": 0,
        "desc": "零成本待机、被动等待唤醒"
    }
}

# 每小时预算上限 (tokens)
HOURLY_BUDGET = {
    "performance": 10000,
    "balanced": 3000,
    "eco": 800,
    "frozen": 0
}

class ModeManager:
    def __init__(self):
        self.current_mode = self._load_current_mode()
        self.cost_log = self._load_cost_log()
    
    def _load_current_mode(self):
        """加载当前模式"""
        if MODE_FILE.exists():
            with open(MODE_FILE) as f:
                return json.load(f)
        return {"mode": "balanced", "switched_at": datetime.now().isoformat()}
    
    def _load_cost_log(self):
        """加载成本日志"""
        if COST_LOG.exists():
            with open(COST_LOG) as f:
                return json.load(f)
        return {"today": 0, "hourly": {}, "history": []}
    
    def _save_mode(self, mode, reason="auto"):
        """保存模式配置"""
        config = {
            "mode": mode,
            "config": MODES[mode],
            "switched_at": datetime.now().isoformat(),
            "reason": reason
        }
        MODE_FILE.write_text(json.dumps(config, indent=2))
        
        # 记录历史
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "from": self.current_mode.get("mode"),
            "to": mode,
            "reason": reason
        }
        if MODE_HISTORY.exists():
            history = json.loads(MODE_HISTORY.read_text())
        else:
            history = []
        history.append(history_entry)
        MODE_HISTORY.write_text(json.dumps(history[-100:], indent=2))  # 保留最近100条
    
    def assess_task_complexity(self, task_text):
        """评估任务复杂度"""
        score = 0
        text = task_text.lower()
        
        # 高性能关键词
        high_keywords = ["分析", "设计", "架构", "研究", "对比", "评估", "优化", "重构"]
        for kw in high_keywords:
            if kw in text:
                score += 2
        
        # 中等复杂度关键词
        mid_keywords = ["总结", "整理", "检查", "执行", "创建", "修改"]
        for kw in mid_keywords:
            if kw in text:
                score += 1
        
        # 简单关键词
        if any(kw in text for kw in ["查看", "确认", "ok", "是", "否"]):
            score = max(0, score - 1)
        
        # 文件数量指标
        file_count = text.count(".md") + text.count(".py") + text.count(".json")
        score += min(file_count // 2, 3)
        
        return score
    
    def get_recommended_mode(self, task_text=None, context_tokens=0):
        """获取推荐模式"""
        now = datetime.now()
        hour = now.hour
        
        # 时间因子：夜间自动降级
        if hour >= 23 or hour < 7:
            if self.current_mode.get("mode") != "frozen":
                return "frozen", "夜间时段自动冻结"
        
        # 成本检查
        current_hour = now.strftime("%H")
        hour_cost = self.cost_log.get("hourly", {}).get(current_hour, 0)
        current_mode = self.current_mode.get("mode", "balanced")
        budget = HOURLY_BUDGET.get(current_mode, 3000)
        
        if hour_cost > budget * 0.9:  # 超过90%预算
            # 降级
            mode_order = ["performance", "balanced", "eco", "frozen"]
            current_idx = mode_order.index(current_mode)
            if current_idx < len(mode_order) - 1:
                new_mode = mode_order[current_idx + 1]
                return new_mode, f"成本保护: 当前{hour_cost}t > 预算{budget}t的90%"
        
        # 任务复杂度评估
        if task_text:
            complexity = self.assess_task_complexity(task_text)
            if complexity >= 6:
                return "performance", f"高复杂度任务 (score={complexity})"
            elif complexity >= 3:
                return "balanced", f"中等复杂度任务 (score={complexity})"
            else:
                return "eco", f"低复杂度任务 (score={complexity})"
        
        # 默认保持当前模式
        return current_mode, "保持当前模式"
    
    def switch_mode(self, new_mode, reason="manual"):
        """切换模式"""
        if new_mode not in MODES:
            print(f"❌ 未知模式: {new_mode}")
            return False
        
        old_mode = self.current_mode.get("mode", "balanced")
        self._save_mode(new_mode, reason)
        self.current_mode = {"mode": new_mode}
        
        print(f"✅ {MODES[new_mode]['name']}")
        print(f"   从 {MODES.get(old_mode, {}).get('name', old_mode)} 切换")
        print(f"   原因: {reason}")
        print(f"   配置: thinking={MODES[new_mode]['thinking']}, max_tokens={MODES[new_mode]['max_tokens']}")
        return True
    
    def show_status(self):
        """显示当前状态"""
        mode = self.current_mode.get("mode", "balanced")
        config = MODES.get(mode, MODES["balanced"])
        
        now = datetime.now()
        current_hour = now.strftime("%H")
        hour_cost = self.cost_log.get("hourly", {}).get(current_hour, 0)
        budget = HOURLY_BUDGET.get(mode, 3000)
        
        print(f"\n📊 当前模式: {config['name']}")
        print(f"   描述: {config['desc']}")
        print(f"   配置: thinking={config['thinking']}, max_tokens={config['max_tokens']}")
        print(f"   成本: ~{config['cost_per_min']} tokens/min")
        print(f"\n💰 本小时消耗: {hour_cost} / {budget} tokens ({hour_cost/budget*100:.1f}%)")
        print(f"📅 今日总计: {self.cost_log.get('today', 0)} tokens")
        print(f"🕐 切换时间: {self.current_mode.get('switched_at', 'unknown')}")
        print(f"\n💡 提示: 使用 /performance /balanced /eco /frozen 手动切换")
    
    def auto_adjust(self, task_text=None):
        """自动调整模式"""
        recommended, reason = self.get_recommended_mode(task_text)
        current = self.current_mode.get("mode", "balanced")
        
        if recommended != current:
            return self.switch_mode(recommended, reason)
        return False

# CLI接口
if __name__ == "__main__":
    manager = ModeManager()
    
    if len(sys.argv) < 2:
        manager.show_status()
    elif sys.argv[1] in ["status", "s"]:
        manager.show_status()
    elif sys.argv[1] in ["auto", "a"]:
        task = sys.argv[2] if len(sys.argv) > 2 else None
        manager.auto_adjust(task)
    elif sys.argv[1] in MODES:
        manager.switch_mode(sys.argv[1])
    else:
        print(f"用法: {sys.argv[0]} [performance|balanced|eco|frozen|status|auto]")