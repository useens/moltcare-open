# 智能任务调度器 - RSI 实验 #1
"""
自动识别可并行任务，使用 sessions_spawn 同时处理
"""
import re
from typing import List, Dict, Any

class TaskScheduler:
    def __init__(self):
        self.parallel_patterns = [
            # 多个独立文件操作
            (r'读.*文件.*和.*读.*文件', 'parallel_files'),
            # 多个独立搜索
            (r'搜索.*和.*搜索', 'parallel_search'),
            # 多个独立检查
            (r'检查.*和.*检查', 'parallel_checks'),
        ]
    
    def analyze_tasks(self, user_request: str) -> Dict[str, Any]:
        """分析用户请求，判断是否可以并行"""
        tasks = {
            'can_parallel': False,
            'task_type': None,
            'subtasks': [],
            'reason': ''
        }
        
        # 检查并行模式
        for pattern, task_type in self.parallel_patterns:
            if re.search(pattern, user_request):
                tasks['can_parallel'] = True
                tasks['task_type'] = task_type
                tasks['subtasks'] = self._extract_subtasks(user_request)
                tasks['reason'] = f"检测到{task_type}模式"
                break
        
        # 检查独立操作关键词
        independent_ops = ['同时', '分别', '各自', '批量']
        if any(op in user_request for op in independent_ops):
            tasks['can_parallel'] = True
            if not tasks['reason']:
                tasks['reason'] = "检测到独立操作关键词"
        
        return tasks
    
    def _extract_subtasks(self, request: str) -> List[str]:
        """从请求中提取子任务"""
        # 简单的句子分割
        import re
        sentences = re.split(r'[。；;]', request)
        return [s.strip() for s in sentences if len(s.strip()) > 10]
    
    def get_execution_strategy(self, tasks: Dict) -> str:
        """返回执行策略建议"""
        if tasks['can_parallel'] and len(tasks['subtasks']) >= 2:
            return f"""
🔀 **并行执行建议**
- 检测到 {len(tasks['subtasks'])} 个可并行子任务
- 建议使用 sessions_spawn 同时处理
- 预计节省时间: {(len(tasks['subtasks'])-1) * 30}%
"""
        return "🔧 串行执行（任务间有依赖关系）"

# 全局调度器实例
task_scheduler = TaskScheduler()
