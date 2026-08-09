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
| 视觉 | RapidOCR 识字 + OpenCV 模板匹配（备用） |
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
├── README.md                      # 使用文档
├── docs/                          # 项目文档
│   ├── AGENT.md                   # 本文件
│   ├── CODE_STYLE.md              # 开发规范（写代码前必读）
│   ├── design.md                  # 设计文档
│   └── progress.md                # 开发进度
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

## 页面检测方案

### 核心思路
灰度二值化 + 搜索区域限制 + 双模板组合匹配。

### 战斗页检测
```
截图 → 灰度 → 二值化(th=170) → 裁剪搜索区域(左中方) → 匹配"探险" + "当前轮次"
```
两个模板同时匹配才算，零误报。

### 页面检测配置
```python
DETECT_CONFIG = {
    "battle": {
        "features": ["battle_tanxian", "battle_dangqianlunci"],
        "search_box": (0.02, 0.20, 0.30, 0.18),
        "threshold": 170,
        "match_threshold": 0.7,
    }
}
```

## 按键方案

| 操作 | 按键 | 方法 |
|--------------|--------------------|--------------------|
| 攻击 | 鼠标左键 | `clicker.attack()` |
| 重击/特殊攻击 | 按住左键 | `clicker.attack_heavy()` |
| 瞄准 | 鼠标右键 | `clicker.aim()` |
| 锁定目标 | 鼠标中键 | `clicker.lock_target()` |
| 小技能 | E | `clicker.use_skill()` |
| 大招 | Q | `clicker.use_ultimate()` |
| 魔灵技能 | Z | `clicker.use_geniemon()` |
| 螺旋飞跃 | 4 | `clicker.helix_leap()` |
| 闪避 | SHIFT | `clicker.dodge()` |
| 跳跃/确认 | SPACE | `clicker.jump()` |
| 换弹/重开 | R | `clicker.reload()` |
| 移动 | WASD | `clicker.move_forward()` 等 |

## 关键词

两个陀螺, RPA, 自动化, 图像识别, Python, OpenCV, dxcam, PostMessage