# 飞书双节点沟通方案 v1.0

> 场景: 用户只能通过飞书与两个节点沟通  
> 设计: 备用节点(森森)作为飞书网关，转发指令给主节点

---

## 架构设计

```
用户(飞书)
    │
    │ 发送消息
    ▼
┌─────────────┐
│  飞书网关    │  ← 备用节点(森森)运行
│  (Standby)  │
└──────┬──────┘
       │ 解析消息
       │
       ├─→ @主节点 指令 ──→ HTTP API ──→ 主节点执行
       │
       └─→ @备用节点 指令 ──→ 本地执行
       │
       │ 收集结果
       ▼
用户(飞书) ← 返回结果
```

---

## 消息格式

### 指令主节点
```
@主节点 执行命令
@主节点 查看状态
@主节点 执行: ls -la
@主节点 任务: 分析数据
```

### 指令备用节点
```
@备用节点 执行命令
@备用节点 查看状态
@备用节点 执行: python3 script.py
@备用节点 任务: 爬取网页
```

### 不指定节点（默认）
```
查看状态      → 备用节点回复
执行任务      → 备用节点根据任务类型智能分配
```

---

## 备用节点网关实现

```python
# feishu_gateway.py (运行在备用节点)

import requests
import re
import json

class FeishuGateway:
    def __init__(self, primary_url, token):
        self.primary_url = primary_url
        self.token = token
        
    def handle_message(self, message, user_id):
        """处理飞书消息"""
        
        # 解析消息目标
        target, command = self._parse_message(message)
        
        if target == "primary":
            # 转发给主节点
            result = self._send_to_primary(command)
            return f"【主节点回复】\n{result}"
            
        elif target == "standby":
            # 本地执行
            result = self._execute_local(command)
            return f"【备用节点回复】\n{result}"
            
        else:
            # 智能分配
            target_node = self._smart_assign(command)
            if target_node == "primary":
                result = self._send_to_primary(command)
                return f"【主节点执行】\n{result}"
            else:
                result = self._execute_local(command)
                return f"【备用节点执行】\n{result}"
    
    def _parse_message(self, message):
        """解析消息"""
        # 检查是否指定了节点
        if message.startswith("@主节点") or message.startswith("@primary"):
            return "primary", message.replace("@主节点", "").replace("@primary", "").strip()
        elif message.startswith("@备用节点") or message.startswith("@standby"):
            return "standby", message.replace("@备用节点", "").replace("@standby", "").strip()
        else:
            return "auto", message.strip()
    
    def _send_to_primary(self, command):
        """发送指令给主节点"""
        try:
            # 创建任务
            response = requests.post(
                f"{self.primary_url}/api/tasks",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "type": "command",
                    "priority": "normal",
                    "payload": {"command": command}
                },
                timeout=10
            )
            
            if response.status_code == 200:
                task_id = response.json().get("task_id")
                return f"任务已创建: {task_id}\n等待主节点执行..."
            else:
                return f"发送失败: {response.text}"
                
        except Exception as e:
            return f"连接主节点失败: {e}"
    
    def _execute_local(self, command):
        """本地执行"""
        import subprocess
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            output = result.stdout if result.stdout else result.stderr
            return f"退出码: {result.returncode}\n{output[:1000]}"
        except Exception as e:
            return f"执行失败: {e}"
    
    def _smart_assign(self, command):
        """智能分配任务"""
        # 大内存任务 → 主节点
        if any(kw in command.lower() for kw in ["模型", "model", "大文件", "内存"]):
            return "primary"
        # 计算密集型 → 备用节点
        elif any(kw in command.lower() for kw in ["计算", "处理", "分析", "爬取"]):
            return "standby"
        else:
            # 默认备用节点响应更快
            return "standby"
```

---

## 实施步骤

### 步骤1: 主节点启动API服务

