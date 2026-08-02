# sb-two-tops — 两个陀螺自动化脚本

## 项目概述

纯 Python RPA 方案，用于自动化操作"两个陀螺"游戏。基于 mss 截图 + OpenCV 图像识别驱动。

## 技术栈

- **截图**: mss (高性能全屏/区域截取)
- **图像处理**: OpenCV (模板匹配、特征检测)
- **控制**: pyautogui / win32api (模拟点击、键盘)
- **运行环境**: Windows (游戏客户端所在)

## 代码结构

```
.
├── screenshot.py      # 截图测试工具
├── requirements.txt   # Python 依赖
├── agent.md           # 本文件 — 新人/Agent 快速上手指南
└── .github/workflows/ # GitHub Actions 通知
```

## 开发规范

### 命名
- 所有代码注释、变量名、commit message 用中文
- 游戏名一律用"两个陀螺"指代，不出现真实游戏名称
- 函数/类名用英文，注释用中文

### 安全
- 仓库公开，不写任何敏感信息（token、账号、密码）
- 截图文件默认在 `.gitignore` 中排除

### 截图原则
- 使用 `mss` 截图，不用 `pyautogui.screenshot()`（性能差）
- 截图区域尽量精确，减少 OpenCV 匹配范围

## 快速上手

```bash
pip install -r requirements.txt
python screenshot.py  # 验证截图功能
```

## 注意事项

- 游戏客户端可能带有 ACE 反作弊检测，操作方式需注意规避
- 纯图像识别方案，不涉及内存读写
- 仅供学习研究使用

## 关键词（Agent 索引用）

两个陀螺, RPA, 自动化, mss, OpenCV, 图像识别, 纯Python