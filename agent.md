# sb-two-tops — 两个陀螺自动化脚本

## 项目概述

纯 Python RPA 方案，用于自动化"两个陀螺"游戏的操作流程。

## 开发环境

- **平台**: Linux（代码开发+验证）
- **运行环境**: Windows（实际运行）
- **无 Windows 测试环境**：代码的 UI 模板匹配联调、ACE 检测等 Windows 专属功能需在目标机器上跑
- **可验证部分**：代码逻辑、算法正确性、宏解析等在 Linux 上可测

## 游戏概况

动作 RPG，1 主控 + 2 AI 协战。满级账号，副本全解锁。
- 战斗：近战+远程双武器切换，技能无 CD，连击蓄力
- 位移：螺旋飞跃、滑铲、二段跳
- 副本类型：探险（角色突破）、皎皎币/勘探（金币）等
- 环境：Windows 客户端，窗口化 1080p，ACE 反作弊（进程检测）

## 技术栈

- 截图：mss
- 图像识别：OpenCV 模板匹配
- 输入模拟：pyautogui / win32 SendInput
- 状态管理：状态机
- 打包：PyInstaller（进程名随机化）

## 代码结构

```
.
├── screenshot.py         # 截图测试工具
├── requirements.txt      # Python 依赖
├── agent.md              # 本文件
├── design.md             # 设计文档
├── src/
│   ├── capturer.py       # 截图模块（mss）
│   ├── matcher.py        # 图像匹配模块（OpenCV 模板匹配）
│   ├── inputer.py        # 输入模拟模块（键鼠）
│   ├── state_machine.py  # 状态机引擎
│   ├── states.py         # 各页面状态定义
│   ├── combos.py         # 连招/宏指令解析
│   └── main.py           # 入口
├── templates/            # UI 特征图模板
├── config.yaml           # 配置
└── .github/workflows/
```

## 开发规范

- 注释、变量名、commit message 用中文
- 游戏名一律用"两个陀螺"指代
- 函数/类名用英文，注释用中文
- 仓库公开，不写任何敏感信息
- 截图文件默认在 `.gitignore` 中排除

## 关键词

两个陀螺, RPA, 自动化, 图像识别, Python, OpenCV, 状态机, ACE