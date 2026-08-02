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
|----|------|
| 截图 | PrintWindow (GDI) — 后台截图，不依赖焦点 |
| 视觉 | OpenCV 模板匹配 |
| 点击 | PostMessage — 后台消息投递，不移动鼠标 |
| 状态管理 | 页面识别器（Page pattern） |
| 打包 | PyInstaller → sihost.exe 伪装系统进程 |

## 依赖

仅 3 个：`opencv-python` `numpy` `pywin32`

## 代码结构

```
.
├── config.json                    # 配置文件
├── requirements.txt               # 依赖
├── agent.md                       # 本文件
├── design.md                      # 设计文档
├── src/
│   ├── main.py                    # 主入口
│   ├── core/
│   │   ├── screenshot.py          # PrintWindow 后台截图
│   │   ├── recognizer.py          # OpenCV 模板匹配
│   │   ├── clicker.py             # PostMessage 后台点击
│   │   └── config.py              # JSON 配置 + 坐标缩放
│   └── pages/
│       ├── base.py                # 页面基类
│       ├── home.py                # 主城页面
│       ├── dungeon.py             # 副本选择/确认
│       └── battle.py              # 战斗/结算
└── templates/                     # UI 特征图模板（待采集）
```

## 核心架构

### 主循环
```
截图(PrintWindow) → 模板匹配识别页面 → 决策 → 操作(PostMessage) → 循环
```

### 状态流转
```
主城 → 副本选择 → 确认进入 → 加载 → 战斗中(按Q) → 结算(继续挑战) → 循环
```

## 开发规范

- 注释、commit message 用中文
- 函数/类名用英文
- 仓库公开，不写任何敏感信息
- 代码修改后必须展示给用户确认后再 push

## 关键词

两个陀螺, RPA, 自动化, 图像识别, Python, OpenCV, PrintWindow, PostMessage