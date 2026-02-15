#!/usr/bin/env python3
"""
林林v5.0 预判引擎主流程集成脚本
版本: v5.0
职责: 自动修改现有主流程以集成预判引擎

修改内容:
1. 导入预判引擎模块
2. 在对话前后添加预判调用
3. 添加反馈收集机制
4. 添加配置管理
"""

import os
import sys
import ast
import re
from pathlib import Path


class PredictionIntegrationPatcher:
    """
    预判引擎集成补丁工具
    自动修改现有主流程文件
    """
    
    # 需要添加的导入语句
    IMPORTS = """
# ========== 预判引擎集成 v5.0 ==========
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.prediction_integration import (
    PredictionIntegration, PredictionResult, PredictionTriggerType
)
from scripts.realtime_predictor import RealtimePredictor
# =========================================
"""
    
    # 需要添加的初始化代码
    INIT_CODE = """
    # ========== 预判引擎初始化 v5.0 ==========
    self._prediction_predictor: Optional[RealtimePredictor] = None
    self._prediction_enabled = True
    self._prediction_min_confidence = 0.75
    # =========================================
"""
    
    # 需要添加的方法
    PREDICTION_METHODS = '''
    # ========== 预判引擎方法 v5.0 ==========
    async def initialize_prediction(self, data_dir: str = "data"):
        """初始化预判系统"""
        if not self._prediction_enabled:
            return
        
        self._prediction_predictor = RealtimePredictor(data_dir)
        await self._prediction_predictor.start()
        
        # 设置回调
        self._prediction_predictor.set_callbacks(
            on_suggestion=self._on_prediction_suggestion,
            on_trigger=self._on_prediction_trigger
        )
        
        print("[预判引擎] 已初始化")
    
    async def shutdown_prediction(self):
        """关闭预判系统"""
        if self._prediction_predictor:
            await self._prediction_predictor.stop()
            print("[预判引擎] 已关闭")
    
    async def _check_prediction_suggestions(self) -> Optional[List[PredictionResult]]:
        """检查预判建议"""
        if not self._prediction_predictor or not self._prediction_enabled:
            return None
        
        # 获取主动建议
        suggestions = await self._prediction_predictor.prediction_integration.generate_proactive_suggestions()
        
        # 过滤低置信度
        return [s for s in suggestions if s.confidence >= self._prediction_min_confidence]
    
    async def _analyze_conversation_for_prediction(self, conversation: Dict, context: Optional[Dict] = None):
        """分析对话并生成预测"""
        if not self._prediction_predictor or not self._prediction_enabled:
            return
        
        await self._prediction_predictor.on_conversation_end(conversation, context)
    
    def _on_prediction_suggestion(self, suggestions: List[PredictionResult]):
        """收到预测建议时的回调"""
        # 子类可以覆盖此方法处理建议
        pass
    
    def _on_prediction_trigger(self, event_type, predictions: List[PredictionResult]):
        """预测触发时的回调"""
        pass
    
    def record_prediction_feedback(self, prediction_id: str, was_accurate: bool, 
                                   actual_need: Optional[str] = None, was_accepted: bool = False):
        """记录预测反馈"""
        if self._prediction_predictor:
            self._prediction_predictor.record_feedback(prediction_id, was_accurate, actual_need, was_accepted)
    
    def set_prediction_config(self, enabled: bool = None, min_confidence: float = None):
        """设置预判配置"""
        if enabled is not None:
            self._prediction_enabled = enabled
        if min_confidence is not None:
            self._prediction_min_confidence = min_confidence
            if self._prediction_predictor:
                self._prediction_predictor.update_config(min_confidence_for_proactive=min_confidence)
    
    def get_prediction_stats(self) -> Dict:
        """获取预测统计"""
        if self._prediction_predictor:
            return self._prediction_predictor.get_stats()
        return {}
    # =========================================
'''
    
    def __init__(self, target_file: str):
        self.target_file = target_file
        self.backup_file = f"{target_file}.backup"
    
    def analyze(self) -> Dict:
        """分析目标文件"""
        if not os.path.exists(self.target_file):
            return {"error": "文件不存在"}
        
        with open(self.target_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            return {"error": f"语法错误: {e}"}
        
        # 查找类定义
        classes = []
        has_init = False
        has_process_message = False
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        if item.name == "__init__":
                            has_init = True
                        elif item.name in ["process", "process_message", "handle", "handle_message"]:
                            has_process_message = True
        
        return {
            "classes": classes,
            "has_init": has_init,
            "has_process_message": has_process_message,
            "line_count": len(content.split('\n'))
        }
    
    def patch(self) -> bool:
        """执行补丁"""
        if not os.path.exists(self.target_file):
            print(f"错误: 文件不存在 {self.target_file}")
            return False
        
        # 创建备份
        with open(self.target_file, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        with open(self.backup_file, 'w', encoding='utf-8') as f:
            f.write(original_content)
        
        print(f"已创建备份: {self.backup_file}")
        
        # 执行修改
        modified_content = original_content
        
        # 1. 添加导入
        modified_content = self._add_imports(modified_content)
        
        # 2. 修改初始化方法
        modified_content = self._modify_init(modified_content)
        
        # 3. 添加预判方法
        modified_content = self._add_prediction_methods(modified_content)
        
        # 4. 修改处理流程
        modified_content = self._modify_process_flow(modified_content)
        
        # 保存修改
        with open(self.target_file, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        print(f"已修改文件: {self.target_file}")
        return True
    
    def _add_imports(self, content: str) -> str:
        """添加导入语句"""
        # 查找导入部分
        lines = content.split('\n')
        import_idx = 0
        
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                import_idx = i + 1
        
        # 检查是否已存在
        if 'PredictionIntegration' in content:
            print("导入已存在，跳过")
            return content
        
        # 插入导入
        lines.insert(import_idx, self.IMPORTS)
        return '\n'.join(lines)
    
    def _modify_init(self, content: str) -> str:
        """修改初始化方法"""
        # 查找 __init__ 方法
        pattern = r'(def __init__\(self[^)]*\):)'
        
        def add_init_code(match):
            return match.group(1) + self.INIT_CODE
        
        # 检查是否已存在
        if '_prediction_predictor' in content:
            print("初始化代码已存在，跳过")
            return content
        
        modified = re.sub(pattern, add_init_code, content)
        return modified
    
    def _add_prediction_methods(self, content: str) -> str:
        """添加预判方法"""
        # 检查是否已存在
        if 'initialize_prediction' in content:
            print("预判方法已存在，跳过")
            return content
        
        # 在文件末尾添加
        return content + '\n' + self.PREDICTION_METHODS
    
    def _modify_process_flow(self, content: str) -> str:
        """修改处理流程"""
        # 这是一个简化的实现，实际可能需要更复杂的AST操作
        # 这里只是添加注释提示用户手动集成
        
        hint = '''
# ========== 预判引擎集成提示 v5.0 ==========
# 请在 process/process_message/handle 方法中添加以下调用:
#
# async def process_message(self, message, ...):
#     # 1. 对话前检查预判建议
#     suggestions = await self._check_prediction_suggestions()
#     if suggestions:
#         # 处理建议...
#         pass
#     
#     # 2. 处理消息
#     response = await self._process_message_core(message, ...)
#     
#     # 3. 对话后分析
#     conversation = {
#         "timestamp": datetime.now().isoformat(),
#         "content": message,
#         "response": response
#     }
#     await self._analyze_conversation_for_prediction(conversation, context)
#     
#     return response
# =========================================
'''
        
        if '预判引擎集成提示' in content:
            return content
        
        return content + '\n' + hint
    
    def restore(self) -> bool:
        """恢复备份"""
        if not os.path.exists(self.backup_file):
            print(f"备份文件不存在: {self.backup_file}")
            return False
        
        with open(self.backup_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        with open(self.target_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"已恢复备份: {self.target_file}")
        return True


def patch_main_flow(file_path: str, auto_confirm: bool = False) -> bool:
    """
    修改主流程文件以集成预判引擎
    
    Args:
        file_path: 主流程文件路径
        auto_confirm: 是否自动确认
        
    Returns:
        是否成功
    """
    patcher = PredictionIntegrationPatcher(file_path)
    
    # 分析文件
    analysis = patcher.analyze()
    print(f"\n文件分析结果:")
    print(f"  类: {analysis.get('classes', [])}")
    print(f"  有__init__: {analysis.get('has_init', False)}")
    print(f"  有process_message: {analysis.get('has_process_message', False)}")
    print(f"  行数: {analysis.get('line_count', 0)}")
    
    if "error" in analysis:
        print(f"错误: {analysis['error']}")
        return False
    
    # 确认
    if not auto_confirm:
        confirm = input("\n确认修改? (y/n): ")
        if confirm.lower() != 'y':
            print("已取消")
            return False
    
    # 执行补丁
    return patcher.patch()


# ========== 手动集成指南 ==========

MANUAL_INTEGRATION_GUIDE = """
# 手动集成指南

## 方案1: 最小改动集成（推荐）

在现有的主流程类中添加以下代码:

```python
# 1. 导入（添加到文件顶部）
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.prediction_integration import PredictionIntegration, PredictionResult
from scripts.realtime_predictor import RealtimePredictor

# 2. 初始化（添加到 __init__ 方法）
async def __init__(self):
    # ... 原有代码 ...
    
    # 预判引擎初始化
    self._predictor = RealtimePredictor()
    await self._predictor.start()
    self._predictor.set_callbacks(
        on_suggestion=self._handle_suggestions
    )

# 3. 对话前检查（添加到 process_message 开头）
async def process_message(self, message, ...):
    # 检查预判建议
    suggestions = await self._predictor.prediction_integration.generate_proactive_suggestions()
    for s in suggestions:
        if s.confidence >= 0.75:
            print(f"🤖 建议: {s.suggested_action}")
    
    # ... 原有处理逻辑 ...
    
    # 对话后分析（添加到 process_message 结尾）
    conversation = {
        "timestamp": datetime.now().isoformat(),
        "content": message,
        "response": response
    }
    await self._predictor.on_conversation_end(conversation)
    
    return response

# 4. 反馈收集（添加反馈处理）
def on_user_accept_suggestion(self, prediction_id):
    self._predictor.record_feedback(prediction_id, was_accurate=True, was_accepted=True)

def on_user_reject_suggestion(self, prediction_id, actual_need=None):
    self._predictor.record_feedback(prediction_id, was_accurate=False, 
                                     actual_need=actual_need, was_accepted=False)
```

## 方案2: 使用包装类

```python
from core.main_flow_integration import PredictionEnabledMainFlow

class MyMainFlow(PredictionEnabledMainFlow):
    async def process_user_message(self, message, context=None):
        # 你的消息处理逻辑
        return "response"

# 使用
flow = MyMainFlow()
await flow.initialize()
result = await flow.process_message("你好")
```

## 方案3: 装饰器模式

```python
from core.main_flow_integration import enable_prediction

@enable_prediction()
class MyMainFlow:
    async def process(self, message):
        return "response"

# 使用
flow = MyMainFlow()
await flow.initialize_prediction()
result = await flow.process_with_prediction("你好")
```

## 配置选项

```python
# 调整预判灵敏度
flow.set_prediction_config(
    enabled=True,           # 启用/禁用预判
    min_confidence=0.75     # 最小置信度阈值
)

# 获取统计
stats = flow.get_prediction_stats()
```
"""


def print_integration_guide():
    """打印集成指南"""
    print(MANUAL_INTEGRATION_GUIDE)


# ========== 演示 ==========

def demo():
    """演示补丁工具"""
    print("=" * 60)
    print("林林v5.0 预判引擎主流程集成工具")
    print("=" * 60)
    
    # 创建一个示例文件
    example_file = "/tmp/example_main_flow.py"
    example_content = '''#!/usr/bin/env python3
import asyncio
from datetime import datetime

class ExampleMainFlow:
    def __init__(self):
        self.name = "Example"
    
    async def process_message(self, message: str, user_id: str = "default"):
        print(f"处理消息: {message}")
        return f"回复: {message}"

if __name__ == "__main__":
    flow = ExampleMainFlow()
    result = asyncio.run(flow.process_message("你好"))
    print(result)
'''
    
    with open(example_file, 'w') as f:
        f.write(example_content)
    
    print(f"\n创建示例文件: {example_file}")
    
    # 分析文件
    patcher = PredictionIntegrationPatcher(example_file)
    analysis = patcher.analyze()
    
    print(f"\n分析结果:")
    print(f"  类: {analysis.get('classes')}")
    print(f"  有__init__: {analysis.get('has_init')}")
    print(f"  有process_message: {analysis.get('has_process_message')}")
    
    # 执行补丁
    print("\n执行补丁...")
    patcher.patch()
    
    # 显示修改后的内容
    print("\n修改后的文件内容（前50行）:")
    with open(example_file, 'r') as f:
        lines = f.readlines()[:50]
        for i, line in enumerate(lines, 1):
            print(f"{i:3d}: {line.rstrip()}")
    
    # 显示手动集成指南
    print("\n" + "=" * 60)
    print("手动集成指南:")
    print("=" * 60)
    print_integration_guide()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--guide":
            print_integration_guide()
        elif sys.argv[1] == "--patch" and len(sys.argv) > 2:
            patch_main_flow(sys.argv[2], auto_confirm="--yes" in sys.argv)
        else:
            print("用法:")
            print("  python integrate_prediction.py --guide              # 显示集成指南")
            print("  python integrate_prediction.py --patch <文件>       # 自动修改文件")
            print("  python integrate_prediction.py --patch <文件> --yes # 自动确认")
    else:
        demo()
