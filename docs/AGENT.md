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
| 截图 | MSS — 后台截图，兼容 DirectX 窗口 |
| 视觉 | RapidOCR 识字（主）+ OpenCV 模板匹配（备用） |
| 点击 | PostMessage 后台 + SetCursorPos 光标移动 |
| 键盘 | SendInput + PostMessage 双通道（含扫描码 lParam） |
| 状态管理 | 页面识别器（Page pattern）+ OCR 检测 |
| 日志 | 控制台 INFO+ + 文件 DEBUG+，RotatingFileHandler |
| 打包 | PyInstaller → sihost.exe 伪装系统进程（计划） |

## 依赖

```
opencv-python>=4.9.0
numpy>=2.5.1
pywin32>=312
rapidocr
onnxruntime
mss
```

## 代码结构

```
.
├── config.json                    # 配置文件
├── requirements.txt               # 依赖
├── README.md                      # 使用文档
├── docs/                          # 项目文档
│   ├── AGENT.md                   # 本文件
│   ├── CODE_STYLE.md              # 开发规范
│   └── progress.md                # 开发进度
├── logs/                          # 日志 + 调试截图（自动生成）
├── src/
│   ├── main.py                    # 主入口（状态机主循环）
│   ├── core/
│   │   ├── config.py              # JSON 配置 + 坐标缩放
│   │   ├── screenshot.py          # MSS 后台截图 + 窗口置前
│   │   ├── recognizer.py          # OpenCV 模板匹配 + 图标计数
│   │   ├── ocr.py                 # RapidOCR 识字模块
│   │   ├── clicker.py             # PostMessage 点击 + 滚轮
│   │   ├── keyboard.py            # SendInput + PostMessage 双通道键盘
│   │   ├── game_controller.py     # 游戏动作控制器
│   │   ├── constants.py           # Win32 消息常量与虚拟键码
│   │   └── logging_config.py      # 日志系统配置
│   ├── pages/
│   │   ├── base.py                # 页面基类
│   │   ├── home.py                # 主城页面（图标行检测）
│   │   ├── dungeon.py             # 副本选择/确认
│   │   ├── esc_menu.py            # ESC 菜单页面
│   │   └── battle.py              # 战斗/结算
│   └── dungeons/
│       ├── __init__.py            # 副本注册表
│       ├── base.py                # 副本基类（选择→确认→战斗→结算）
│       ├── guard.py               # 扼守 配置
│       └── explore.py             # 探险 配置
├── test/
│   ├── test_dungeon_select.py     # 完整流程测试
│   └── test_ocr.py                # OCR 识别测试
└── templates/                     # UI 特征图模板
    └── battle/
        ├── battle_tanxian.png     # "探险" 文字模板
        └── battle_dangqianlunci.png  # "当前轮次" 文字模板
```

## 核心架构

### 主循环
```
截图(MSS) → OCR 识别页面 → 决策 → 操作(PostMessage + SendInput) → 循环
```

### 状态流转
```
主城 → 副本选择 → 确认进入 → 加载 → 战斗(按Q) → 结算(继续挑战) → 循环
```

## 页面检测方案

### 核心思路
OCR 识字为主，图标计数为辅。

### 主城检测
```
图标行 ≥ 3（阈值低覆盖不同城市，A城8个，B城5个）
```

### 副本选择页检测
```
OCR 在顶部 tab 栏区域 (500, 40, 200, 60) 搜索"委托"
```

### 战斗页检测
```
灰度二值化(th=170) → 裁剪搜索区域(左中方) → 匹配"探险"+"当前轮次"
两个模板同时匹配才算，零误报。
```

### ESC 菜单检测
```
OCR 在 (200, 150, 800, 300) 搜索"背包"或"商店"
```

## 输入方案

### 键盘
Unity 游戏不吃 PostMessage 键盘消息（lParam=0 时）。
**双通道策略：** 每次按键 SendInput（真实输入）+ PostMessage（含正确的扫描码 lParam）。

### 鼠标点击
PostMessage 只发消息不移光标，Unity 游戏可能检查实际光标位置。
**策略：** 先 SetCursorPos 到 `(窗口左+点击X, 窗口顶+点击Y)`，再发 PostMessage 到子窗口和主窗口。

### 鼠标滚轮
PostMessage 到子窗口 + SendInput 系统级滚轮。`times` 参数控制重复次数。

## 日志系统

会话启动自动生成 `logs/sb-two-tops_YYYY-MM-DD_SESSIONID.log`

```
[INFO] 2026-08-09 19:30:00 [sb-two-tops.test.dungeon_select] Step 1/3: 前往副本菜单
[DEBUG] 2026-08-09 19:30:00 [sb-two-tops.screenshot] 截图: 1920x1080 mean=42 region=(0,0,1920,1080)
[DEBUG] 2026-08-09 19:30:00 [sb-two-tops.pages.home] home.detect: icons=8 threshold=3 result=True
```

- 未知页面自动保存截图到 `logs/debug_TIMESTAMP_unknown_page.png`
- 找不到目标时自动 dump 全屏 OCR 文字
- 截图亮度异常（mean<30 或全黑）自动重试

## 按键方案

| 操作 | 按键 | 方法 |
|------|------|------|
| 攻击 | 鼠标左键 | `controller.attack()` |
| 重击/特殊攻击 | 按住左键 | `controller.attack_heavy()` |
| 瞄准 | 鼠标右键 | `controller.ranged_attack()` |
| 小技能 | E | `controller.use_skill()` |
| 大招 | Q | `controller.use_ultimate()` |
| 魔灵技能 | Z | `controller.use_monster()` |
| 螺旋飞跃 | 4 | `controller.helix_leap()` |
| 闪避 | SHIFT | `controller.dodge()` |
| 跳跃/确认 | SPACE | `controller.jump()` |
| 换弹/重开 | R | `controller.reload()` |
| 移动 | WASD | `controller.move_forward()` 等 |
| 打开副本菜单 | L | 在主城按 L |
| 关闭菜单 | ESC | `controller.press_key("ESC")` |

## 环境要求

- **Python**: 3.12+（onnxruntime 已支持 3.13）
- **依赖**: `pip install -r requirements.txt`
- **首次运行**: RapidOCR 自动下载模型（~30MB）
- **游戏**: 窗口化 1920x1080，ACE 反作弊

## 关键词

两个陀螺, RPA, 自动化, 图像识别, Python, OpenCV, MSS, RapidOCR, PostMessage, SendInput