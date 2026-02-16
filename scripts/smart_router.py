#!/usr/bin/env python3
# 智能路由Python模块
# 用于Cron任务和Python脚本内部调用

import subprocess
import json

class SmartRouter:
    """智能路由类 - 根据任务自动选择模型和thinking模式"""

    def __init__(self):
        self.router_script = "/root/.openclaw/workspace/scripts/smart-router-unified.sh"

    def route(self, task_description: str, current_model: str = "ds") -> dict:
        """
        执行智能路由分析

        Args:
            task_description: 任务描述
            current_model: 当前模型

        Returns:
            dict: {
                "model": "ds/kimi/glm/k2p5",
                "full_model": "完整模型路径",
                "thinking": "off/concise/on/stream",
                "difficulty": "L1/L2/L3/L4/L5",
                "reason": "原因说明"
            }
        """
        try:
            # 调用shell脚本
            result = subprocess.run(
                [self.router_script, task_description, current_model],
                capture_output=True,
                text=True,
                timeout=5
            )

            # 解析输出
            output = result.stdout

            # 提取关键信息
            model = self._extract_line(output, "建议:")
            thinking = self._extract_line(output, "Thinking模式:")
            reason = self._extract_line(output, "原因:")

            # 映射到完整模型路径
            full_model = self._get_full_model(model)

            return {
                "model": model,
                "full_model": full_model,
                "thinking": thinking,
                "reason": reason,
                "success": True
            }

        except Exception as e:
            # 失败时返回默认配置
            return {
                "model": "ds",
                "full_model": "nvidia-build/deepseek-ai/deepseek-v3.2",
                "thinking": "off",
                "reason": f"路由失败，使用默认: {str(e)}",
                "success": False
            }

    def _extract_line(self, text: str, prefix: str) -> str:
        """从文本中提取特定前缀的行"""
        for line in text.split('\n'):
            if prefix in line:
                return line.split(':')[1].strip()
        return "unknown"

    def _get_full_model(self, model: str) -> str:
        """映射模型别名到完整路径"""
        mapping = {
            "ds": "nvidia-build/deepseek-ai/deepseek-v3.2",
            "kimi": "nvidia-build/moonshotai/kimi-k2.5",
            "glm": "nvidia-build/z-ai/glm4.7",
            "k2p5": "kimi-coding/k2p5"
        }
        return mapping.get(model, "nvidia-build/deepseek-ai/deepseek-v3.2")

    def route_by_signal(self, signal_score: int) -> dict:
        """
        根据Signal评分快速路由（用于Cron任务内部）

        Args:
            signal_score: Signal评分 (1-10)

        Returns:
            dict: 模型和thinking配置
        """
        if signal_score >= 9:
            return {
                "model": "k2p5",
                "full_model": "kimi-coding/k2p5",
                "thinking": "stream",
                "reason": f"Signal {signal_score} - 高价值，最强模型+流式思考"
            }
        elif signal_score >= 7:
            return {
                "model": "kimi",
                "full_model": "nvidia-build/moonshotai/kimi-k2.5",
                "thinking": "on",
                "reason": f"Signal {signal_score} - 中高价值，kimi完整思考"
            }
        elif signal_score >= 5:
            return {
                "model": "ds",
                "full_model": "nvidia-build/deepseek-ai/deepseek-v3.2",
                "thinking": "concise",
                "reason": f"Signal {signal_score} - 中等价值，ds精简思考"
            }
        else:
            return {
                "model": "ds",
                "full_model": "nvidia-build/deepseek-ai/deepseek-v3.2",
                "thinking": "off",
                "reason": f"Signal {signal_score} - 低价值，基础处理"
            }


# 便捷函数
def smart_route(task: str, current_model: str = "ds") -> dict:
    """快捷路由函数"""
    router = SmartRouter()
    return router.route(task, current_model)

def route_by_signal(signal: int) -> dict:
    """根据Signal评分路由"""
    router = SmartRouter()
    return router.route_by_signal(signal)


if __name__ == "__main__":
    # 测试
    print("=== 测试智能路由 ===")
    print()

    # 测试1: 任务描述路由
    result = smart_route("设计一个高并发的微服务架构")
    print("任务: 设计高并发微服务架构")
    print(f"模型: {result['model']} ({result['full_model']})")
    print(f"Thinking: {result['thinking']}")
    print(f"原因: {result['reason']}")
    print()

    # 测试2: Signal评分路由
    print("=== 测试Signal路由 ===")
    for signal in [4, 7, 10]:
        result = route_by_signal(signal)
        print(f"Signal {signal}: {result['model']} + {result['thinking']}")
