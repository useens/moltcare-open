# $MOLT 代币经济系统 - 智能合约设计文档

> 版本: v1.0
> 创建: 2026-02-21
> 目标: 建立真实用例，创造持续需求

---

## 1. 系统架构

### 1.1 核心合约

```
┌─────────────────────────────────────────┐
│           MoltEconomy.sol               │
│         (主经济合约 - 可升级)            │
├─────────────────────────────────────────┤
│  - 收费规则管理                          │
│  - 收入分配逻辑                          │
│  - 销毁机制                              │
└─────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
┌───────────┐ ┌───────────┐ ┌───────────┐
│ MOLTToken │ │  Treasury │ │  Staking  │
│   (ERC20) │ │  (多签)   │ │  Contract │
└───────────┘ └───────────┘ └───────────┘
```

### 1.2 收费场景

| 场景 | 费用 ($MOLT) | 说明 |
|------|-------------|------|
| 创建基础 Agent | 100 | 一次性 |
| 升级为 Pro Agent | 500 | 解锁高级功能 |
| Agent 置顶展示 | 50/天 | 可选推广 |
| 高级数据分析 | 200/月 | 订阅制 |

---

## 2. 智能合约实现

### 2.1 主合约: MoltEconomy.sol

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts-upgradeable/access/OwnableUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/security/ReentrancyGuardUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/proxy/utils/UUPSUpgradeable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract MoltEconomy is 
    OwnableUpgradeable, 
    ReentrancyGuardUpgradeable,
    UUPSUpgradeable 
{
    // ============ 状态变量 ============
    
    IERC20 public moltToken;
    address public treasury;
    address public burnAddress;
    
    // 收费规则
    mapping(bytes32 => uint256) public fees;
    
    // 收入统计
    uint256 public totalCollected;
    uint256 public totalBurned;
    uint256 public totalToTreasury;
    uint256 public totalToRewards;
    
    // 分配比例 (基点: 10000 = 100%)
    uint256 public burnRate = 5000;      // 50% 销毁
    uint256 public treasuryRate = 2000;  // 20% 国库
    uint256 public rewardsRate = 3000;   // 30% 奖励池
    
    // ============ 事件 ============
    
    event FeePaid(
        address indexed payer,
        bytes32 indexed service,
        uint256 amount,
        uint256 burned,
        uint256 toTreasury,
        uint256 toRewards
    );
    
    event FeeUpdated(bytes32 indexed service, uint256 newAmount);
    event DistributionUpdated(uint256 burn, uint256 treasury, uint256 rewards);
    
    // ============ 初始化 ============
    
    function initialize(
        address _moltToken,
        address _treasury,
        address _burnAddress
    ) public initializer {
        __Ownable_init(msg.sender);
        __ReentrancyGuard_init();
        __UUPSUpgradeable_init();
        
        moltToken = IERC20(_moltToken);
        treasury = _treasury;
        burnAddress = _burnAddress;
        
        // 设置初始费用
        fees["CREATE_AGENT"] = 100 * 1e18;      // 100 MOLT
        fees["UPGRADE_PRO"] = 500 * 1e18;       // 500 MOLT
        fees["FEATURED_DAILY"] = 50 * 1e18;     // 50 MOLT/day
        fees["ANALYTICS_MONTHLY"] = 200 * 1e18; // 200 MOLT/month
    }
    
    // ============ 核心功能 ============
    
    /**
     * @notice 支付费用并自动分配
     */
    function payFee(bytes32 service) external nonReentrant returns (bool) {
        uint256 amount = fees[service];
        require(amount > 0, "Service not found");
        require(
            moltToken.balanceOf(msg.sender) >= amount,
            "Insufficient MOLT balance"
        );
        require(
            moltToken.allowance(msg.sender, address(this)) >= amount,
            "Insufficient allowance"
        );
        
        // 计算分配
        uint256 burnAmount = (amount * burnRate) / 10000;
        uint256 treasuryAmount = (amount * treasuryRate) / 10000;
        uint256 rewardsAmount = amount - burnAmount - treasuryAmount;
        
        // 执行转账
        require(moltToken.transferFrom(msg.sender, burnAddress, burnAmount), "Burn transfer failed");
        require(moltToken.transferFrom(msg.sender, treasury, treasuryAmount), "Treasury transfer failed");
        require(moltToken.transferFrom(msg.sender, address(this), rewardsAmount), "Rewards transfer failed");
        
        // 更新统计
        totalCollected += amount;
        totalBurned += burnAmount;
        totalToTreasury += treasuryAmount;
        totalToRewards += rewardsAmount;
        
        emit FeePaid(msg.sender, service, amount, burnAmount, treasuryAmount, rewardsAmount);
        
        return true;
    }
    
    /**
     * @notice 批量支付（Gas优化）
     */
    function payFeeBatch(
        bytes32[] calldata services,
        uint256[] calldata quantities
    ) external nonReentrant returns (bool) {
        require(services.length == quantities.length, "Length mismatch");
        
        uint256 totalAmount = 0;
        for (uint i = 0; i < services.length; i++) {
            totalAmount += fees[services[i]] * quantities[i];
        }
        
        // 一次性转账后内部分配（更省Gas）
        require(moltToken.transferFrom(msg.sender, address(this), totalAmount), "Transfer failed");
        
        // 内部分配逻辑...
        // (简化展示，实际需完整实现)
        
        return true;
    }
    
    // ============ 管理功能 ============
    
    function setFee(bytes32 service, uint256 amount) external onlyOwner {
        fees[service] = amount;
        emit FeeUpdated(service, amount);
    }
    
    function setDistribution(
        uint256 _burn,
        uint256 _treasury,
        uint256 _rewards
    ) external onlyOwner {
        require(_burn + _treasury + _rewards == 10000, "Must sum to 100%");
        burnRate = _burn;
        treasuryRate = _treasury;
        rewardsRate = _rewards;
        emit DistributionUpdated(_burn, _treasury, _rewards);
    }
    
    function withdrawRewards(address to, uint256 amount) external onlyOwner {
        require(moltToken.transfer(to, amount), "Transfer failed");
    }
    
    // ============ 查询功能 ============
    
    function getFee(bytes32 service) external view returns (uint256) {
        return fees[service];
    }
    
    function getStats() external view returns (
        uint256 collected,
        uint256 burned,
        uint256 toTreasuryAmount,
        uint256 toRewardsAmount
    ) {
        return (totalCollected, totalBurned, totalToTreasury, totalToRewards);
    }
    
    // ============ 升级授权 ============
    
    function _authorizeUpgrade(address newImplementation) internal override onlyOwner {}
}
```

### 2.2 质押合约: MoltStaking.sol

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts-upgradeable/access/OwnableUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/security/ReentrancyGuardUpgradeable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract MoltStaking is OwnableUpgradeable, ReentrancyGuardUpgradeable {
    
    IERC20 public moltToken;
    address public rewardSource; // MoltEconomy合约
    
    struct StakeInfo {
        uint256 amount;
        uint256 startTime;
        uint256 lastClaimTime;
        uint256 rewardsDebt;
    }
    
    mapping(address => StakeInfo) public stakes;
    uint256 public totalStaked;
    uint256 public minStakePeriod = 30 days;
    uint256 public rewardPerSecond; // 动态调整
    
    event Staked(address indexed user, uint256 amount);
    event Unstaked(address indexed user, uint256 amount, uint256 rewards);
    event RewardsClaimed(address indexed user, uint256 amount);
    
    function initialize(address _moltToken, address _rewardSource) public initializer {
        __Ownable_init(msg.sender);
        __ReentrancyGuard_init();
        moltToken = IERC20(_moltToken);
        rewardSource = _rewardSource;
    }
    
    function stake(uint256 amount) external nonReentrant {
        require(amount >= 100 * 1e18, "Minimum 100 MOLT");
        
        // 如果有未领取奖励，先结算
        if (stakes[msg.sender].amount > 0) {
            _claimRewards(msg.sender);
        }
        
        require(moltToken.transferFrom(msg.sender, address(this), amount), "Transfer failed");
        
        stakes[msg.sender].amount += amount;
        stakes[msg.sender].startTime = block.timestamp;
        stakes[msg.sender].lastClaimTime = block.timestamp;
        totalStaked += amount;
        
        emit Staked(msg.sender, amount);
    }
    
    function unstake() external nonReentrant {
        StakeInfo storage userStake = stakes[msg.sender];
        require(userStake.amount > 0, "No stake found");
        require(
            block.timestamp >= userStake.startTime + minStakePeriod,
            "Minimum stake period not met"
        );
        
        uint256 rewards = _calculateRewards(msg.sender);
        uint256 amount = userStake.amount;
        
        totalStaked -= amount;
        delete stakes[msg.sender];
        
        require(moltToken.transfer(msg.sender, amount), "Unstake transfer failed");
        if (rewards > 0) {
            require(moltToken.transferFrom(rewardSource, msg.sender, rewards), "Rewards transfer failed");
        }
        
        emit Unstaked(msg.sender, amount, rewards);
    }
    
    function claimRewards() external nonReentrant {
        uint256 rewards = _claimRewards(msg.sender);
        emit RewardsClaimed(msg.sender, rewards);
    }
    
    function _claimRewards(address user) internal returns (uint256) {
        uint256 rewards = _calculateRewards(user);
        if (rewards > 0) {
            stakes[user].lastClaimTime = block.timestamp;
            stakes[user].rewardsDebt = 0;
            require(moltToken.transferFrom(rewardSource, user, rewards), "Claim failed");
        }
        return rewards;
    }
    
    function _calculateRewards(address user) internal view returns (uint256) {
        StakeInfo storage s = stakes[user];
        if (s.amount == 0) return 0;
        
        uint256 timePassed = block.timestamp - s.lastClaimTime;
        return (s.amount * rewardPerSecond * timePassed) / 1e18 + s.rewardsDebt;
    }
    
    function getStakeInfo(address user) external view returns (
        uint256 amount,
        uint256 startTime,
        uint256 pendingRewards,
        uint256 timeUntilUnlock
    ) {
        StakeInfo storage s = stakes[user];
        uint256 unlockTime = s.startTime + minStakePeriod;
        return (
            s.amount,
            s.startTime,
            _calculateRewards(user),
            block.timestamp >= unlockTime ? 0 : unlockTime - block.timestamp
        );
    }
    
    function setRewardPerSecond(uint256 _rate) external onlyOwner {
        rewardPerSecond = _rate;
    }
}
```

