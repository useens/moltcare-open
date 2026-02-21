const { expect } = require('chai');
const { ethers, upgrades } = require('hardhat');

describe('MoltEconomy', function () {
  let moltEconomy;
  let moltToken;
  let owner;
  let user;
  let treasury;
  let burnAddress;

  const INITIAL_SUPPLY = ethers.parseEther('1000000'); // 1M MOLT
  const SERVICE_CREATE = ethers.keccak256(ethers.toUtf8Bytes('CREATE_AGENT'));
  const SERVICE_UPGRADE = ethers.keccak256(ethers.toUtf8Bytes('UPGRADE_PRO'));

  beforeEach(async function () {
    [owner, user, treasury, burnAddress] = await ethers.getSigners();

    // 部署模拟 MOLT 代币
    const MockToken = await ethers.getContractFactory('MockMOLT');
    moltToken = await MockToken.deploy('MOLT Token', 'MOLT', INITIAL_SUPPLY);
    await moltToken.waitForDeployment();

    // 给用户转一些代币
    await moltToken.transfer(user.address, ethers.parseEther('10000'));

    // 部署 MoltEconomy
    const MoltEconomy = await ethers.getContractFactory('MoltEconomy');
    moltEconomy = await upgrades.deployProxy(
      MoltEconomy,
      [await moltToken.getAddress(), treasury.address, burnAddress.address],
      { initializer: 'initialize' }
    );
    await moltEconomy.waitForDeployment();

    // 用户授权合约使用代币
    await moltToken.connect(user).approve(await moltEconomy.getAddress(), ethers.MaxUint256);
  });

  describe('Deployment', function () {
    it('Should set the right owner', async function () {
      expect(await moltEconomy.owner()).to.equal(owner.address);
    });

    it('Should set correct initial fees', async function () {
      const createFee = await moltEconomy.getFee(SERVICE_CREATE);
      expect(createFee).to.equal(ethers.parseEther('100'));

      const upgradeFee = await moltEconomy.getFee(SERVICE_UPGRADE);
      expect(upgradeFee).to.equal(ethers.parseEther('500'));
    });

    it('Should set correct distribution rates', async function () {
      const [burn, treasuryRate, rewards] = await moltEconomy.getDistributionRates();
      expect(burn).to.equal(5000); // 50%
      expect(treasuryRate).to.equal(2000); // 20%
      expect(rewards).to.equal(3000); // 30%
    });
  });

  describe('Pay Fee', function () {
    it('Should allow user to pay fee', async function () {
      const feeAmount = ethers.parseEther('100');
      const burnAmount = (feeAmount * 5000n) / 10000n; // 50%
      const treasuryAmount = (feeAmount * 2000n) / 10000n; // 20%
      const rewardsAmount = feeAmount - burnAmount - treasuryAmount; // 30%

      const userBalanceBefore = await moltToken.balanceOf(user.address);
      const treasuryBalanceBefore = await moltToken.balanceOf(treasury.address);

      await expect(moltEconomy.connect(user).payFee(SERVICE_CREATE))
        .to.emit(moltEconomy, 'FeePaid')
        .withArgs(
          user.address,
          SERVICE_CREATE,
          feeAmount,
          burnAmount,
          treasuryAmount,
          rewardsAmount
        );

      // 验证用户余额减少
      const userBalanceAfter = await moltToken.balanceOf(user.address);
      expect(userBalanceBefore - userBalanceAfter).to.equal(feeAmount);

      // 验证国库收到
      const treasuryBalanceAfter = await moltToken.balanceOf(treasury.address);
      expect(treasuryBalanceAfter - treasuryBalanceBefore).to.equal(treasuryAmount);

      // 验证统计更新
      const stats = await moltEconomy.getStats();
      expect(stats[0]).to.equal(feeAmount); // totalCollected
      expect(stats[1]).to.equal(burnAmount); // totalBurned
      expect(stats[2]).to.equal(treasuryAmount); // totalToTreasury
      expect(stats[3]).to.equal(rewardsAmount); // totalToRewards
    });

    it('Should reject if service not found', async function () {
      const invalidService = ethers.keccak256(ethers.toUtf8Bytes('INVALID'));
      await expect(
        moltEconomy.connect(user).payFee(invalidService)
      ).to.be.revertedWithCustomError(moltEconomy, 'ServiceNotFound');
    });

    it('Should reject if insufficient balance', async function () {
      // 创建一个没有代币的用户
      const [, , , , poorUser] = await ethers.getSigners();
      await expect(
        moltEconomy.connect(poorUser).payFee(SERVICE_CREATE)
      ).to.be.revertedWithCustomError(moltEconomy, 'InsufficientBalance');
    });
  });

  describe('Admin Functions', function () {
    it('Should allow owner to set fee', async function () {
      const newFee = ethers.parseEther('200');
      await expect(moltEconomy.setFee(SERVICE_CREATE, newFee))
        .to.emit(moltEconomy, 'FeeUpdated')
        .withArgs(SERVICE_CREATE, newFee);

      expect(await moltEconomy.getFee(SERVICE_CREATE)).to.equal(newFee);
    });

    it('Should allow owner to set distribution', async function () {
      await moltEconomy.setDistribution(4000, 3000, 3000);
      
      const [burn, treasury, rewards] = await moltEconomy.getDistributionRates();
      expect(burn).to.equal(4000);
      expect(treasury).to.equal(3000);
      expect(rewards).to.equal(3000);
    });

    it('Should reject invalid distribution', async function () {
      await expect(
        moltEconomy.setDistribution(5000, 5000, 1000)
      ).to.be.revertedWithCustomError(moltEconomy, 'InvalidDistribution');
    });

    it('Should not allow non-owner to set fee', async function () {
      await expect(
        moltEconomy.connect(user).setFee(SERVICE_CREATE, ethers.parseEther('200'))
      ).to.be.revertedWithCustomError(moltEconomy, 'OwnableUnauthorizedAccount');
    });

    it('Should allow owner to pause and unpause', async function () {
      await moltEconomy.pause();
      
      await expect(
        moltEconomy.connect(user).payFee(SERVICE_CREATE)
      ).to.be.revertedWithCustomError(moltEconomy, 'EnforcedPause');

      await moltEconomy.unpause();
      
      // 应该可以正常支付了
      await expect(moltEconomy.connect(user).payFee(SERVICE_CREATE)).to.not.be.reverted;
    });
  });

  describe('Pay Fee Batch', function () {
    it('Should allow batch payment', async function () {
      const services = [SERVICE_CREATE, SERVICE_UPGRADE];
      const createFee = ethers.parseEther('100');
      const upgradeFee = ethers.parseEther('500');
      const totalFee = createFee + upgradeFee;

      const userBalanceBefore = await moltToken.balanceOf(user.address);

      await expect(moltEconomy.connect(user).payFeeBatch(services))
        .to.emit(moltEconomy, 'FeePaid')
        .to.emit(moltEconomy, 'FeePaid');

      const userBalanceAfter = await moltToken.balanceOf(user.address);
      expect(userBalanceBefore - userBalanceAfter).to.equal(totalFee);

      // 验证统计
      const stats = await moltEconomy.getStats();
      expect(stats[0]).to.equal(totalFee);
    });
  });
});
