#!/usr/bin/env python3
"""
v6.0 可视化洞察系统
- 记忆图谱可视化
- 进化历程仪表盘
- 实时状态监控
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sys

sys.path.insert(0, 'scripts/memory-system')

class MemoryVisualization:
    """记忆可视化引擎"""
    
    def __init__(self):
        self.memory_dir = "memory"
        self.output_dir = "memory/visualizations"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_memory_stats(self) -> Dict[str, Any]:
        """生成记忆统计报告"""
        stats = {
            'timestamp': datetime.now().isoformat(),
            'memory_system': {},
            'evolution_progress': {},
            'system_health': {}
        }
        
        # 1. 向量记忆统计
        vector_file = f"{self.memory_dir}/vector/memory_vectors.pkl"
        if os.path.exists(vector_file):
            import pickle
            with open(vector_file, 'rb') as f:
                vectors = pickle.load(f)
            stats['memory_system']['vector_memories'] = len(vectors)
            stats['memory_system']['vector_storage_kb'] = round(os.path.getsize(vector_file) / 1024, 2)
        
        # 2. 关联图谱统计
        graph_file = f"{self.memory_dir}/associations/memory_graph.json"
        if os.path.exists(graph_file):
            with open(graph_file, 'r') as f:
                graph = json.load(f)
            stats['memory_system']['associations'] = len(graph.get('edges', []))
            stats['memory_system']['memory_nodes'] = len(graph.get('nodes', []))
        
        # 3. 进化版本统计
        modules_dir = f"{self.memory_dir}/modules"
        versions = []
        for f in os.listdir(modules_dir):
            if f.startswith('linlin-v') and f.endswith('-release.md'):
                version = f.replace('linlin-', '').replace('-release.md', '')
                versions.append(version)
        stats['evolution_progress']['completed_versions'] = sorted(versions)
        stats['evolution_progress']['total_versions'] = len(versions)
        
        # 4. 快照统计
        snapshots_dir = f"{self.memory_dir}/snapshots"
        if os.path.exists(snapshots_dir):
            snapshot_count = len([f for f in os.listdir(snapshots_dir) if f.startswith('snap_')])
            stats['system_health']['snapshots'] = snapshot_count
        
        # 5. 今日活动统计
        daily_file = f"{self.memory_dir}/daily/{datetime.now().strftime('%Y-%m-%d')}.md"
        if os.path.exists(daily_file):
            with open(daily_file, 'r') as f:
                content = f.read()
            stats['system_health']['today_activity_lines'] = len(content.split('\n'))
        
        return stats
    
    def generate_text_dashboard(self) -> str:
        """生成文本仪表盘"""
        stats = self.generate_memory_stats()
        
        lines = []
        lines.append("=" * 60)
        lines.append("🌱 林林 v6.0 记忆系统仪表盘")
        lines.append("=" * 60)
        lines.append(f"生成时间: {stats['timestamp']}")
        lines.append("")
        
        # 记忆系统
        lines.append("📊 记忆系统状态")
        lines.append("-" * 40)
        mem = stats['memory_system']
        lines.append(f"  向量记忆: {mem.get('vector_memories', 0)} 条")
        lines.append(f"  存储占用: {mem.get('vector_storage_kb', 0)} KB")
        lines.append(f"  记忆节点: {mem.get('memory_nodes', 0)} 个")
        lines.append(f"  关联边数: {mem.get('associations', 0)} 条")
        lines.append("")
        
        # 进化进度
        lines.append("🚀 进化历程")
        lines.append("-" * 40)
        evo = stats['evolution_progress']
        lines.append(f"  完成版本: {evo.get('total_versions', 0)} 个")
        for v in evo.get('completed_versions', []):
            lines.append(f"    ✓ {v}")
        lines.append("")
        
        # 系统健康
        lines.append("💓 系统健康")
        lines.append("-" * 40)
        health = stats['system_health']
        lines.append(f"  快照数量: {health.get('snapshots', 0)} 个")
        lines.append(f"  今日活动: {health.get('today_activity_lines', 0)} 行")
        lines.append("")
        
        lines.append("=" * 60)
        
        return '\n'.join(lines)
    
    def generate_memory_graph_text(self) -> str:
        """生成记忆图谱文本可视化"""
        graph_file = f"{self.memory_dir}/associations/memory_graph.json"
        if not os.path.exists(graph_file):
            return "记忆图谱不存在"
        
        with open(graph_file, 'r') as f:
            graph = json.load(f)
        
        lines = []
        lines.append("=" * 60)
        lines.append("🕸️ 记忆关联图谱")
        lines.append("=" * 60)
        lines.append("")
        
        # 找出连接最多的节点（核心记忆）
        node_connections = {}
        for edge in graph.get('edges', []):
            source = edge.get('source', '')
            target = edge.get('target', '')
            node_connections[source] = node_connections.get(source, 0) + 1
            node_connections[target] = node_connections.get(target, 0) + 1
        
        # 排序
        sorted_nodes = sorted(node_connections.items(), key=lambda x: x[1], reverse=True)
        
        lines.append("核心记忆节点（按关联度）:")
        lines.append("-" * 40)
        for node_id, count in sorted_nodes[:10]:
            # 获取记忆内容
            content = self._get_memory_content(node_id)
            preview = content[:40] + "..." if len(content) > 40 else content
            lines.append(f"  [{count:2d}] {preview}")
        
        lines.append("")
        lines.append(f"总计: {len(graph.get('nodes', []))} 节点, {len(graph.get('edges', []))} 关联")
        lines.append("=" * 60)
        
        return '\n'.join(lines)
    
    def _get_memory_content(self, memory_id: str) -> str:
        """获取记忆内容"""
        # 尝试从长期记忆中查找
        lt_file = f"{self.memory_dir}/long_term_memories.json"
        if os.path.exists(lt_file):
            with open(lt_file, 'r') as f:
                memories = json.load(f)
            for mem in memories:
                if mem.get('id') == memory_id:
                    return mem.get('content', 'Unknown')
        return memory_id[:30]
    
    def save_dashboard(self):
        """保存仪表盘到文件"""
        dashboard = self.generate_text_dashboard()
        graph_viz = self.generate_memory_graph_text()
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存仪表盘
        dashboard_file = f"{self.output_dir}/dashboard_{timestamp}.txt"
        with open(dashboard_file, 'w') as f:
            f.write(dashboard)
            f.write("\n\n")
            f.write(graph_viz)
        
        # 同时保存为最新版本
        latest_file = f"{self.output_dir}/dashboard_latest.txt"
        with open(latest_file, 'w') as f:
            f.write(dashboard)
            f.write("\n\n")
            f.write(graph_viz)
        
        return {
            'dashboard_file': dashboard_file,
            'latest_file': latest_file
        }


def main():
    """命令行测试"""
    viz = MemoryVisualization()
    
    print("=" * 60)
    print("🌐 v6.0 可视化洞察系统测试")
    print("=" * 60)
    
    # 生成仪表盘
    print("\n📊 生成系统仪表盘...")
    dashboard = viz.generate_text_dashboard()
    print(dashboard)
    
    # 生成图谱可视化
    print("\n" + viz.generate_memory_graph_text())
    
    # 保存文件
    print("\n💾 保存可视化文件...")
    result = viz.save_dashboard()
    print(f"   已保存: {result['latest_file']}")
    
    print("\n" + "=" * 60)
    print("✅ v6.0 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
