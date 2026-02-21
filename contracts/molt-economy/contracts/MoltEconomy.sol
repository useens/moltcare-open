// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts-upgradeable/access/OwnableUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/security/ReentrancyGuardUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/security/PausableUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/proxy/utils/UUPSUpgradeable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

/**
 * @title MoltEconomy
 * @notice Moltbook 生态经济系统核心合约
 * @dev 可升级合约，管理所有收费和分配逻辑
 */
contract MoltEconomy is 
    OwnableUpgradeable, 
    ReentrancyGuardUpgradeable,
    PausableUpgradeable,
    UUPSUpgradeable 
{
    // ============ 错误定义 ============
    error InvalidAddress();
    error InvalidAmount();
    error ServiceNotFound();
    error InvalidDistribution();
    error TransferFailed();
    error InsufficientBalance();
    error InsufficientAllowance();
    
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
    event AddressesUpdated(address treasury, address burnAddress);
    event EmergencyWithdraw(address token, uint256 amount);
    
    // ============ 状态变量 ============
    
    IERC20 public moltToken;
    address public treasury;
    address public burnAddress;
    
    // 收费规则: serviceKey => amount
    mapping(bytes32 => uint256) public fees;
    
    // 收入统计
    uint256 public totalCollected;
    uint256 public totalBurned;
    uint256 public totalToTreasury;
    uint256 public totalToRewards;
    
    // 分配比例 (基点: 10000 = 100%)
    // 默认: 50% 销毁, 20% 国库, 30% 奖励池
    uint256 public burnRate = 5000;
    uint256 public treasuryRate = 2000;
    uint256 public rewardsRate = 3000;
    
    // ============ 初始化 ============
    
    function initialize(
        address _moltToken,
        address _treasury,
        address _burnAddress
    ) public initializer {
        if (_moltToken == address(0) || _treasury == address(0) || _burnAddress == address(0)) {
            revert InvalidAddress();
        }
        
        __Ownable_init(msg.sender);
        __ReentrancyGuard_init();
        __Pausable_init();
        __UUPSUpgradeable_init();
        
        moltToken = IERC20(_moltToken);
        treasury = _treasury;
        burnAddress = _burnAddress;
        
        // 设置初始费用 (18位小数)
        fees[keccak256("CREATE_AGENT")] = 100 * 10**18;      // 100 MOLT
        fees[keccak256("UPGRADE_PRO")] = 500 * 10**18;       // 500 MOLT
        fees[keccak256("FEATURED_DAILY")] = 50 * 10**18;     // 50 MOLT/day
        fees[keccak256("ANALYTICS_MONTHLY")] = 200 * 10**18; // 200 MOLT/month
    }
    
    // ============ 核心功能 ============
    
    /**
     * @notice 支付指定服务的费用
     * @param service 服务标识符的 keccak256 哈希
     */
    function payFee(bytes32 service) external nonReentrant whenNotPaused returns (bool) {
        uint256 amount = fees[service];
        if (amount == 0) revert ServiceNotFound();
        
        if (moltToken.balanceOf(msg.sender) < amount) revert InsufficientBalance();
        if (moltToken.allowance(msg.sender, address(this)) < amount) revert InsufficientAllowance();
        
        // 计算分配
        uint256 burnAmount = (amount * burnRate) / 10000;
        uint256 treasuryAmount = (amount * treasuryRate) / 10000;
        uint256 rewardsAmount = amount - burnAmount - treasuryAmount;
        
        // 执行转账
        bool success;
        
        success = moltToken.transferFrom(msg.sender, burnAddress, burnAmount);
        if (!success) revert TransferFailed();
        
        success = moltToken.transferFrom(msg.sender, treasury, treasuryAmount);
        if (!success) revert TransferFailed();
        
        success = moltToken.transferFrom(msg.sender, address(this), rewardsAmount);
        if (!success) revert TransferFailed();
        
        // 更新统计
        totalCollected += amount;
        totalBurned += burnAmount;
        totalToTreasury += treasuryAmount;
        totalToRewards += rewardsAmount;
        
        emit FeePaid(msg.sender, service, amount, burnAmount, treasuryAmount, rewardsAmount);
        
        return true;
    }
    
    /**
     * @notice 批量支付多个服务（Gas优化）
     * @param services 服务标识符数组
     */
    function payFeeBatch(bytes32[] calldata services) external nonReentrant whenNotPaused returns (bool) {
        uint256 totalAmount = 0;
        uint256[] memory amounts = new uint256[](services.length);
        
        for (uint i = 0; i < services.length; i++) {
            uint256 fee = fees[services[i]];
            if (fee == 0) revert ServiceNotFound();
            amounts[i] = fee;
            totalAmount += fee;
        }
        
        if (moltToken.balanceOf(msg.sender) < totalAmount) revert InsufficientBalance();
        if (moltToken.allowance(msg.sender, address(this)) < totalAmount) revert InsufficientAllowance();
        
        // 一次性转入本合约
        bool success = moltToken.transferFrom(msg.sender, address(this), totalAmount);
        if (!success) revert TransferFailed();
        
        // 内部分配
        for (uint i = 0; i < services.length; i++) {
            uint256 amount = amounts[i];
            uint256 burnAmount = (amount * burnRate) / 10000;
            uint256 treasuryAmount = (amount * treasuryRate) / 10000;
            uint256 rewardsAmount = amount - burnAmount - treasuryAmount;
            
            // 销毁部分直接转账
            success = moltToken.transfer(burnAddress, burnAmount);
            if (!success) revert TransferFailed();
            
            // 国库部分转账
            success = moltToken.transfer(treasury, treasuryAmount);
            if (!success) revert TransferFailed();
            
            // 更新统计 (奖励部分已在本合约中)
            totalCollected += amount;
            totalBurned += burnAmount;
            totalToTreasury += treasuryAmount;
            totalToRewards += rewardsAmount;
            
            emit FeePaid(msg.sender, services[i], amount, burnAmount, treasuryAmount, rewardsAmount);
        }
        
        return true;
    }
    
    // ============ 管理功能 ============
    
    /**
     * @notice 设置服务费用
     */
    function setFee(bytes32 service, uint256 amount) external onlyOwner {
        fees[service] = amount;
        emit FeeUpdated(service, amount);
    }
    
    /**
     * @notice 批量设置费用
     */
    function setFeesBatch(bytes32[] calldata services, uint256[] calldata amounts) external onlyOwner {
        require(services.length == amounts.length, "Length mismatch");
        for (uint i = 0; i < services.length; i++) {
            fees[services[i]] = amounts[i];
            emit FeeUpdated(services[i], amounts[i]);
        }
    }
    
    /**
     * @notice 设置收入分配比例
     * @param _burn 销毁比例 (基点)
     * @param _treasury 国库比例 (基点)
     * @param _rewards 奖励池比例 (基点)
     */
    function setDistribution(
        uint256 _burn,
        uint256 _treasury,
        uint256 _rewards
    ) external onlyOwner {
        if (_burn + _treasury + _rewards != 10000) revert InvalidDistribution();
        burnRate = _burn;
        treasuryRate = _treasury;
        rewardsRate = _rewards;
        emit DistributionUpdated(_burn, _treasury, _rewards);
    }
    
    /**
     * @notice 更新关键地址
     */
    function setAddresses(address _treasury, address _burnAddress) external onlyOwner {
        if (_treasury == address(0) || _burnAddress == address(0)) revert InvalidAddress();
        treasury = _treasury;
        burnAddress = _burnAddress;
        emit AddressesUpdated(_treasury, _burnAddress);
    }
    
    /**
     * @notice 提取奖励池资金（用于质押奖励分发）
     */
    function withdrawRewards(address to, uint256 amount) external onlyOwner {
        if (to == address(0)) revert InvalidAddress();
        if (amount > totalToRewards) revert InvalidAmount();
        
        bool success = moltToken.transfer(to, amount);
        if (!success) revert TransferFailed();
        
        totalToRewards -= amount;
    }
    
    /**
     * @notice 紧急暂停
     */
    function pause() external onlyOwner {
        _pause();
    }
    
    /**
     * @notice 恢复运行
     */
    function unpause() external onlyOwner {
        _unpause();
    }
    
    /**
     * @notice 紧急提取（仅限极端情况）
     */
    function emergencyWithdraw(address token, uint256 amount) external onlyOwner {
        IERC20(token).transfer(owner(), amount);
        emit EmergencyWithdraw(token, amount);
    }
    
    // ============ 查询功能 ============
    
    function getFee(bytes32 service) external view returns (uint256) {
        return fees[service];
    }
    
    function getStats() external view returns (
        uint256 collected,
        uint256 burned,
        uint256 toTreasuryAmount,
        uint256 toRewardsAmount,
        uint256 contractBalance
    ) {
        return (
            totalCollected,
            totalBurned,
            totalToTreasury,
            totalToRewards,
            moltToken.balanceOf(address(this))
        );
    }
    
    function getDistributionRates() external view returns (
        uint256 burn,
        uint256 treasury,
        uint256 rewards
    ) {
        return (burnRate, treasuryRate, rewardsRate);
    }
    
    // ============ 升级授权 ============
    
    function _authorizeUpgrade(address newImplementation) internal override onlyOwner {}
}
