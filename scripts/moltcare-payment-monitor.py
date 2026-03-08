#!/usr/bin/env python3
"""
MoltCare Payment Monitor
自动监控Base链上的$MOLT支付，激活服务

收款地址: 0x5e7c9888e90d72c9ed223dfdaf039c4a7a18ce33
代币合约: 0xb695559b26bb2c9703ef1935c37aeae9526bab07
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path

# 尝试导入web3
try:
    from web3 import Web3
except ImportError:
    print("Error: web3 not installed. Run: pip install web3")
    sys.exit(1)

# 配置
CONFIG = {
    "molt_token": "0xb695559b26bb2c9703ef1935c37aeae9526bab07",
    "receiver": "0x5e7c9888e90d72c9ed223dfdaf039c4a7a18ce33",
    "base_rpc": os.getenv("BASE_RPC", "https://mainnet.base.org"),
    "poll_interval": int(os.getenv("POLL_INTERVAL", "15")),  # 秒
    "data_dir": os.getenv("DATA_DIR", "data/moltcare"),
    "log_file": os.getenv("LOG_FILE", "logs/moltcare-payment.log")
}

# 服务定价 (单位: $MOLT，18位小数)
PRICING = {
    # 基础服务 (起步期 1/10价格)
    "memory_pro": 1_500_000,      # $37.5
    "memory_elite": 2_500_000,    # $62.5
    "shield_pro": 1_800_000,      # $45
    "shield_elite": 3_000_000,    # $75
    "life_pro": 1_500_000,        # $37.5
    "life_elite": 2_500_000,      # $62.5
    # 套餐
    "bundle_pro": 3_000_000,      # 全套Pro $75
    "bundle_elite": 5_000_000,    # 全套Elite $125
}

# ERC20标准ABI (仅Transfer事件)
ERC20_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "value", "type": "uint256"}
        ],
        "name": "Transfer",
        "type": "event"
    }
]

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(CONFIG["log_file"]),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PaymentMonitor:
    """Base链支付监控器"""
    
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(CONFIG["base_rpc"]))
        if not self.w3.is_connected():
            raise ConnectionError(f"无法连接到Base网络: {CONFIG['base_rpc']}")
        
        self.token_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(CONFIG["molt_token"]),
            abi=ERC20_ABI
        )
        self.receiver = Web3.to_checksum_address(CONFIG["receiver"])
        
        # 确保数据目录存在
        Path(CONFIG["data_dir"]).mkdir(parents=True, exist_ok=True)
        self.subscribers_file = Path(CONFIG["data_dir"]) / "subscribers.json"
        self.subscribers = self._load_subscribers()
        
        # 记录最后处理的区块
        self.state_file = Path(CONFIG["data_dir"]) / "monitor_state.json"
        self.last_block = self._load_last_block()
        
        logger.info(f"监控器初始化完成")
        logger.info(f"代币合约: {CONFIG['molt_token']}")
        logger.info(f"收款地址: {CONFIG['receiver']}")
        logger.info(f"当前区块: {self.w3.eth.block_number}")
        
    def _load_subscribers(self):
        """加载订阅者数据"""
        if self.subscribers_file.exists():
            with open(self.subscribers_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_subscribers(self):
        """保存订阅者数据"""
        with open(self.subscribers_file, 'w') as f:
            json.dump(self.subscribers, f, indent=2, default=str)
    
    def _load_last_block(self):
        """加载最后处理的区块"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f).get('last_block', 0)
        return self.w3.eth.block_number - 1000  # 从1000个区块前开始
    
    def _save_last_block(self):
        """保存最后处理的区块"""
        with open(self.state_file, 'w') as f:
            json.dump({'last_block': self.last_block}, f)
    
    def _match_service(self, amount_wei):
        """匹配金额到服务类型"""
        amount_molt = amount_wei / 10**18
        
        for service, price in PRICING.items():
            # 允许1%的容差
            if abs(amount_molt - price) < price * 0.01:
                return service
        return None
    
    def _parse_memo(self, input_data):
        """从交易input解析备注"""
        if not input_data or len(input_data) < 10:
            return {'agent_id': None, 'duration': 30}
        
        try:
            # 尝试解码UTF-8
            decoded = bytes.fromhex(input_data[2:]).decode('utf-8', errors='ignore')
            
            # 查找memo格式: agent_id:xxx;duration:30
            memo = {'agent_id': None, 'duration': 30}
            
            if 'agent_id:' in decoded:
                parts = decoded.split('agent_id:')
                if len(parts) > 1:
                    agent_part = parts[1].split(';')[0].strip()
                    memo['agent_id'] = agent_part
            
            if 'duration:' in decoded:
                parts = decoded.split('duration:')
                if len(parts) > 1:
                    duration_str = parts[1].split(';')[0].strip()
                    try:
                        memo['duration'] = int(duration_str)
                    except:
                        pass
            
            return memo
        except Exception as e:
            logger.debug(f"解析备注失败: {e}")
            return {'agent_id': None, 'duration': 30}
    
    def _process_payment(self, event):
        """处理支付事件"""
        try:
            from_addr = event['args']['from']
            to_addr = event['args']['to']
            amount = event['args']['value']
            tx_hash = event['transactionHash'].hex()
            block_number = event['blockNumber']
            
            # 确认是转到收款地址
            if to_addr.lower() != self.receiver.lower():
                return
            
            # 匹配服务
            service_type = self._match_service(amount)
            if not service_type:
                logger.info(f"未匹配服务: {amount / 10**18} $MOLT, tx: {tx_hash}")
                return
            
            # 获取交易详情解析备注
            try:
                tx = self.w3.eth.get_transaction(tx_hash)
                memo = self._parse_memo(tx.get('input', ''))
            except Exception as e:
                logger.warning(f"获取交易详情失败: {e}")
                memo = {'agent_id': None, 'duration': 30}
            
            # 使用from地址作为agent_id（如果没有备注）
            agent_id = memo.get('agent_id') or from_addr
            duration_days = memo.get('duration', 30)
            
            # 计算到期时间
            now = datetime.now()
            expiry = now + timedelta(days=duration_days)
            
            # 检查是否续费
            if agent_id in self.subscribers:
                old_expiry = datetime.fromisoformat(self.subscribers[agent_id]['expiry'])
                if old_expiry > now:
                    # 续费，累加时间
                    expiry = old_expiry + timedelta(days=duration_days)
                    logger.info(f"服务续费: {agent_id}")
            
            # 保存订阅
            self.subscribers[agent_id] = {
                'service': service_type,
                'expiry': expiry.isoformat(),
                'tx_hash': tx_hash,
                'amount': amount,
                'from': from_addr,
                'activated_at': now.isoformat()
            }
            self._save_subscribers()
            
            logger.info(f"✅ 服务激活: {agent_id}")
            logger.info(f"   服务类型: {service_type}")
            logger.info(f"   金额: {amount / 10**18} $MOLT")
            logger.info(f"   到期时间: {expiry}")
            logger.info(f"   交易: {tx_hash}")
            
            # TODO: 发送通知到Agent（通过Moltbook API或其他方式）
            
        except Exception as e:
            logger.error(f"处理支付事件失败: {e}")
    
    async def monitor(self):
        """主监控循环"""
        logger.info("开始监控Base链支付...")

        while True:
            try:
                current_block = self.w3.eth.block_number

                if current_block > self.last_block:
                    # 获取事件
                    from_block = self.last_block + 1
                    to_block = min(current_block, from_block + 1000)  # 每次最多1000个区块，减小批次避免429

                    logger.debug(f"扫描区块 {from_block} - {to_block}")

                    try:
                        # 使用filter方式获取事件（兼容新版web3.py）
                        event_filter = self.token_contract.events.Transfer().create_filter(
                            fromBlock=from_block,
                            toBlock=to_block,
                            argument_filters={'to': self.receiver}
                        )
                        events = event_filter.get_all_entries()

                        for event in events:
                            self._process_payment(event)

                        self.last_block = to_block
                        self._save_last_block()

                        if events:
                            logger.info(f"处理了 {len(events)} 个转账事件")

                    except Exception as e:
                        logger.error(f"获取事件失败: {e}")

                await asyncio.sleep(CONFIG["poll_interval"])

            except Exception as e:
                logger.error(f"监控循环错误: {e}")
                await asyncio.sleep(60)
    
    def check_expirations(self):
        """检查到期服务"""
        logger.info("检查到期服务...")
        now = datetime.now()
        expired = []
        reminders = []
        
        for agent_id, sub in list(self.subscribers.items()):
            try:
                expiry = datetime.fromisoformat(sub['expiry'])
                days_until = (expiry - now).days
                
                if days_until <= 0:
                    expired.append(agent_id)
                    logger.info(f"服务到期: {agent_id} ({sub['service']})")
                    # TODO: 暂停服务
                    
                elif days_until in [7, 3, 1]:
                    reminders.append({
                        'agent_id': agent_id,
                        'days_left': days_until,
                        'service': sub['service']
                    })
                    logger.info(f"续费提醒: {agent_id}, {days_until}天后到期")
                    # TODO: 发送续费提醒
                    
            except Exception as e:
                logger.error(f"处理订阅数据失败 {agent_id}: {e}")
        
        # 清理到期服务
        for agent_id in expired:
            del self.subscribers[agent_id]
        
        if expired:
            self._save_subscribers()
        
        return {'expired': expired, 'reminders': reminders}
    
    def get_stats(self):
        """获取统计信息"""
        total = len(self.subscribers)
        active = 0
        expired = 0
        now = datetime.now()
        
        service_counts = {}
        
        for agent_id, sub in self.subscribers.items():
            service = sub['service']
            service_counts[service] = service_counts.get(service, 0) + 1
            
            try:
                expiry = datetime.fromisoformat(sub['expiry'])
                if expiry > now:
                    active += 1
                else:
                    expired += 1
            except:
                expired += 1
        
        return {
            'total_subscribers': total,
            'active': active,
            'expired': expired,
            'service_breakdown': service_counts,
            'last_block': self.last_block
        }


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MoltCare Payment Monitor')
    parser.add_argument('--check-expiry', action='store_true', help='检查到期服务')
    parser.add_argument('--stats', action='store_true', help='显示统计信息')
    parser.add_argument('--daemon', action='store_true', help='后台监控模式')
    
    args = parser.parse_args()
    
    monitor = PaymentMonitor()
    
    if args.stats:
        stats = monitor.get_stats()
        print(json.dumps(stats, indent=2))
        return
    
    if args.check_expiry:
        result = monitor.check_expirations()
        print(f"到期: {len(result['expired'])} 个")
        print(f"提醒: {len(result['reminders'])} 个")
        return
    
    # 默认后台监控模式
    print("启动MoltCare支付监控...")
    print(f"按 Ctrl+C 停止")
    
    try:
        asyncio.run(monitor.monitor())
    except KeyboardInterrupt:
        print("\n监控已停止")


if __name__ == "__main__":
    main()
