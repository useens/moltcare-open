#!/usr/bin/env python3
"""
林林v5.0 主流程预判集成 (Main Flow Prediction Integration)
版本: v5.0
职责: 将预判引擎集成到主对话流程中

集成点:
1. 对话前 - 检查是否有待处理的主动建议
2. 对话后 - 分析对话并触发预测
3. 定时 - 运行定时预测检查
4. 事件 - 响应外部事件触发预测
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.prediction_integration import (
    PredictionIntegration, PredictionResult, PredictionTriggerType
)
from scripts.realtime_predictor import (
    RealtimePredictor, get_predictor, start_prediction_service, stop_prediction_service
)


class PredictionEnabledMainFlow:
    """
    启用预判功能的主流程
    包装现有主流程，添加预判能力
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.predictor: Optional[RealtimePredictor] = None
        self.pending_suggestions: List[PredictionResult] = []
        self.suggestion_shown: set = set()
        
        # 配置
        self.auto_show_suggestions = True
        self.min_confidence_to_show = 0.75
        self.max_suggestions_per_turn = 2
        
        # 统计
        self.stats = {
            "total_predictions": 0,
            "shown_suggestions": 0,
            "accepted_suggestions": 0,
            "rejected_suggestions": 0
        }
    
    async def initialize(self):
        """初始化预判系统"""
        self.predictor = await start_prediction_service(self.data_dir)
        
        # 设置回调
        self.predictor.set_callbacks(
            on_suggestion=self._on_suggestion_received,
            on_trigger=self._on_trigger_received
        )
        
        print("[预判集成] 预判系统已初始化")
    
    async def shutdown(self):
        """关闭预判系统"""
        await stop_prediction_service()
        print("[预判集成] 预判系统已关闭")
    
    # ========== 对话流程集成 ==========
    
    async def before_conversation(self) -> Optional[List[PredictionResult]]:
        """
        对话前调用
        返回待处理的主动建议
        """
        if not self.pending_suggestions:
            return None
        
        # 过滤已显示的建议
        new_suggestions = [
            s for s in self.pending_suggestions 
            if s.prediction_id not in self.suggestion_shown
            and s.confidence >= self.min_confidence_to_show
        ]
        
        # 限制数量
        suggestions_to_show = new_suggestions[:self.max_suggestions_per_turn]
        
        # 标记为已显示
        for s in suggestions_to_show:
            self.suggestion_shown.add(s.prediction_id)
            self.stats["shown_suggestions"] += 1
        
        # 清空待处理列表
        self.pending_suggestions = []
        
        return suggestions_to_show if suggestions_to_show else None
    
    async def after_conversation(self, conversation: Dict, 
                                 context: Optional[Dict] = None) -> List[PredictionResult]:
        """
        对话后调用
        分析对话并生成预测
        """
        if not self.predictor:
            return []
        
        predictions = await self.predictor.on_conversation_end(conversation, context)
        self.stats["total_predictions"] += len(predictions)
        
        return predictions
    
    async def process_message(self, message: str, user_id: str = "default",
                             context: Optional[Dict] = None) -> Dict:
        """
        处理用户消息的主流程
        集成预判功能
        """
        results = {
            "message": message,
            "suggestions_before": [],
            "suggestions_after": [],
            "response": "",
            "prediction_stats": {}
        }
        
        # 1. 对话前 - 检查主动建议
        if self.auto_show_suggestions:
            before_suggestions = await self.before_conversation()
            if before_suggestions:
                results["suggestions_before"] = [s.to_dict() for s in before_suggestions]
                self._display_suggestions(before_suggestions, "对话前建议")
        
        # 2. 处理消息（这里是实际的消息处理逻辑）
        # 在实际集成中，这里会调用现有的主处理逻辑
        results["response"] = await self._process_message_core(message, context)
        
        # 3. 对话后 - 分析并预测
        conversation = {
            "timestamp": datetime.now().isoformat(),
            "content": message,
            "user_id": user_id,
            "response": results["response"]
        }
        
        after_predictions = await self.after_conversation(conversation, context)
        if after_predictions:
            results["suggestions_after"] = [p.to_dict() for p in after_predictions[:3]]
        
        results["prediction_stats"] = self.stats.copy()
        
        return results
    
    async def _process_message_core(self, message: str, 
                                    context: Optional[Dict] = None) -> str:
        """
        核心消息处理
        在实际集成中，这里应该调用现有的主处理逻辑
        """
        # 模拟响应
        return f"已收到消息: {message[:50]}..."
    
    # ========== 回调处理 ==========
    
    def _on_suggestion_received(self, suggestions: List[PredictionResult]):
        """收到建议时的回调"""
        # 添加到待处理列表
        for s in suggestions:
            if s.confidence >= self.min_confidence_to_show:
                self.pending_suggestions.append(s)
        
        # 限制待处理列表大小
        self.pending_suggestions = sorted(
            self.pending_suggestions, 
            key=lambda x: x.confidence, 
            reverse=True
        )[:10]
    
    def _on_trigger_received(self, event_type, predictions: List[PredictionResult]):
        """触发事件时的回调"""
        print(f"[预判集成] 事件 {event_type.value} 触发 {len(predictions)} 个预测")
    
    def _display_suggestions(self, suggestions: List[PredictionResult], 
                            title: str = "建议"):
        """显示建议（可自定义输出方式）"""
        print(f"\n{'='*40}")
        print(f"🤖 {title}")
        print('='*40)
        
        for i, s in enumerate(suggestions, 1):
            print(f"\n{i}. {s.predicted_need} (置信度: {s.confidence:.0%})")
            print(f"   💡 {s.suggested_action}")
            print(f"   📝 {s.reason}")
        
        print(f"\n{'='*40}\n")
    
    # ========== 反馈接口 ==========
    
    def accept_suggestion(self, prediction_id: str):
        """用户接受了建议"""
        self.stats["accepted_suggestions"] += 1
        if self.predictor:
            self.predictor.record_feedback(
                prediction_id, 
                was_accurate=True, 
                was_accepted=True
            )
        print(f"[预判集成] 建议 {prediction_id} 已接受")
    
    def reject_suggestion(self, prediction_id: str, actual_need: Optional[str] = None):
        """用户拒绝了建议"""
        self.stats["rejected_suggestions"] += 1
        if self.predictor:
            self.predictor.record_feedback(
                prediction_id, 
                was_accurate=False, 
                actual_need=actual_need,
                was_accepted=False
            )
        print(f"[预判集成] 建议 {prediction_id} 已拒绝")
    
    # ========== 配置接口 ==========
    
    def update_config(self, **kwargs):
        """更新配置"""
        if "auto_show_suggestions" in kwargs:
            self.auto_show_suggestions = kwargs["auto_show_suggestions"]
        if "min_confidence_to_show" in kwargs:
            self.min_confidence_to_show = kwargs["min_confidence_to_show"]
        if "max_suggestions_per_turn" in kwargs:
            self.max_suggestions_per_turn = kwargs["max_suggestions_per_turn"]
        
        # 更新底层预测器配置
        if self.predictor:
            self.predictor.update_config(**kwargs)
        
        print(f"[预判集成] 配置已更新: {kwargs}")
    
    def get_config(self) -> Dict:
        """获取配置"""
        return {
            "auto_show_suggestions": self.auto_show_suggestions,
            "min_confidence_to_show": self.min_confidence_to_show,
            "max_suggestions_per_turn": self.max_suggestions_per_turn,
            "predictor_config": self.predictor.get_config() if self.predictor else None
        }
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        stats = self.stats.copy()
        if self.predictor:
            stats["predictor_stats"] = self.predictor.get_stats()
        return stats


