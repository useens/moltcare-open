const hre = require('hardhat');
const { ethers, upgrades } = require('hardhat');

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log('Deploying contracts with account:', deployer.address);
  console.log('Account balance:', ethers.formatEther(await ethers.provider.getBalance(deployer.address)));

  // 配置参数
  const MOLT_TOKEN = process.env.MOLT_TOKEN_ADDRESS;
  const TREASURY = process.env.TREASURY_ADDRESS || deployer.address;
  const BURN_ADDRESS = process.env.BURN_ADDRESS || '0x000000000000000000000000000000000000dEaD';

  if (!MOLT_TOKEN) {
    console.error('Error: MOLT_TOKEN_ADDRESS not set');
    process.exit(1);
  }

  console.log('\n=== Deployment Configuration ===');
  console.log('MOLT Token:', MOLT_TOKEN);
  console.log('Treasury:', TREASURY);
  console.log('Burn Address:', BURN_ADDRESS);

  // 1. 部署 MoltEconomy 代理合约
  console.log('\n=== Deploying MoltEconomy ===');
  const MoltEconomy = await ethers.getContractFactory('MoltEconomy');
  const moltEconomy = await upgrades.deployProxy(
    MoltEconomy,
    [MOLT_TOKEN, TREASURY, BURN_ADDRESS],
    { 
      initializer: 'initialize',
      kind: 'uups'
    }
  );
  
  await moltEconomy.waitForDeployment();
  const moltEconomyAddress = await moltEconomy.getAddress();
  
  console.log('MoltEconomy deployed to:', moltEconomyAddress);
  console.log('Implementation address:', await upgrades.erc1967.getImplementationAddress(moltEconomyAddress));
  console.log('Admin address:', await upgrades.erc1967.getAdminAddress(moltEconomyAddress));

  // 2. 验证初始配置
  console.log('\n=== Verifying Initial Configuration ===');
  const stats = await moltEconomy.getStats();
  console.log('Contract MOLT balance:', ethers.formatEther(stats[4]));
  
  const distribution = await moltEconomy.getDistributionRates();
  console.log('Distribution rates:');
  console.log('  Burn:', distribution[0] / 100, '%');
  console.log('  Treasury:', distribution[1] / 100, '%');
  console.log('  Rewards:', distribution[2] / 100, '%');

  // 3. 查询初始费用
  console.log('\n=== Initial Fees ===');
  const services = [
    'CREATE_AGENT',
    'UPGRADE_PRO', 
    'FEATURED_DAILY',
    'ANALYTICS_MONTHLY'
  ];
  
  for (const service of services) {
    const fee = await moltEconomy.getFee(ethers.keccak256(ethers.toUtf8Bytes(service)));
    console.log(`${service}: ${ethers.formatEther(fee)} MOLT`);
  }

  // 保存部署信息
  const deploymentInfo = {
    network: hre.network.name,
    chainId: hre.network.config.chainId,
    moltEconomy: moltEconomyAddress,
    implementation: await upgrades.erc1967.getImplementationAddress(moltEconomyAddress),
    moltToken: MOLT_TOKEN,
    treasury: TREASURY,
    burnAddress: BURN_ADDRESS,
    deployedAt: new Date().toISOString(),
    deployer: deployer.address,
  };

  const fs = require('fs');
  fs.writeFileSync(
    `deployment-${hre.network.name}.json`,
    JSON.stringify(deploymentInfo, null, 2)
  );
  
  console.log('\n=== Deployment Info Saved ===');
  console.log(`File: deployment-${hre.network.name}.json`);

  // 4. 验证合约（如果是测试网/主网）
  if (hre.network.name !== 'hardhat') {
    console.log('\n=== Waiting for block confirmations... ===');
    await new Promise(r => setTimeout(r, 30000)); // 等待30秒
    
    try {
      console.log('Verifying contract...');
      await hre.run('verify:verify', {
        address: moltEconomyAddress,
        constructorArguments: [],
      });
      console.log('Contract verified!');
    } catch (error) {
      console.log('Verification failed:', error.message);
    }
  }

  console.log('\n=== Deployment Complete ===');
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
