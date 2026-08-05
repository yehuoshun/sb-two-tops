# sb-two-tops — 两个陀螺自动化脚本

## 项目概述

纯 Python + Win32 API 游戏自动化脚本。基于 czn-auto 的成熟架构重构。

## 开发环境

- **平台**: Linux（代码开发+语法验证）
- **运行环境**: Windows（实际运行）
- **无 Windows 测试环境**：代码的 UI 联调、ACE 检测等需在目标机器上跑
- **可验证部分**：Python 语法检查、逻辑正确性
- **禁止在开发环境安装依赖**：不做 `pip install`，只做 `ast.parse` 语法验证

## 游戏概况

动作 RPG。1 主控 + 2 AI 协战。满级账号，副本全解锁。
- 战斗：近战+远程双武器切换，技能无 CD
- 窗口化 1080p，ACE 反作弊（进程检测）
- 游戏名一律用"两个陀螺"指代

## 技术栈

| 层 | 技术 |
|--------------|------------------------------------------------------------------|
| 截图 | DXGI (dxcam) — 后台截图，支持 DirectX 窗口 |
| 视觉 | OpenCV 模板匹配 |
| 点击 | PostMessage — 后台消息投递，不移动鼠标 |
| 状态管理 | 页面识别器（Page pattern） |
| 打包 | PyInstaller → sihost.exe 伪装系统进程 |

## 依赖

仅 4 个：`opencv-python` `numpy` `pywin32` `dxcam`

## 代码结构

```
.
├── config.json                    # 配置文件
├── requirements.txt               # 依赖
├── AGENT.md                       # 本文件
├── design.md                      # 设计文档
├── progress.md                    # 开发进度
├── src/
│   ├── main.py                    # 主入口
│   ├── core/
│   │   ├── screenshot.py          # DXGI (dxcam) 后台截图
│   │   ├── recognizer.py          # OpenCV 模板匹配
│   │   ├── clicker.py             # PostMessage 后台点击/键盘
│   │   └── config.py              # JSON 配置 + 坐标缩放
│   └── pages/
│       ├── base.py                # 页面基类（抽象）
│       ├── home.py                # 主城页面
│       ├── dungeon.py             # 副本选择/确认
│       └── battle.py              # 战斗/结算
├── test/
│   └── test_detect.py             # 页面检测自包含测试
└── templates/                     # UI 特征图模板
    └── battle/
        ├── battle_tanxian.png     # "探险" 文字模板
        └── battle_dangqianlunci.png  # "当前轮次" 文字模板
```

## 核心架构

### 主循环
```
截图(dxcam) → 模板匹配识别页面 → 决策 → 操作(PostMessage) → 循环
```

### 状态流转
```
主城 → 副本选择 → 确认进入 → 加载 → 战斗中(按Q) → 结算(继续挑战) → 循环
```

## 开发规范

### 命名
- 类名：CapWords（如 `HomePage`）
- 函数/变量：snake_case（如 `click_continue`）
- 常量：UPPER_CASE（如 `VK_Q`）
- 受保护成员：`_leading_underscore`（如 `_handle_battle`）
- 注释、commit message 用中文

### 代码风格（PyCharm 零警告规则）

**必须保证 PyCharm 打开后没有任何红线、黄线、波浪线。**

#### 红线（Error）
| 问题 | 规则 |
|--------------|------------------------------------------------------------------|
| 语法错误 | 提交前 `python3 -c "import ast; ast.parse(open(f).read())"` 验证 |
| 未解析的引用 | import 路径必须正确 |
| 未定义的变量 | 变量必须先赋值再使用 |

#### 黄线（Warning）
| 检查项 | 规避方法 |
|--------------|------------------------------------------------------------------|
| 方法不用 self | 不用 self → `@staticmethod`；签名必须保留但暂未用 → `_ = self.xxx` 占位 |
| 未使用的 import | 只 import 实际用到的 |
| 未使用的变量 | 删掉，或 `_ = var` 标记为"有意不用" |
| 变量遮蔽内置名 | 不用 `list`、`dict`、`id`、`type` 等做变量名 |
| 冗余括号 | `if (x):` → `if x:` |
| 比较 None/True/False | `if x == True:` → `if x:`，`if x is None:` 正确 |

#### 代码风格（PEP 8）
- 缩进：4 空格，不用 tab
- 行宽：120 字符，不超
- 空行：类定义前 2 空行，方法前 1 空行
- import 分组：标准库 → 第三方 → 本地，每组内字母序

#### 验证命令
```bash
# 语法检查
python3 -c "import ast; ast.parse(open('src/main.py').read()); print('OK')"

# 行宽检查
awk 'length>120 {print NR": "length" chars"}' src/**/*.py

# self 未使用检查
python3 -c "
import ast, os
for root, dirs, files in os.walk('src'):
    for f in files:
        if not f.endswith('.py'): continue
        tree = ast.parse(open(os.path.join(root, f)).read())
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.args.args and item.args.args[0].arg == 'self':
                        if not any(isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == 'self' for n in ast.walk(item)):
                            print(f'{os.path.join(root, f)}:{item.lineno} {item.name}() self 未使用')
"
```

### 架构
- **单一职责**：每个文件只做一件事，避免大文件
- 核心模块放 `core/`，页面识别放 `pages/`，入口在 `main.py`
- 截图、识别、点击三者严格分离

### 安全
- 仓库公开，不写任何敏感信息
- 截图文件默认在 `.gitignore` 中排除

### 工作流
- 代码修改后先展示给用户确认，再 push
- 开发环境只做 `ast.parse` 语法验证，不装依赖

## 关键词

两个陀螺, RPA, 自动化, 图像识别, Python, OpenCV, dxcam, PostMessage