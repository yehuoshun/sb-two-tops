# sb-two-tops — 两个陀螺自动化脚本

## 项目概述

纯 Python RPA 方案，用于自动化"两个陀螺"游戏的操作流程。

## 游戏概况

动作 RPG，1 主控 + 2 AI 协战。满级账号，副本全解锁。
- 战斗：近战+远程双武器切换，技能无 CD，连击蓄力
- 位移：螺旋飞跃、滑铲、二段跳
- 副本类型：委托（材料本）、沉浸式剧院（爬塔）、迷津（肉鸽）、梦魇残响（周本）
- 环境：Windows 客户端，带 ACE 反作弊

## 代码结构

```
.
├── screenshot.py      # 截图测试工具
├── requirements.txt   # Python 依赖
├── agent.md           # 本文件 — Agent 快速上手指南
├── design.md          # 设计文档
└── .github/workflows/ # GitHub Actions 通知
```

## 开发规范

### 命名
- 注释、变量名、commit message 用中文
- 游戏名一律用"两个陀螺"指代
- 函数/类名用英文，注释用中文

### 安全
- 仓库公开，不写任何敏感信息
- 截图文件默认在 `.gitignore` 中排除

### 环境
- 无测试环境，只能验证代码可行性
- 所有代码必须在 Windows 上实际运行测试

## 关键词

两个陀螺, RPA, 自动化, 图像识别, Python, OpenCV, ACE