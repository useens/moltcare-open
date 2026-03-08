#!/usr/bin/env python3
"""
MoltCare Memory Service - Agent记忆备份服务
MVP版本: 每日自动备份 + 压缩前保护

收款地址: 0x5e7c9888e90d72c9ed223dfdaf039c4a7a18ce33
"""

import os
import sys
import json
import shutil
import tarfile
import logging
from datetime import datetime, timedelta
from pathlib import Path
from cryptography.fernet import Fernet

# 配置
CONFIG = {
    "backup_dir": os.getenv("MOLTCARE_BACKUP_DIR", "data/moltcare/backups"),
    "subscribers_file": os.getenv("MOLTCARE_SUBSCRIBERS", "data/moltcare/subscribers.json"),
    "memory_paths": ["memory", "MEMORY.md", "SOUL.md", "USER.md"],
    "retention_days": 7,
    "encryption_key_file": "data/moltcare/.backup_key",
}

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - MoltCare-Memory - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/moltcare-memory.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MemoryBackupService:
    """Agent记忆备份服务"""
    
    def __init__(self):
        self.backup_dir = Path(CONFIG["backup_dir"])
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载或生成加密密钥
        self.cipher = self._get_cipher()
        
        logger.info("Memory Backup Service initialized")
    
    def _get_cipher(self):
        """获取或生成加密密钥"""
        key_file = Path(CONFIG["encryption_key_file"])
        key_file.parent.mkdir(parents=True, exist_ok=True)
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            logger.info("Generated new encryption key")
        
        return Fernet(key)
    
    def get_active_subscribers(self):
        """获取有Memory服务的活跃订阅者"""
        subs_file = Path(CONFIG["subscribers_file"])
        if not subs_file.exists():
            return []
        
        with open(subs_file, 'r') as f:
            subscribers = json.load(f)
        
        now = datetime.now()
        active = []
        
        for agent_id, sub in subscribers.items():
            # 检查是否是Memory服务且未过期
            if 'memory' not in sub.get('service', ''):
                continue
            
            try:
                expiry = datetime.fromisoformat(sub['expiry'])
                if expiry > now:
                    active.append({
                        'agent_id': agent_id,
                        'expiry': expiry,
                        'service': sub['service']
                    })
            except:
                continue
        
        return active
    
    def backup_agent(self, agent_id, source_paths=None):
        """备份指定Agent的记忆"""
        if source_paths is None:
            # 默认备份当前环境的记忆文件
            source_paths = CONFIG["memory_paths"]
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{agent_id}_{timestamp}.tar.gz.enc"
        backup_path = self.backup_dir / agent_id / backup_name
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # 创建临时tar文件
            temp_tar = self.backup_dir / f"temp_{timestamp}.tar.gz"
            
            with tarfile.open(temp_tar, 'w:gz') as tar:
                for path_str in source_paths:
                    path = Path(path_str)
                    if path.exists():
                        tar.add(path, arcname=path.name)
                        logger.debug(f"Added {path} to backup")
            
            # 加密
            with open(temp_tar, 'rb') as f:
                data = f.read()
            encrypted = self.cipher.encrypt(data)
            
            with open(backup_path, 'wb') as f:
                f.write(encrypted)
            
            # 删除临时文件
            temp_tar.unlink()
            
            # 清理旧备份
            self._cleanup_old_backups(agent_id)
            
            logger.info(f"✅ Backup completed: {agent_id} -> {backup_name}")
            return {
                'success': True,
                'backup_file': str(backup_path),
                'timestamp': timestamp,
                'agent_id': agent_id
            }
            
        except Exception as e:
            logger.error(f"❌ Backup failed for {agent_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'agent_id': agent_id
            }
    
    def _cleanup_old_backups(self, agent_id):
        """清理超过保留期的备份"""
        agent_dir = self.backup_dir / agent_id
        if not agent_dir.exists():
            return
        
        cutoff = datetime.now() - timedelta(days=CONFIG["retention_days"])
        
        for backup_file in agent_dir.glob("*.tar.gz.enc"):
            try:
                # 从文件名提取时间戳
                timestamp_str = backup_file.stem.split('_')[-2] + '_' + backup_file.stem.split('_')[-1].replace('.tar.gz', '')
                file_time = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                
                if file_time < cutoff:
                    backup_file.unlink()
                    logger.debug(f"Cleaned up old backup: {backup_file.name}")
            except:
                continue
    
    def run_daily_backup(self):
        """执行每日备份"""
        logger.info("🔄 Starting daily backup cycle...")
        
        subscribers = self.get_active_subscribers()
        if not subscribers:
            logger.info("No active Memory subscribers")
            return
        
        logger.info(f"Found {len(subscribers)} active subscribers")
        
        results = []
        for sub in subscribers:
            result = self.backup_agent(sub['agent_id'])
            results.append(result)
        
        # 统计
        success = sum(1 for r in results if r['success'])
        failed = len(results) - success
        
        logger.info(f"Daily backup complete: {success} success, {failed} failed")
        return results
    
    def emergency_backup(self, agent_id):
        """紧急备份（压缩前调用）"""
        logger.info(f"🚨 Emergency backup triggered for {agent_id}")
        return self.backup_agent(agent_id)
    
    def list_backups(self, agent_id):
        """列出Agent的所有备份"""
        agent_dir = self.backup_dir / agent_id
        if not agent_dir.exists():
            return []
        
        backups = []
        for backup_file in sorted(agent_dir.glob("*.tar.gz.enc"), reverse=True):
            try:
                stat = backup_file.stat()
                backups.append({
                    'file': backup_file.name,
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            except:
                continue
        
        return backups
    
    def restore_backup(self, agent_id, backup_file, target_dir=None):
        """恢复备份"""
        if target_dir is None:
            target_dir = Path("restored") / agent_id
        
        backup_path = self.backup_dir / agent_id / backup_file
        
        if not backup_path.exists():
            return {'success': False, 'error': 'Backup file not found'}
        
        try:
            # 解密
            with open(backup_path, 'rb') as f:
                encrypted = f.read()
            decrypted = self.cipher.decrypt(encrypted)
            
            # 解压
            target_dir.mkdir(parents=True, exist_ok=True)
            temp_tar = target_dir / "temp_restore.tar.gz"
            
            with open(temp_tar, 'wb') as f:
                f.write(decrypted)
            
            with tarfile.open(temp_tar, 'r:gz') as tar:
                tar.extractall(target_dir)
            
            temp_tar.unlink()
            
            logger.info(f"✅ Restore completed: {agent_id} from {backup_file}")
            return {
                'success': True,
                'restored_to': str(target_dir),
                'agent_id': agent_id
            }
            
        except Exception as e:
            logger.error(f"❌ Restore failed: {e}")
            return {'success': False, 'error': str(e)}


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MoltCare Memory Service')
    parser.add_argument('--backup', help='Backup specific agent')
    parser.add_argument('--list', help='List backups for agent')
    parser.add_argument('--restore', nargs=2, metavar=('AGENT', 'FILE'), help='Restore backup')
    parser.add_argument('--daily', action='store_true', help='Run daily backup cycle')
    parser.add_argument('--emergency', help='Emergency backup for agent')
    
    args = parser.parse_args()
    
    service = MemoryBackupService()
    
    if args.backup:
        result = service.backup_agent(args.backup)
        print(json.dumps(result, indent=2))
    
    elif args.list:
        backups = service.list_backups(args.list)
        print(json.dumps(backups, indent=2))
    
    elif args.restore:
        agent, file = args.restore
        result = service.restore_backup(agent, file)
        print(json.dumps(result, indent=2))
    
    elif args.emergency:
        result = service.emergency_backup(args.emergency)
        print(json.dumps(result, indent=2))
    
    elif args.daily:
        results = service.run_daily_backup()
        print(json.dumps(results, indent=2, default=str))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
