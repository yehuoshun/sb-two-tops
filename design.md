# 设计文档 — sb-two-tops

> 两个陀螺自动化脚本设计方案。

## 目标

副本自动化 — 探险、皎皎币等材料本全自动挂机。

## 技术选型

| 模块 | 方案 | 理由 |
|--------------|------------------------------------------------------------------|------|
| 截图 | DXGI (dxcam) | 后台截图，支持 DirectX 窗口 |
| 图像识别 | OpenCV 模板匹配 | 轻量，无额外依赖 |
| 输入模拟 | PostMessage | 后台操作，不移动鼠标，ACE 不敏感 |
| 配置 | JSON | 简单，不用额外解析库 |
| 打包 | PyInstaller → sihost.exe | 伪装系统进程 |

## 依赖

```
opencv-python  numpy  pywin32  dxcam
```

仅 4 个第三方包，最小化依赖风险。

## 架构

```
截图(dxcam) → 模板匹配识别 → 决策 → 操作(PostMessage) → 循环
```

## 状态流转

```
主城 → 副本选择 → 确认进入 → 加载 → 战斗中(按Q) → 结算(继续挑战) → 循环
```

## 代码结构

```
config.json                     # 配置
src/
├── main.py                     # 主入口
├── core/
│   ├── screenshot.py           # DXGI (dxcam) 后台截图
│   ├── recognizer.py           # OpenCV 模板匹配
│   ├── clicker.py              # PostMessage 后台点击 + 键盘
│   └── config.py               # JSON 配置 + 坐标缩放
└── pages/
    ├── base.py                 # 页面基类
    ├── home.py                 # 主城
    ├── dungeon.py              # 副本选择/确认
    └── battle.py               # 战斗/结算
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
        "search_box": (0.02, 0.20, 0.30, 0.18),  # 相对比例
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

## 开发阶段

### Phase 1：基础框架 ✅
- [x] DXGI (dxcam) 后台截图
- [x] OpenCV 模板匹配
- [x] PostMessage 后台点击/键盘
- [x] 页面识别器
- [x] 主循环

### Phase 2：模板采集 + 流程联调（当前）
- [x] 截图引擎改为 dxcam
- [x] 战斗页检测：双模板匹配（探险 + 当前轮次）
- [x] 自包含测试脚本（test/test_detect.py，4/4 通过）
- [ ] 采集主城/副本选择/确认/结算页模板
- [ ] 填入各页面点击坐标
- [ ] 跑通全流程

### Phase 3：打包
- [ ] PyInstaller 编译为 sihost.exe
- [ ] 使用文档