# ========== 装饰器模式集成 ==========

def enable_prediction(data_dir: str = "data"):
    """
    启用预判功能的装饰器
    用于包装现有的主流程类
    
    示例:
        @enable_prediction()
        class MyMainFlow:
            async def process(self, message):
                return "response"
    """
    def decorator(cls):
        class PredictionEnabledClass(cls):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._prediction_flow = PredictionEnabledMainFlow(data_dir)
                self._prediction_initialized = False
            
            async def initialize_prediction(self):
                """初始化预判系统"""
                await self._prediction_flow.initialize()
                self._prediction_initialized = True
            
            async def shutdown_prediction(self):
                """关闭预判系统"""
                await self._prediction_flow.shutdown()
                self._prediction_initialized = False
            
            async def process_with_prediction(self, message: str, 
                                            user_id: str = "default",
                                            context: Optional[Dict] = None) -> Dict:
                """集成预判的消息处理"""
                if not self._prediction_initialized:
                    await self.initialize_prediction()
                
                return await self._prediction_flow.process_message(
                    message, user_id, context
                )
            
            async def get_prediction_suggestions(self) -> Optional[List[PredictionResult]]:
                """获取主动建议"""
                if not self._prediction_initialized:
                    return None
                return await self._prediction_flow.before_conversation()
            
            def accept_prediction(self, prediction_id: str):
                """接受预测建议"""
                self._prediction_flow.accept_suggestion(prediction_id)
            
            def reject_prediction(self, prediction_id: str, 
                                 actual_need: Optional[str] = None):
                """拒绝预测建议"""
                self._prediction_flow.reject_suggestion(prediction_id, actual_need)
        
        return PredictionEnabledClass
    return decorator


