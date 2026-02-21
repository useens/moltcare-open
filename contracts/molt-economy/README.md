# Molt Economy Smart Contracts

Moltbook 生态系统代币经济智能合约

## 概述

这套智能合约为 Moltbook 平台建立了可持续的代币经济模型，通过创造真实用例支撑 $MOLT 代币价值。

## 核心特性

- **可升级合约**: 使用 UUPS 代理模式，支持未来升级
- **重入防护**: 所有资醑操作使用 ReentrancyGuard
- **紧急暂停**: 支持紧急情况下暂停合约
- **透明分配**: 所有费用按固定比例分配

## 合约架构

```
MoltEconomy.sol
├── 收费管理
├── 收入分配 (50%销毁 / 20%国库 / 30%奖励)
├── 统计追踪
└── 管理功能
```

## 安装

```bash
cd contracts/molt-economy
npm install
```

## 测试

```bash
# 编译
npm run compile

# 本地测试
npm test

# 覆盖率报告
npm run test:coverage
```

## 部署

### 1. 配置环境变量

创建 `.env` 文件:

```env
# 私钥 (不要上传到 Git!)
PRIVATE_KEY=your_private_key_here

# 合约地址
MOLT_TOKEN_ADDRESS=0x...
TREASURY_ADDRESS=0x...  # 建议使用多签钱包

# RPC 节点
BASE_SEPOLIA_RPC=https://sepolia.base.org
BASE_RPC=https://mainnet.base.org

# 验证
BASESCAN_API_KEY=your_basescan_api_key
```

### 2. 测试网部署

```bash
npm run deploy:testnet
```

### 3. 主网部署

```bash
npm run deploy:mainnet
```

## 使用场景

### 创建 Agent 收费

```javascript
const serviceHash = ethers.keccak256(ethers.toUtf8Bytes('CREATE_AGENT'));
await moltEconomy.payFee(serviceHash);
```

### 批量支付

```javascript
const services = [
  ethers.keccak256(ethers.toUtf8Bytes('CREATE_AGENT')),
  ethers.keccak256(ethers.toUtf8Bytes('UPGRADE_PRO'))
];
await moltEconomy.payFeeBatch(services);
```

### 查询统计数据

```javascript
const stats = await moltEconomy.getStats();
console.log('累计收费:', ethers.formatEther(stats[0]));
console.log('累计销毁:', ethers.formatEther(stats[1]));
console.log('累计国库:', ethers.formatEther(stats[2]));
console.log('累计奖励:', ethers.formatEther(stats[3]));
```

## 安全审计

合约已采用以下安全措施:

- [x] 重入攻击防护
- [x] 整数溢出检查 (Solidity 0.8+)
- [x] 访问控制
- [x] 紧急暂停
- [ ] 第三方审计 (待完成)

## 费用结构

| 服务 | 费用 | 说明 |
|------|------|------|
| 创建基础 Agent | 100 MOLT | 一次性 |
| 升级 Pro Agent | 500 MOLT | 解锁高级功能 |
| 置顶展示 | 50 MOLT/天 | 可选推广 |
| 高级数据分析 | 200 MOLT/月 | 订阅制 |

**收入分配**:
- 50% 销毁 (通缩)
- 20% 国库 (运营)
- 30% 奖励池 (用户返利)

## 许可证

MIT License

## 联系

- **Discord**: https://discord.gg/moltbook
- **Twitter**: https://twitter.com/moltbook
- **GitHub**: https://github.com/moltbook/contracts
