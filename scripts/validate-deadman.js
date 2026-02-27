const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const WORKSPACE = '/root/.openclaw/workspace';
const SCRIPT_PATH = path.join(WORKSPACE, 'scripts/deadman-switch-v2.sh');

console.log('Validating Dead Man\'s Switch System...');

// 1. 检查脚本文件存在
if (!fs.existsSync(SCRIPT_PATH)) {
    console.error('❌ Script not found:', SCRIPT_PATH);
    process.exit(1);
}
console.log('✅ Script file exists');

// 2. 检查脚本语法 (使用 bash -n)
try {
    execSync(`bash -n ${SCRIPT_PATH}`, { stdio: 'pipe' });
    console.log('✅ Bash syntax check passed');
} catch (e) {
    console.error('❌ Bash syntax error:', e.message);
    process.exit(1);
}

// 3. 检查核心函数存在
const scriptContent = fs.readFileSync(SCRIPT_PATH, 'utf8');
const requiredFunctions = [
    'save_incremental_snapshot',
    'calculate_health_score',
    'rollback_to_snapshot_v2',
    'verify_rollback'
];

for (const func of requiredFunctions) {
    if (!scriptContent.includes(`${func}()`)) {
        console.error(`❌ Missing function: ${func}`);
        process.exit(1);
    }
}
console.log('✅ All required functions present');

// 4. 检查快照目录可写
const snapshotDir = path.join(WORKSPACE, '.snapshots');
try {
    if (!fs.existsSync(snapshotDir)) {
        fs.mkdirSync(snapshotDir, { recursive: true });
    }
    const testFile = path.join(snapshotDir, '.write_test');
    fs.writeFileSync(testFile, 'test');
    fs.unlinkSync(testFile);
    console.log('✅ Snapshot directory writable');
} catch (e) {
    console.error('❌ Snapshot directory not writable:', e.message);
    process.exit(1);
}

console.log('\n✅ All validations passed!');
process.exit(0);
