# 设计文档 — sb-two-tops

> 两个陀螺自动化脚本设计方案。

## 目标

副本自动化 — 探险、皎皎币等材料本全自动挂机。

## 技术选型

| 模块 | 方案 | 理由 |
|--------------|------------------------------------------------------------------|------|
| 截图 | DXGI (dxcam) | 后台截图，支持 DirectX 窗口 |
| 图像识别 | RapidOCR 识字 + OpenCV 模板匹配（备用） | 识字为主，自定点击坐标，模板匹配备用 |
| 输入模拟 | PostMessage | 后台操作，不移动鼠标，ACE 不敏感 |
| 配置 | JSON | 简单，不用额外解析库 |
| 打包 | PyInstaller → sihost.exe | 伪装系统进程 |

## 依赖

```
opencv-python  numpy  pywin32  dxcam
```

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
config.json
src/
├── main.py
├── core/
│   ├── screenshot.py
│   ├── recognizer.py
│   ├── clicker.py
│   └── config.py
└── pages/
    ├── base.py
    ├── home.py
    ├── dungeon.py
    └── battle.py
```

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