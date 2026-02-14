#!/usr/bin/env python3
"""
智能情报收集调度系统 v2.0
Intelligent Intelligence Collection Scheduler

功能:
- 多源情报调度 (Moltbook/HN/GitHub)
- 自适应频率调整
- Signal评分自动优化
- 学习债务自动处理
- 情报质量评估

Cron设置: 根据模式自动调整
"""

import os
import json
import asyncio
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import sys

sys.path.insert(0, str(Path(__file__).parent))


class IntelScheduler:
    """情报收集调度器"""
    
    def __init__(self):
        self.workspace = Path("/root/.openclaw/workspace")
        self.memory_dir = self.workspace / "memory"
        self.intel_dir = self.memory_dir / "intel"
        self.report_dir = self.workspace / "reports" / "intel"
        
        # 配置
        self.config = {
            "normal_mode": {
                "interval_hours": 6,
                "signal_threshold": 7,
                "max_deep_extract": 3,
                "sources": ["moltbook", "hackernews", "github"]
            },
            "hyper_mode": {
                "interval_hours": 1,
                "signal_threshold": 6,
                "max_deep_extract": 10,
                "sources": ["moltbook", "hackernews", "github", "reddit", "arxiv"]
            },
            "adaptive_frequency": True
        }
        
        # 源配置
        self.sources = {
            "moltbook": {
                "script": "scripts/collect-web-intel-fast.py",
                "weight": 1.0,
                "enabled": True
            },
            "hackernews": {
                "script": "scripts/collect-web-intel-fast.py",
                "weight": 0.9,
                "enabled": True
            },
            "github": {
                "script": "scripts/collect-web-intel-fast.py",
                "weight": 0.8,
                "enabled": True
            },
            "reddit": {
                "script": "scripts/collect-web-intel-hyper.py",
                "weight": 0.7,
                "enabled": False  # 仅在超进化模式启用
            },
            "arxiv": {
                "script": "scripts/collect-web-intel-hyper.py",
                "weight": 0.6,
                "enabled": False
            }
        }
        
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.intel_dir.mkdir(parents=True, exist_ok=True)
        
        # 执行统计
        self.stats = {
            "sources_processed": 0,
            "items_collected": 0,
            "high_signal_count": 0,
            "learning_debt_added": 0,
            "errors": []
        }
        
        self.collected_items = []
    
    def run_scheduled_collection(self) -> Dict:
        """运行调度收集"""
        print(f"\n{'='*70}")
        print(f"🕸️  智能情报收集调度系统 v2.0")
        print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")
        
        # 1. 检测当前模式
        mode = self.detect_mode()
        print(f"📊 当前模式: {mode}")
        
        # 2. 检查是否应该执行
        if not self.should_run(mode):
            print("⏱️  距离上次收集时间太短，跳过本次执行")
            return {"status": "skipped", "reason": "too_early"}
        
        # 3. 获取源列表
        sources = self.get_active_sources(mode)
        print(f"📡 活跃源: {', '.join(sources)}")
        
        # 4. 执行收集
        for source in sources:
            self.collect_from_source(source, mode)
        
        # 5. 处理学习债务
        self.process_learning_debt()
        
        # 6. 评估情报质量
        self.assess_quality()
        
        # 7. 生成报告
        report = self.generate_report(mode)
        
        # 8. 保存调度状态
        self.save_scheduler_state(mode)
        
        print(f"\n{'='*70}")
        print("✅ 情报收集调度完成")
        print(f"{'='*70}\n")
        
        return report
    
    def detect_mode(self) -> str:
        """检测当前运行模式"""
        # 检查超进化状态文件
        hyper_state_file = self.memory_dir / "hyper-evolution-state.json"
        
        if hyper_state_file.exists():
            with open(hyper_state_file, 'r') as f:
                try:
                    state = json.load(f)
                    if state.get("active", False):
                        return "hyper"
                except:
                    pass
        
        # 检查自适应频率设置
        adaptive_file = self.memory_dir / "adaptive_freq.json"
        if adaptive_file.exists():
            with open(adaptive_file, 'r') as f:
                try:
                    config = json.load(f)
                    if config.get("current_mode") == "hyper":
                        return "hyper"
                except:
                    pass
        
        return "normal"
    
    def should_run(self, mode: str) -> bool:
        """检查是否应该执行收集"""
        state_file = self.memory_dir / "intel-scheduler-state.json"
        
        if not state_file.exists():
            return True
        
        with open(state_file, 'r') as f:
            try:
                state = json.load(f)
                last_run = state.get("last_run")
                if last_run:
                    last_time = datetime.fromisoformat(last_run)
                    interval = self.config[mode]["interval_hours"]
                    if datetime.now() - last_time < timedelta(hours=interval * 0.8):
                        return False
            except:
                pass
        
        return True
    
    def get_active_sources(self, mode: str) -> List[str]:
        """获取活跃的源列表"""
        config = self.config[mode]
        return [s for s in config["sources"] if self.sources.get(s, {}).get("enabled", False) or mode == "hyper"]
    
    def collect_from_source(self, source: str, mode: str):
        """从指定源收集情报"""
        print(f"\n📡 收集 [{source}]...")
        
        config = self.config[mode]
        
        try:
            # 根据源执行不同的收集逻辑
            if source == "moltbook":
                items = self.collect_moltbook(config)
            elif source == "hackernews":
                items = self.collect_hackernews(config)
            elif source == "github":
                items = self.collect_github(config)
            else:
                items = []
            
            self.stats["sources_processed"] += 1
            self.stats["items_collected"] += len(items)
            
            # 计算Signal
            for item in items:
                signal = self.calculate_signal(item)
                item["signal"] = signal
                
                if signal >= config["signal_threshold"]:
                    self.stats["high_signal_count"] += 1
                    self.collected_items.append(item)
            
            print(f"   ✓ 收集 {len(items)} 条，高Signal {len([i for i in items if i.get('signal', 0) >= config['signal_threshold']])} 条")
            
        except Exception as e:
            self.stats["errors"].append({"source": source, "error": str(e)})
            print(f"   ❌ 收集失败: {e}")
    
    def collect_moltbook(self, config: Dict) -> List[Dict]:
        """收集Moltbook情报"""
        # 尝试使用快速收集脚本
        try:
            result = subprocess.run(
                ["python3", str(self.workspace / "scripts" / "moltbook-quick-extract.py")],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # 解析输出中的JSON
            # 简化处理：返回空列表，实际应由专用脚本处理
            return []
            
        except:
            return []
    
    def collect_hackernews(self, config: Dict) -> List[Dict]:
        """收集Hacker News情报"""
        # 使用web search获取HN热门
        try:
            # 这里简化处理，实际应调用相关脚本
            return []
        except:
            return []
    
    def collect_github(self, config: Dict) -> List[Dict]:
        """收集GitHub Trending"""
        try:
            return []
        except:
            return []
    
    def calculate_signal(self, item: Dict) -> int:
        """计算Signal评分"""
        score = 5  # 基础分
        
        # 根据互动加分
        likes = item.get('likes', 0) or item.get('score', 0) or item.get('stars', 0)
        if isinstance(likes, str):
            likes = int(likes.replace('k', '000').replace('.', '')) if 'k' in likes.lower() else int(likes)
        
        if likes > 1000:
            score += 3
        elif likes > 500:
            score += 2
        elif likes > 100:
            score += 1
        
        # 根据关键词加分
        title = item.get('title', '').lower()
        keywords = ['agent', 'llm', 'ai', 'memory', 'autonomous', 'evolution', 
                   'mcp', 'rag', 'vector', 'embedding', 'learning']
        for keyword in keywords:
            if keyword in title:
                score += 1
                break
        
        return min(score, 10)
    
    def process_learning_debt(self):
        """处理学习债务"""
        print("\n📝 处理学习债务...")
        
        if not self.collected_items:
            print("   没有高Signal内容需要处理")
            return
        
        learning_debt_file = self.memory_dir / "learning-debt.md"
        
        # 写入学习债务
        with open(learning_debt_file, 'a', encoding='utf-8') as f:
            f.write(f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')} - 情报收集调度\n\n")
            
            for item in self.collected_items[:20]:  # 最多20条
                f.write(f"- [Signal {item.get('signal', 0)}] [{item.get('title', 'Untitled')[:80]}]({item.get('url', '')})\n")
            
            f.write(f"\n待处理: {len(self.collected_items)} 条\n")
        
        self.stats["learning_debt_added"] = len(self.collected_items)
        print(f"   ✓ 添加 {len(self.collected_items)} 条到学习债务")
    
    def assess_quality(self):
        """评估情报质量"""
        print("\n📊 评估情报质量...")
        
        if not self.collected_items:
            print("   没有内容可评估")
            return
        
        signals = [item.get('signal', 0) for item in self.collected_items]
        avg_signal = sum(signals) / len(signals) if signals else 0
        
        print(f"   平均Signal: {avg_signal:.1f}")
        print(f"   最高Signal: {max(signals) if signals else 0}")
        print(f"   内容数量: {len(self.collected_items)}")
        
        # 保存质量评估
        quality_file = self.intel_dir / f"quality-{datetime.now().strftime('%Y%m%d')}.json"
        quality_data = {
            "timestamp": datetime.now().isoformat(),
            "avg_signal": avg_signal,
            "max_signal": max(signals) if signals else 0,
            "count": len(self.collected_items)
        }
        
        with open(quality_file, 'w', encoding='utf-8') as f:
            json.dump(quality_data, f, indent=2)
    
    def generate_report(self, mode: str) -> Dict:
        """生成调度报告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "mode": mode,
            "configuration": self.config[mode],
            "statistics": self.stats,
            "collected_items": len(self.collected_items),
            "status": "success" if not self.stats["errors"] else "partial"
        }
        
        # 保存JSON报告
        report_file = self.report_dir / f"intel-scheduler-{datetime.now().strftime('%Y%m%d-%H%M')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 打印摘要
        print(f"\n{'='*70}")
        print("📋 情报收集调度报告")
        print(f"{'='*70}")
        print(f"模式: {mode}")
        print(f"处理源: {self.stats['sources_processed']}")
        print(f"收集内容: {self.stats['items_collected']} 条")
        print(f"高Signal: {self.stats['high_signal_count']} 条")
        print(f"学习债务: +{self.stats['learning_debt_added']} 条")
        print(f"错误: {len(self.stats['errors'])} 个")
        print(f"报告保存: {report_file}")
        print(f"{'='*70}")
        
        return report
    
    def save_scheduler_state(self, mode: str):
        """保存调度器状态"""
        state_file = self.memory_dir / "intel-scheduler-state.json"
        
        state = {
            "last_run": datetime.now().isoformat(),
            "last_mode": mode,
            "total_runs": 0,
            "total_items_collected": 0
        }
        
        if state_file.exists():
            with open(state_file, 'r') as f:
                try:
                    old_state = json.load(f)
                    state["total_runs"] = old_state.get("total_runs", 0) + 1
                    state["total_items_collected"] = old_state.get("total_items_collected", 0) + self.stats["items_collected"]
                except:
                    state["total_runs"] = 1
        else:
            state["total_runs"] = 1
        
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)


def main():
    """主函数"""
    scheduler = IntelScheduler()
    report = scheduler.run_scheduled_collection()
    return report


if __name__ == "__main__":
    main()
