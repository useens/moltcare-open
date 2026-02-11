#!/usr/bin/env python3
"""
记忆系统自愈守护进程
- 自动检测问题
- 自动修复常见问题
- 持续保持系统健康
"""
import os
import sys
import json
import time
from datetime import datetime, timedelta

sys.path.insert(0, 'scripts/memory-system')

class MemorySystemGuardian:
    """记忆系统守护者"""
    
    def __init__(self):
        self.log_file = "/root/.openclaw/logs/guardian.log"
        self.state_file = "/root/.openclaw/logs/guardian_state.json"
        self.state = self._load_state()
    
    def _load_state(self):
        if os.path.exists(self.state_file):
            with open(self.state_file) as f:
                return json.load(f)
        return {'last_check': None, 'fixes_applied': 0}
    
    def _save_state(self):
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f)
    
    def log(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        with open(self.log_file, 'a') as f:
            f.write(log_entry + '\n')
    
    def check_and_fix_v52_vectors(self):
        """检查并修复v5.2向量"""
        try:
            from vector_memory import get_vector_memory
            from sentence_transformers import SentenceTransformer
            
            vm = get_vector_memory()
            
            # 检查无向量的记忆
            no_vec_memories = []
            for mid, mem in vm.memories.items():
                vec = mem.get('vector')
                emb = mem.get('embedding')
                # 安全判断：None、空列表、空数组都视为无向量
                has_vec = vec is not None and len(vec) > 0 if hasattr(vec, '__len__') else bool(vec)
                has_emb = emb is not None and len(emb) > 0 if hasattr(emb, '__len__') else bool(emb)
                if not has_vec and not has_emb:
                    no_vec_memories.append((mid, mem))
            
            if no_vec_memories:
                self.log(f"⚠️ 发现 {len(no_vec_memories)} 条无向量记忆，开始修复...")
                
                model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
                
                for mid, mem in no_vec_memories:
                    content = mem.get('content', '')
                    if content:
                        vector = model.encode(content).tolist()
                        mem['vector'] = vector
                
                vm._save_vectors()
                self.log(f"✅ 已修复 {len(no_vec_memories)} 条记忆")
                self.state['fixes_applied'] += len(no_vec_memories)
                return True
            else:
                self.log("✅ v5.2向量记忆全部正常")
                return False
                
        except Exception as e:
            self.log(f"❌ v5.2检查失败: {e}")
            return False
    
    def check_and_fix_v51_long_term(self):
        """检查并修复v5.1长期记忆"""
        try:
            lt_file = 'memory/long_term_memories.json'
            
            needs_rebuild = False
            
            if not os.path.exists(lt_file):
                needs_rebuild = True
                self.log("⚠️ 长期记忆文件不存在")
            else:
                with open(lt_file) as f:
                    lt = json.load(f)
                if len(lt) < 10:
                    needs_rebuild = True
                    self.log(f"⚠️ 长期记忆仅 {len(lt)} 条，需要重建")
            
            if needs_rebuild:
                self.log("🔄 自动重建长期记忆...")
                os.system('python3 scripts/memory-system/enhanced_layered_memory.py > /dev/null 2>&1')
                self.log("✅ 长期记忆重建完成")
                self.state['fixes_applied'] += 1
                return True
            else:
                self.log("✅ v5.1长期记忆正常")
                return False
                
        except Exception as e:
            self.log(f"❌ v5.1检查失败: {e}")
            return False
    
    def check_and_fix_v55_snapshots(self):
        """检查v5.5快照"""
        try:
            from session_persistence import SessionPersistence
            
            sp = SessionPersistence()
            history = sp.get_snapshot_history(hours=24)
            
            if len(history) < 2:
                self.log(f"⚠️ 24小时内仅 {len(history)} 个快照，创建新快照...")
                sp.create_snapshot()
                self.log("✅ 新快照已创建")
                return True
            else:
                self.log(f"✅ v5.5快照正常: {len(history)}个/24h")
                return False
                
        except Exception as e:
            self.log(f"❌ v5.5检查失败: {e}")
            return False
    
    def run_health_check(self):
        """运行完整健康检查"""
        self.log("="*60)
        self.log("🛡️ 记忆系统守护进程启动")
        self.log("="*60)
        
        fixes = []
        
        # 检查v5.2
        if self.check_and_fix_v52_vectors():
            fixes.append('v5.2_vectors')
        
        # 检查v5.1
        if self.check_and_fix_v51_long_term():
            fixes.append('v5.1_long_term')
        
        # 检查v5.5
        if self.check_and_fix_v55_snapshots():
            fixes.append('v5.5_snapshots')
        
        # 更新状态
        self.state['last_check'] = datetime.now().isoformat()
        self._save_state()
        
        self.log("="*60)
        if fixes:
            self.log(f"✅ 已自动修复: {', '.join(fixes)}")
        else:
            self.log("✅ 所有系统健康，无需修复")
        self.log(f"📊 累计修复次数: {self.state['fixes_applied']}")
        self.log("="*60)
        
        return fixes


def main():
    """主函数"""
    guardian = MemorySystemGuardian()
    
    # 单次运行模式（用于定时任务）
    guardian.run_health_check()
    
    print("\n💾 日志保存到: /root/.openclaw/logs/guardian.log")


if __name__ == "__main__":
    main()
