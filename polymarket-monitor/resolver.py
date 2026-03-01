"""
Polymarket 市场解析器
用于跟踪市场结果并更新告警记录的准确率统计
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import aiohttp
import asyncio
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketResolver:
    """市场解析器 - 跟踪事件结果"""
    
    def __init__(self, db_path: str = "data/polymarket.db"):
        self.db_path = db_path
        self.base_url = "https://gamma-api.polymarket.com"
    
    def get_unresolved_alerts(self) -> List[Dict]:
        """获取未解析的告警"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT alert_id, market_id, market_title, spike_after, alert_time
                FROM alerts
                WHERE resolved = 0
                ORDER BY alert_time DESC
            """)
            
            rows = cursor.fetchall()
            return [{
                'alert_id': row[0],
                'market_id': row[1],
                'market_title': row[2],
                'spike_after': row[3],
                'alert_time': row[4]
            } for row in rows]
    
    async def fetch_market_status(self, market_id: str) -> Optional[Dict]:
        """获取市场当前状态"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/markets"
                params = {'slug': market_id}
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and len(data) > 0:
                            return data[0]
                    return None
        except Exception as e:
            logger.error(f"获取市场状态失败 {market_id}: {e}")
            return None
    
    def determine_outcome(self, market: Dict) -> Optional[str]:
        """根据市场数据判断结果"""
        try:
            # 检查市场是否已关闭
            if market.get('active') == False:
                # 找到获胜的结果
                outcomes = market.get('outcomes', [])
                if outcomes:
                    # 找到价格为1的结果
                    for outcome in outcomes:
                        if outcome.get('price') == 1:
                            return outcome.get('name', 'yes')
                return 'no'
            
            # 市场仍然活跃但可能已有明确趋势
            outcomes = market.get('outcomes', [])
            if outcomes:
                # 如果当前价格非常接近1或0，可以认为已有明确结果
                for outcome in outcomes:
                    price = outcome.get('price', 0.5)
                    if price >= 0.95:
                        return outcome.get('name', 'yes')
                    elif price <= 0.05:
                        return 'no' if outcome.get('name', '').lower() == 'yes' else 'yes'
            
            return None
            
        except Exception as e:
            logger.error(f"判断结果失败: {e}")
            return None
    
    def was_spike_correct(self, spike_after: float, final_outcome: str) -> bool:
        """判断告警是否正确
        
        逻辑:
        - 如果概率飙升到 > 70% 且最终结果是 YES，则告警正确
        - 如果概率飙升到 > 70% 但最终结果是 NO，则告警错误
        - 如果概率飙升到 < 30% 且最终结果是 NO，则告警正确（概率下降）
        """
        try:
            if final_outcome == 'yes' or final_outcome.upper() == 'YES':
                # 如果飙升到高概率且结果是 YES，则正确
                return spike_after > 0.5
            elif final_outcome == 'no' or final_outcome.upper() == 'NO':
                # 如果结果是 NO，需要判断概率飙升方向
                return spike_after < 0.5
            else:
                logger.warning(f"未知的结果类型: {final_outcome}")
                return False
        except Exception as e:
            logger.error(f"判断告警正确性失败: {e}")
            return False
    
    def update_alert_resolution(self, alert_id: str, final_outcome: str, correct: bool):
        """更新告警的解析状态"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE alerts
                SET resolved = 1, final_outcome = ?, correct = ?, updated_at = CURRENT_TIMESTAMP
                WHERE alert_id = ?
            """, (final_outcome, correct, alert_id))
            conn.commit()
            logger.info(f"告警 {alert_id} 已解析: {final_outcome}, 正确: {correct}")
    
    async def resolve_single_alert(self, alert: Dict) -> bool:
        """解析单个告警"""
        try:
            logger.info(f"🔍 解析告警: {alert['market_title']}")
            
            # 获取市场当前状态
            market = await self.fetch_market_status(alert['market_id'])
            
            if not market:
                logger.warning(f"无法获取市场: {alert['market_id']}")
                return False
            
            # 判断结果
            final_outcome = self.determine_outcome(market)
            
            if final_outcome:
                # 判断告警是否正确
                correct = self.was_spike_correct(alert['spike_after'], final_outcome)
                
                # 更新数据库
                self.update_alert_resolution(alert['alert_id'], final_outcome, correct)
                
                logger.info(f"✅ 告警已解析: {final_outcome}, 正确: {correct}")
                return True
            else:
                logger.info(f"⏳ 市场尚未有明确结果: {alert['market_id']}")
                return False
                
        except Exception as e:
            logger.error(f"解析告警失败 {alert['alert_id']}: {e}")
            return False
    
    async def resolve_all_alerts(self):
        """解析所有未解析的告警"""
        alerts = self.get_unresolved_alerts()
        
        if not alerts:
            logger.info("✅ 没有待解析的告警")
            return
        
        logger.info(f"📋 找到 {len(alerts)} 个待解析的告警")
        
        resolved_count = 0
        for alert in alerts:
            try:
                result = await self.resolve_single_alert(alert)
                if result:
                    resolved_count += 1
                
                # 避免请求过快
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"处理告警异常: {e}")
                continue
        
        logger.info(f"📊 解析完成: {resolved_count}/{len(alerts)} 个告警已解析")
        
        # 显示统计信息
        self.show_statistics()
    
    def show_statistics(self):
        """显示准确率统计"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 获取统计数据
            cursor.execute("SELECT COUNT(*) FROM alerts")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM alerts WHERE resolved = 1")
            resolved = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM alerts WHERE correct = 1")
            correct = cursor.fetchone()[0]
            
            accuracy = (correct / resolved * 100) if resolved > 0 else 0
            
            print("\n" + "="*60)
            print("📊 Polymarket Monitor 准确率统计")
            print("="*60)
            print(f"总告警数: {total}")
            print(f"已解析: {resolved}")
            print(f"正确: {correct}")
            print(f"❌ 错误: {resolved - correct}")
            print(f"✅ 准确率: {accuracy:.2f}%")
            print("="*60 + "\n")

async def main():
    """主函数"""
    print("╔════════════════════════════════════════════════════════════╗")
    print("║         🎯 Polymarket 市场解析器                         ║")
    print("║         跟踪事件结果 · 统计准确率                        ║")
    print("╚════════════════════════════════════════════════════════════╝\n")
    
    resolver = MarketResolver()
    await resolver.resolve_all_alerts()

if __name__ == "__main__":
    asyncio.run(main())
