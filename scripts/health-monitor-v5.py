#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
林林 v5.0 诊断修复主控脚本
整合self-diagnosis.py和auto-heal.py，每10分钟运行一次

用法: 通过crontab运行: */10 * * * * /usr/bin/python3 /root/.openclaw/workspace/scripts/health-monitor-v5.py
"""

import os
import sys
import json
import time
import logging
import subprocess
from datetime import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/.openclaw/workspace/logs/health-monitor-v5.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('health-monitor-v5')

WORKSPACE = Path('/root/.openclaw/workspace')
DATA_DIR = WORKSPACE / 'data'
NOTIFICATION_LOG = DATA_DIR / 'notifications.jsonl'

class HealthMonitorV5:
    """健康监控主控类"""
    
    def __init__(self):
        self.diagnosis_script = WORKSPACE / 'scripts' / 'self-diagnosis.py'
        self.heal_script = WORKSPACE / 'scripts' / 'auto-heal.py'
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    def run(self):
        """执行完整的诊断和修复流程"""
        logger.info("=" * 70)
        logger.info("林林 v5.0 健康监控系统启动")
        logger.info("=" * 70)
        
        start_time = time.time()
        
        # 步骤1: 运行诊断
        diagnosis_result = self._run_diagnosis()
        
        if not diagnosis_result:
            logger.error("诊断执行失败，跳过修复")
            return False
        
        # 步骤2: 根据诊断结果决定是否需要修复
        status = diagnosis_result.get('overall_status', 'unknown')
        score = diagnosis_result.get('overall_score', 0)
        
        logger.info(f"诊断结果: 状态={status}, 分数={score:.1f}")
        
        # 步骤3: 如果需要，执行自动修复
        heal_report = None
        if status in ['warning', 'critical'] or score < 70:
            logger.info("系统状态需要修复，启动自动修复...")
            heal_report = self._run_heal(diagnosis_result)
        else:
            logger.info("系统健康，无需修复")
        
        # 步骤4: 发送通知（如果需要）
        notification_sent = self._send_notification_if_needed(diagnosis_result, heal_report)
        
        elapsed = time.time() - start_time
        logger.info(f"监控完成，总耗时: {elapsed:.2f}s")
        
        return True
    
    def _run_diagnosis(self) -> dict:
        """运行诊断脚本"""
        try:
            logger.info("执行诊断...")
            result = subprocess.run(
                [sys.executable, str(self.diagnosis_script), '--json'],
                capture_output=True, text=True, timeout=120
            )
            
            # 从输出中提取JSON（处理可能的非JSON前缀）
            output = result.stdout.strip()
            # 找到JSON开始的位置
            json_start = output.find('{')
            json_end = output.rfind('}')
            
            if json_start >= 0 and json_end > json_start:
                json_str = output[json_start:json_end+1]
                diagnosis = json.loads(json_str)
                logger.info(f"诊断完成: {len(diagnosis.get('checks', []))} 项检查")
                return diagnosis
            else:
                logger.error(f"无法从输出中提取JSON: {output[:200]}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("诊断脚本超时")
            return None
        except Exception as e:
            logger.error(f"运行诊断失败: {e}")
            return None
    
    def _run_heal(self, diagnosis_result: dict) -> dict:
        """运行修复脚本"""
        try:
            logger.info("执行自动修复...")
            
            # 将诊断结果写入临时文件
            temp_file = DATA_DIR / 'last_diagnosis.json'
            with open(temp_file, 'w') as f:
                json.dump(diagnosis_result, f)
            
            result = subprocess.run(
                [sys.executable, str(self.heal_script), '--json', '-d', str(temp_file)],
                capture_output=True, text=True, timeout=180
            )
            
            heal_report = json.loads(result.stdout)
            
            if heal_report.get('needs_human_attention'):
                logger.warning("修复需要人工关注!")
            elif heal_report.get('overall_success'):
                logger.info("自动修复成功")
            else:
                logger.warning("部分修复失败")
            
            return heal_report
            
        except subprocess.TimeoutExpired:
            logger.error("修复脚本超时")
            return {'overall_success': False, 'error': 'timeout'}
        except Exception as e:
            logger.error(f"运行修复失败: {e}")
            return {'overall_success': False, 'error': str(e)}
    
    def _send_notification_if_needed(self, diagnosis: dict, heal_report: dict = None) -> bool:
        """根据需要发送通知"""
        
        # 判断是否需要发送通知
        should_notify = False
        notification_level = 'info'
        message = None
        
        if diagnosis.get('overall_status') == 'critical':
            should_notify = True
            notification_level = 'critical'
        elif heal_report and heal_report.get('needs_human_attention'):
            should_notify = True
            notification_level = 'high'
        elif heal_report and not heal_report.get('overall_success'):
            should_notify = True
            notification_level = 'medium'
        
        if not should_notify:
            return False
        
        # 构建通知消息
        message = self._build_notification_message(diagnosis, heal_report, notification_level)
        
        # 记录通知
        self._log_notification(notification_level, message)
        
        # 对于严重问题，打印到控制台
        if notification_level in ['critical', 'high']:
            print("\n" + "=" * 70)
            print(message)
            print("=" * 70 + "\n")
        
        logger.info(f"通知已记录: 级别={notification_level}")
        return True
    
    def _build_notification_message(self, diagnosis: dict, heal_report: dict, level: str) -> str:
        """构建通知消息"""
        lines = []
        
        if level == 'critical':
            lines.append("🚨 林林 v5.0 紧急告警 🚨")
        elif level == 'high':
            lines.append("⚠️ 林林 v5.0 严重问题告警")
        else:
            lines.append("ℹ️ 林林 v5.0 系统通知")
        
        lines.extend([
            "",
            f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"系统状态: {diagnosis.get('overall_status', 'unknown')} (分数: {diagnosis.get('overall_score', 0):.1f})",
            "",
            "诊断详情:"
        ])
        
        # 添加问题检查项
        for check in diagnosis.get('checks', []):
            if check.get('status') in ['warning', 'critical']:
                icon = "⚠️" if check['status'] == 'warning' else "🚨"
                lines.append(f"  {icon} {check['component']}: {check['message']}")
        
        # 添加修复结果
        if heal_report:
            lines.extend(["", "自动修复结果:"])
            if heal_report.get('overall_success'):
                lines.append("  ✓ 修复成功")
            else:
                lines.append("  ✗ 部分修复失败")
            
            if heal_report.get('actions'):
                for action in heal_report['actions'][:5]:  # 只显示前5个
                    icon = "✓" if action.get('success') else "✗"
                    lines.append(f"    {icon} {action.get('action')}: {action.get('message', '')}")
        
        # 添加建议
        recommendations = diagnosis.get('recommendations', [])
        if recommendations:
            lines.extend(["", "建议操作:"])
            for rec in recommendations[:3]:
                lines.append(f"  • {rec}")
        
        return '\n'.join(lines)
    
    def _log_notification(self, level: str, message: str):
        """记录通知"""
        try:
            notification = {
                'timestamp': datetime.now().isoformat(),
                'level': level,
                'message': message
            }
            
            with open(NOTIFICATION_LOG, 'a') as f:
                f.write(json.dumps(notification, ensure_ascii=False) + '\n')
                
        except Exception as e:
            logger.error(f"记录通知失败: {e}")


def main():
    """主函数"""
    monitor = HealthMonitorV5()
    
    try:
        success = monitor.run()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.exception("健康监控执行失败")
        sys.exit(1)


if __name__ == '__main__':
    main()