# ========== 现有主流程修改指南 ==========

MAIN_FLOW_INTEGRATION_GUIDE = """
# 现有主流程集成指南

## 方案1: 继承模式（推荐）

```python
from core.prediction_integration import PredictionEnabledMainFlow

class MyMainFlow(PredictionEnabledMainFlow):
    async def __init__(self):
        await super().initialize()
        # 你的初始化代码
    
    async def handle_message(self, message, user_id="default"):
        # 1. 检查主动建议
        suggestions = await self.before_conversation()
        if suggestions:
            # 处理建议...
            pass
        
        # 2. 处理消息
        response = await self.process_user_message(message)
        
        # 3. 对话后分析
        conversation = {
            "timestamp": datetime.now().isoformat(),
            "content": message,
            "response": response
        }
        await self.after_conversation(conversation)
        
        return response
```

## 方案2: 组合模式

```python
from core.prediction_integration import PredictionEnabledMainFlow

class MyMainFlow:
    def __init__(self):
        self.prediction = PredictionEnabledMainFlow()
    
    async def initialize(self):
        await self.prediction.initialize()
    
    async def handle_message(self, message):
        # 使用集成的方法
        result = await self.prediction.process_message(message)
        return result["response"]
```

## 方案3: 装饰器模式

```python
from core.prediction_integration import enable_prediction

@enable_prediction()
class MyMainFlow:
    async def process(self, message):
        return "response"

# 使用
flow = MyMainFlow()
await flow.initialize_prediction()
result = await flow.process_with_prediction("你好")
```

## 集成点说明

1. **初始化时**: 调用 `await prediction.initialize()`
2. **对话前**: 调用 `await prediction.before_conversation()` 获取主动建议
3. **对话后**: 调用 `await prediction.after_conversation(conversation)` 分析对话
4. **关闭时**: 调用 `await prediction.shutdown()`

## 反馈收集

```python
# 用户接受建议
prediction.accept_suggestion(prediction_id)

# 用户拒绝建议
prediction.reject_suggestion(prediction_id, actual_need="真实需求")
```
"""


# ========== 演示 ==========

async def demo():
    """演示主流程集成"""
    print("=" * 60)
    print("林林v5.0 主流程预判集成 v5.0 演示")
    print("=" * 60)
    
    # 创建集成流程
    flow = PredictionEnabledMainFlow()
    await flow.initialize()
    
    # 演示1: 处理消息
    print("\n[演示1] 处理用户消息...")
    result = await flow.process_message(
        "帮我总结一下昨天的邮件",
        user_id="user1",
        context={
            "emails": [
                {"id": "em1", "subject": "项目更新", "unread": True},
                {"id": "em2", "subject": "会议邀请", "unread": True},
            ]
        }
    )
    
    print(f"响应: {result['response']}")
    if result['suggestions_before']:
        print(f"对话前建议: {len(result['suggestions_before'])} 个")
    if result['suggestions_after']:
        print(f"对话后预测: {len(result['suggestions_after'])} 个")
    
    # 演示2: 模拟用户反馈
    print("\n[演示2] 用户反馈...")
    if result['suggestions_after']:
        pred_id = result['suggestions_after'][0]['prediction_id']
        flow.accept_suggestion(pred_id)
    
    # 演示3: 显示统计
    print("\n[演示3] 统计信息...")
    stats = flow.get_stats()
    print(f"总预测数: {stats['total_predictions']}")
    print(f"已显示建议: {stats['shown_suggestions']}")
    print(f"已接受: {stats['accepted_suggestions']}")
    print(f"已拒绝: {stats['rejected_suggestions']}")
    
    # 关闭
    await flow.shutdown()
    
    # 显示集成指南
    print("\n" + "=" * 60)
    print("集成指南:")
    print("=" * 60)
    print(MAIN_FLOW_INTEGRATION_GUIDE)
    
    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(demo())