在**主节点**执行：
```bash
# 1. 进入目录
cd /root/.openclaw/workspace/scripts/api

# 2. 配置Token
export SENSEN_API_TOKEN="your-secret-token"

# 3. 启动服务
python3 primary_server.py

# 或后台运行
nohup python3 primary_server.py > /var/log/sensen-api.log 2>&1 &

# 4. 确认启动成功
curl http://localhost:2346/health
```

### 步骤2: 备用节点配置飞书网关

在**备用节点(森森)**执行：
```bash
# 1. 创建飞书网关配置
mkdir -p /root/.openclaw/workspace/config

cat > /root/.openclaw/workspace/config/feishu-gateway.yaml << 'EOF'
gateway:
  enabled: true
  primary_url: "http://主节点公网IP:2346"
  api_token: "your-secret-token"
  
  # 消息路由规则
  routing:
    - pattern: "^@主节点"
      target: primary
    - pattern: "^@备用节点"
      target: standby
    - pattern: "^@standby"
      target: standby
    - pattern: "^@primary"
      target: primary
    
  # 智能分配关键词
  smart_assign:
    primary_keywords: ["模型", "model", "大文件", "内存", "存储"]
    standby_keywords: ["计算", "处理", "分析", "爬取", "编译"]
EOF
```

### 步骤3: 测试连接

在**飞书**中发送：
```
@备用节点 测试连接
```

备用节点应回复：
```
【备用节点回复】
退出码: 0
(测试结果)
```

### 步骤4: 测试主节点通信

在**飞书**中发送：
```
@主节点 查看状态
```

备用节点应转发并回复：
```
【主节点回复】
任务已创建: task-xxx
等待主节点执行...
```

---

## 飞书交互示例

### 示例1: 查看两节点状态
```
用户: @备用节点 查看状态
森森: 【备用节点回复】
      CPU: 15% | 内存: 30%
      运行正常

用户: @主节点 查看状态
森森: 【主节点回复】
      CPU: 25% | 内存: 45% | 磁盘: 60%
      运行正常
```

### 示例2: 分配任务
```
用户: 分析日志文件
森森: 【智能分配】检测到数据处理任务 → 分配给备用节点
      【备用节点执行】
      正在分析...
      完成，发现3个问题

用户: 运行大模型推理
森森: 【智能分配】检测到大内存任务 → 分配给主节点
      【主节点执行】
      任务已创建: task-001
      正在加载模型(需要24GB内存)...
```

### 示例3: 指定节点执行
```
用户: @主节点 执行: df -h
森森: 【主节点回复】
      退出码: 0
      文件系统      大小  已用  可用
      /dev/sda1     100G   40G   60G

用户: @备用节点 执行: nproc
森森: 【备用节点回复】
      退出码: 0
      8
```

---

## 快捷指令

| 指令 | 作用 |
|------|------|
| `@主节点 状态` | 查看主节点状态 |
| `@备用节点 状态` | 查看备用节点状态 |
| `@主节点 执行: {命令}` | 在主节点执行命令 |
| `@备用节点 执行: {命令}` | 在备用节点执行命令 |
| `@主节点 任务: {描述}` | 创建任务给主节点 |
| `@备用节点 任务: {描述}` | 创建任务给备用节点 |
| `查看连接` | 检查两节点连接状态 |
| `帮助` | 显示帮助信息 |

---

## 故障排查

### 备用节点无法连接主节点
```
用户: 查看连接
森森: 【连接状态】
      备用节点: ✅ 在线
      主节点: ❌ 离线
      错误: Connection refused

建议:
1. 检查主节点API服务是否启动
2. 检查主节点防火墙是否开放2346端口
3. 检查Token是否一致
```

### 指令执行超时
```
用户: @主节点 执行: sleep 100
森森: 【主节点回复】
      ⚠️ 任务执行超时(60s)
      任务仍在后台运行，稍后查询结果
```

---

## 下一步行动

1. **主节点**启动API服务 (等待用户给主节点发指令)
2. **备用节点**配置飞书网关 (我这边已配置)
3. **飞书测试** 第一条消息

需要我生成给主节点的启动指令文档吗？
