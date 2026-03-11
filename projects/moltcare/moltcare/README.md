# Moltcare

## 项目结构

```
projects/moltcare/
├── moltcare/                 # 主包
│   ├── __init__.py          # 包初始化
│   ├── cli.py               # CLI 主入口
│   ├── constants.py         # 常量定义
│   ├── utils.py             # 工具函数
│   ├── commands/            # 命令模块
│   │   ├── __init__.py
│   │   ├── init.py          # init 命令
│   │   ├── upgrade.py       # upgrade 命令
│   │   ├── doctor.py        # doctor 命令
│   │   └── backup.py        # backup/restore 命令
│   └── templates/           # 模板模块
│       ├── __init__.py      # 默认模板
│       └── default.py
├── tests/                   # 测试
│   ├── test_cli.py
│   └── README.md
├── pyproject.toml          # 项目配置
├── install.sh              # 安装脚本
├── README.md               # 项目文档
└── LICENSE                 # 许可证
```

## CLI 命令

- `moltcare init` - 交互式初始化
- `moltcare upgrade` - 智能升级
- `moltcare doctor` - 诊断检查
- `moltcare backup` - 创建备份
- `moltcare restore` - 恢复备份

## 技术栈

- Python 3.10+
- Click (CLI 框架)
- Jinja2 (模板引擎)
- pytest (测试)
