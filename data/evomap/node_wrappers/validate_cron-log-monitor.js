const { spawn } = require('child_process');
const path = require('path');

const scriptPath = path.join(__dirname, 'scripts/cron-log-monitor.py');
const pythonCmd = process.env.PYTHON_CMD || 'python3';

// 验证脚本是否存在且可导入
const validation = spawn(pythonCmd, ['-c', `
import sys
sys.path.insert(0, '/root/.openclaw/workspace/scripts')
try:
    # 尝试导入模块（不执行）
    import ast
    with open('scripts/cron-log-monitor.py') as f:
        code = f.read()
    ast.parse(code)
    print('VALIDATION_PASSED: Syntax OK')
    sys.exit(0)
except Exception as e:
    print('VALIDATION_FAILED:', str(e))
    sys.exit(1)
`]);

let output = '';
validation.stdout.on('data', (data) => { output += data; });
validation.stderr.on('data', (data) => { output += data; });

validation.on('close', (code) => {
    if (code === 0 && output.includes('VALIDATION_PASSED')) {
        console.log('✓ Validation passed');
        process.exit(0);
    } else {
        console.error('✗ Validation failed:', output);
        process.exit(1);
    }
});
