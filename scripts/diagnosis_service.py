#!/usr/bin/env python3
"""
Self-Diagnosis Service v5.0
自我诊断系统服务

功能：
- 启动/停止所有诊断模块
- 提供统一的HTTP API接口
- 定期生成诊断报告
- 系统健康仪表盘
"""

import json
import asyncio
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# 导入集成模块
import sys
sys.path.insert(0, str(Path(__file__).parent))

from diagnosis_integration import get_orchestrator, analyze_response, check_system_health

import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/.openclaw/workspace/logs/diagnosis_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiagnosisService')


class DiagnosisService:
    """诊断服务"""
    
    def __init__(self):
        self.orchestrator = get_orchestrator()
        self.running = False
        self.data_dir = Path('/root/.openclaw/workspace/data/diagnosis')
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    async def start(self):
        """启动服务"""
        logger.info("Starting Self-Diagnosis Service v5.0...")
        
        await self.orchestrator.initialize()
        self.running = True
        
        # 启动主循环
        asyncio.create_task(self._main_loop())
        
        logger.info("Self-Diagnosis Service started")
    
    async def stop(self):
        """停止服务"""
        logger.info("Stopping Self-Diagnosis Service...")
        self.running = False
        self.orchestrator.stop()
        logger.info("Self-Diagnosis Service stopped")
    
    async def _main_loop(self):
        """主循环"""
        while self.running:
            try:
                await self.orchestrator.run_cycle()
                await asyncio.sleep(60)  # 每分钟运行一次
            except Exception as e:
                logger.error(f"Service loop error: {e}")
                await asyncio.sleep(10)
    
    async def analyze(self, session_id: str, user_query: str, ai_response: str) -> Dict:
        """分析交互"""
        return await self.orchestrator.analyze_interaction(session_id, user_query, ai_response)
    
    def get_status(self) -> Dict:
        """获取状态"""
        return self.orchestrator.get_full_status()
    
    def get_health_dashboard(self) -> Dict:
        """获取健康仪表盘数据"""
        status = self.get_status()
        
        # 计算健康分数
        health_score = 100
        
        # 根据降级级别扣分
        if 'modules' in status and 'smart_degrade' in status['modules']:
            degrade_level = status['modules']['smart_degrade'].get('current_level', 'normal')
            level_penalty = {
                'normal': 0,
                'light': 10,
                'medium': 25,
                'severe': 50,
                'offline': 75
            }
            health_score -= level_penalty.get(degrade_level, 0)
        
        # 根据资源使用扣分
        if 'modules' in status and 'smart_degrade' in status['modules']:
            resources = status['modules']['smart_degrade'].get('resource_usage', {})
            for resource, usage in resources.items():
                if usage > 90:
                    health_score -= 10
                elif usage > 80:
                    health_score -= 5
        
        health_score = max(0, min(100, health_score))
        
        # 确定健康状态
        if health_score >= 90:
            health_status = 'excellent'
        elif health_score >= 75:
            health_status = 'good'
        elif health_score >= 60:
            health_status = 'fair'
        elif health_score >= 40:
            health_status = 'poor'
        else:
            health_status = 'critical'
        
        return {
            'timestamp': datetime.now().isoformat(),
            'health_score': health_score,
            'health_status': health_status,
            'system_status': status
        }
    
    def generate_report(self, format: str = 'json') -> str:
        """生成诊断报告"""
        dashboard = self.get_health_dashboard()
        
        if format == 'json':
            return json.dumps(dashboard, indent=2, default=str)
        
        elif format == 'markdown':
            lines = [
                "# 自我诊断系统报告 v5.0",
                f"\n生成时间: {dashboard['timestamp']}",
                f"\n## 健康评分: {dashboard['health_score']}/100 ({dashboard['health_status']})",
                "\n## 系统状态",
            ]
            
            status = dashboard['system_status']
            
            # 降级状态
            if 'modules' in status and 'smart_degrade' in status['modules']:
                sd = status['modules']['smart_degrade']
                lines.extend([
                    f"\n### 降级状态",
                    f"- 当前级别: {sd.get('current_level', 'unknown')}",
                    f"- 质量分数: {sd.get('quality_score', 'N/A'):.3f}",
                    f"- 网络可用: {sd.get('network_available', 'N/A')}",
                    f"- 可恢复: {sd.get('can_recover', 'N/A')}",
                ])
            
            # 资源使用
            if 'modules' in status and 'smart_degrade' in status['modules']:
                resources = status['modules']['smart_degrade'].get('resource_usage', {})
                lines.extend([
                    f"\n### 资源使用",
                    f"- CPU: {resources.get('cpu', 'N/A')}%",
                    f"- 内存: {resources.get('memory', 'N/A')}%",
                    f"- 磁盘: {resources.get('disk', 'N/A')}%",
                ])
            
            # 优化建议
            if 'modules' in status and 'optimization' in status['modules']:
                opt = status['modules']['optimization']
                lines.extend([
                    f"\n### 优化建议",
                    f"- 总建议数: {opt.get('total_suggestions', 0)}",
                    f"- 待执行: {opt.get('pending', 0)}",
                    f"- 已执行: {opt.get('executed', 0)}",
                ])
            
            return '\n'.join(lines)
        
        return json.dumps(dashboard, indent=2, default=str)