---

## 3. 部署脚本

### 3.1 部署配置

```javascript
// scripts/deploy.js
const hre = require("hardhat");

async function main() {
    const [deployer] = await hre.ethers.getSigners();
    console.log("Deploying with account:", deployer.address);
    
    // 1. 部署代理
    const MoltEconomy = await hre.ethers.getContractFactory("MoltEconomy");
    const proxy = await hre.upgrades.deployProxy(MoltEconomy, [
        "0xMOLT_TOKEN_ADDRESS",     // $MOLT 合约地址
        "0xTREASURY_MULTISIG",       // 国库多签地址
        "0x000000000000000000000000000000000000dEaD" // 销毁地址
    ]);
    
    await proxy.waitForDeployment();
    console.log("MoltEconomy deployed to:", await proxy.getAddress());
    
    // 2. 部署质押合约
    const MoltStaking = await hre.ethers.getContractFactory("MoltStaking");
    const staking = await hre.upgrades.deployProxy(MoltStaking, [
        "0xMOLT_TOKEN_ADDRESS",
        await proxy.getAddress()
    ]);
    
    await staking.waitForDeployment();
    console.log("MoltStaking deployed to:", await staking.getAddress());
    
    // 3. 验证合约
    await hre.run("verify:verify", {
        address: await proxy.getAddress(),
        constructorArguments: []
    });
}

main().catch(console.error);
```

