#!/usr/bin/env python3
"""
Neural Hub - Closed Loop Processing System
神经中枢闭环处理系统

完整的处理闭环:
输入 → 分析 → 决策 → 执行/路由 → 反馈 → 再分析 → ... → 输出
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/core')

from feedback_processor import FeedbackProcessor, NeuralSignal, InputSource
from datetime import datetime

class NeuralHubLoop:
    """神经中枢闭环系统"""
    
    def __init__(self):
        self.processor = FeedbackProcessor()
        self.loop_count = 0
        self.max_loops = 5  # 防止无限循环
    
    def process_closed_loop(self, initial_signal: NeuralSignal) -> dict:
        """
        闭环处理主函数
        
        可能的闭环路径:
        1. 用户请求 → 小弟执行 → 结果OK → 我汇总 → 返回用户
        2. 用户请求 → 小弟执行 → 失败 → 我决策 → 重试/转给其他小弟 → 成功 → 返回
        3. 用户请求 → 我分析 → 需要深度思考 → Multi-Agent → 决策 → 小弟执行 → 返回
        4. 小弟反馈 → 我分析 → 需要补充 → 交给其他小弟 → 汇总 → 返回
        """
        
        current_signal = initial_signal
        processing_chain = []
        
        print(f"\n{'='*70}")
        print(f"🧠 神经中枢闭环处理开始")
        print(f"{'='*70}")
        print(f"初始输入: [{current_signal.source.value}] {current_signal.content[:50]}...")
        
        while self.loop_count < self.max_loops:
            self.loop_count += 1
            
            # 1. 分析当前信号
            result = self.processor.process(current_signal)
            processing_chain.append(result)
            
            print(f"\n--- 循环 {self.loop_count} ---")
            print(f"处理模式: {result['processing_mode']}")
            if result['target_node']:
                print(f"目标节点: {result['target_node']}")
            print(f"决策原因: {result['reason']}")
            
            # 2. 根据处理模式决定下一步
            mode = result['processing_mode']
            
            if mode == 'quick':
                # 我快速响应，闭环结束
                print(f"✅ 我快速响应，闭环完成")
                break
                
            elif mode == 'deep':
                # 需要Multi-Agent深度分析
                print(f"🧠 触发Multi-Agent深度分析...")
                # 模拟深度分析结果
                analysis_result = "深度分析完成，得出决策..."
                
                # 生成新的信号继续处理
                current_signal = NeuralSignal(
                    signal_id=f"sig_deep_{self.loop_count}",
                    source=InputSource.SELF_REFLECTION,
                    content=analysis_result,
                    context={"depth": "multi_agent", "step": self.loop_count},
                    timestamp=datetime.now().isoformat()
                )
                
            elif mode == 'delegate':
                # 交给小弟执行
                target = result['target_node']
                print(f"📤 交给小弟 {target} 执行...")
                
                # 模拟小弟执行结果
                import random
                if random.random() > 0.3:  # 70%成功率
                    node_result = f"小弟{target}执行成功，结果数据..."
                    node_status = "success"
                else:
                    node_result = f"小弟{target}执行失败，网络超时"
                    node_status = "failed"
                
                # 生成小弟反馈信号
                current_signal = NeuralSignal(
                    signal_id=f"sig_node_{self.loop_count}",
                    source=InputSource.NODE_FEEDBACK,
                    content=node_result,
                    context={
                        "node_id": target,
                        "status": node_status,
                        "error_type": "timeout" if node_status == "failed" else None,
                        "retry_count": self.loop_count - 1
                    },
                    timestamp=datetime.now().isoformat()
                )
                
            elif mode == 'retry':
                # 重试
                target = result['target_node']
                print(f"🔄 命令小弟 {target} 重试...")
                
                # 模拟重试
                current_signal = NeuralSignal(
                    signal_id=f"sig_retry_{self.loop_count}",
                    source=InputSource.SYSTEM_EVENT,
                    content=f"命令{target}重试任务",
                    context={"action": "retry", "target": target},
                    timestamp=datetime.now().isoformat()
                )
                
            elif mode == 'route':
                # 转给其他小弟
                target = result['target_node']
                print(f"🔄 转给小弟 {target} 执行...")
                
                current_signal = NeuralSignal(
                    signal_id=f"sig_route_{self.loop_count}",
                    source=InputSource.SYSTEM_EVENT,
                    content=f"任务转给{target}",
                    context={"action": "route", "target": target},
                    timestamp=datetime.now().isoformat()
                )
        
        # 闭环结束，生成最终结果
        final_output = {
            "initial_input": initial_signal.content,
            "processing_chain": processing_chain,
            "loop_count": self.loop_count,
            "final_result": f"闭环处理完成，共经历{self.loop_count}轮处理",
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"\n{'='*70}")
        print(f"✅ 闭环处理完成")
        print(f"总循环次数: {self.loop_count}")
        print(f"处理链路: {' → '.join([p['processing_mode'] for p in processing_chain])}")
        print(f"{'='*70}\n")
        
        return final_output

def demo():
    """演示闭环处理"""
    
    scenarios = [
        {
            "name": "场景1: 简单任务 - 一次完成",
            "signal": NeuralSignal(
                signal_id="demo_001",
                source=InputSource.USER,
                content="搜索最新的AI论文",
                context={},
                timestamp=datetime.now().isoformat()
            )
        },
        {
            "name": "场景2: 复杂决策 - 需要深度分析",
            "signal": NeuralSignal(
                signal_id="demo_002",
                source=InputSource.USER,
                content="帮我分析为什么选择微服务架构而不是单体架构？考虑扩展性、维护成本、团队规模等多个维度。",
                context={},
                timestamp=datetime.now().isoformat()
            )
        },
        {
            "name": "场景3: 小弟失败 - 需要重试",
            "signal": NeuralSignal(
                signal_id="demo_003",
                source=InputSource.NODE_FEEDBACK,
                content="执行失败，网络超时",
                context={
                    "node_id": "NB02",
                    "status": "failed",
                    "error_type": "timeout",
                    "retry_count": 0
                },
                timestamp=datetime.now().isoformat()
            )
        }
    ]
    
    hub = NeuralHubLoop()
    
    for scenario in scenarios:
        print(f"\n{'='*70}")
        print(f"🎯 {scenario['name']}")
        print(f"{'='*70}")
        
        # 重置计数器
        hub.loop_count = 0
        
        # 执行闭环
        result = hub.process_closed_loop(scenario['signal'])
        
        print(f"\n处理结果: {result['final_result']}")

if __name__ == "__main__":
    demo()