# 全局服务实例
_service: Optional[DiagnosisService] = None


def get_service() -> DiagnosisService:
    """获取服务实例"""
    global _service
    if _service is None:
        _service = DiagnosisService()
    return _service


# 简单的HTTP API服务器（可选）
async def run_http_server(host: str = '127.0.0.1', port: int = 8765):
    """运行HTTP API服务器"""
    from aiohttp import web
    
    service = get_service()
    
    async def handle_status(request):
        return web.json_response(service.get_status())
    
    async def handle_health(request):
        return web.json_response(service.get_health_dashboard())
    
    async def handle_analyze(request):
        try:
            data = await request.json()
            result = await service.analyze(
                data.get('session_id', 'anonymous'),
                data.get('query', ''),
                data.get('response', '')
            )
            return web.json_response(result)
        except Exception as e:
            return web.json_response({'error': str(e)}, status=400)
    
    async def handle_report(request):
        format = request.query.get('format', 'json')
        report = service.generate_report(format)
        
        if format == 'markdown':
            return web.Response(text=report, content_type='text/markdown')
        return web.Response(text=report, content_type='application/json')
    
    app = web.Application()
    app.router.add_get('/status', handle_status)
    app.router.add_get('/health', handle_health)
    app.router.add_post('/analyze', handle_analyze)
    app.router.add_get('/report', handle_report)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    
    logger.info(f"HTTP API server started on http://{host}:{port}")
    await site.start()
    
    return runner


# CLI主函数
async def main():
    parser = argparse.ArgumentParser(description='Self-Diagnosis Service v5.0')
    parser.add_argument('--start', action='store_true', help='Start the service')
    parser.add_argument('--stop', action='store_true', help='Stop the service')
    parser.add_argument('--status', action='store_true', help='Show status')
    parser.add_argument('--report', action='store_true', help='Generate report')
    parser.add_argument('--http', action='store_true', help='Enable HTTP API')
    parser.add_argument('--http-host', default='127.0.0.1', help='HTTP server host')
    parser.add_argument('--http-port', type=int, default=8765, help='HTTP server port')
    parser.add_argument('--analyze', nargs=3, metavar=('SESSION', 'QUERY', 'RESPONSE'),
                       help='Analyze an interaction')
    
    args = parser.parse_args()
    
    service = get_service()
    
    if args.start:
        await service.start()
        
        if args.http:
            runner = await run_http_server(args.http_host, args.http_port)
        
        try:
            # 保持运行
            while service.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            await service.stop()
            if args.http:
                await runner.cleanup()
    
    elif args.stop:
        await service.stop()
    
    elif args.status:
        print(json.dumps(service.get_status(), indent=2, default=str))
    
    elif args.report:
        print(service.generate_report(format='markdown'))
    
    elif args.analyze:
        await service.start()
        session_id, query, response = args.analyze
        result = await service.analyze(session_id, query, response)
        print(json.dumps(result, indent=2))
        await service.stop()
    
    else:
        parser.print_help()


if __name__ == '__main__':
    asyncio.run(main())