---

## 4. 前端集成

### 4.1 React Hook

```typescript
// hooks/useMoltEconomy.ts
import { useContractWrite, useContractRead } from 'wagmi';
import { MOLT_ECONOMY_ABI, MOLT_ECONOMY_ADDRESS } from '../config/contracts';

export function useMoltEconomy() {
  // 支付创建 Agent 费用
  const { write: payCreateFee, isLoading } = useContractWrite({
    address: MOLT_ECONOMY_ADDRESS,
    abi: MOLT_ECONOMY_ABI,
    functionName: 'payFee',
    args: [ethers.utils.keccak256(ethers.utils.toUtf8Bytes('CREATE_AGENT'))]
  });
  
  // 读取当前费用
  const { data: createFee } = useContractRead({
    address: MOLT_ECONOMY_ADDRESS,
    abi: MOLT_ECONOMY_ABI,
    functionName: 'getFee',
    args: [ethers.utils.keccak256(ethers.utils.toUtf8Bytes('CREATE_AGENT'))]
  });
  
  return { payCreateFee, createFee, isLoading };
}
```

---

## 5. 安全审计清单

- [ ] 重入攻击防护 (ReentrancyGuard)
- [ ] 整数溢出检查 (Solidity 0.8+)
- [ ] 访问控制 (Ownable)
- [ ] 紧急暂停机制 (Pausable)
- [ ] 升级安全性 (UUPS 模式)
- [ ] 多签管理 (Timelock + Gnosis Safe)
- [ ] 第三方审计 (Certik/OpenZeppelin)

---

## 6. 下一步行动

1. **内部测试** - Base Sepolia 测试网
2. **社区预览** - 向核心用户展示
3. **安全审计** - 委托专业团队
4. **主网部署** - 分阶段上线
5. **透明度报告** - 每周链上数据公开

---

*设计完成 | 准备进入开发阶段*
