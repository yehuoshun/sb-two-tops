# 设计文档 — sb-two-tops

> 两个陀螺自动化脚本设计方案。

## 目标

副本自动化 — 探险、皎皎币等材料本全自动挂机。

## 技术选型

| 模块 | 方案 | 理由 |
|------|------|------|
| 截图 | PrintWindow (GDI) | 后台截图，不依赖窗口焦点 |
| 图像识别 | OpenCV 模板匹配 | 轻量，无额外依赖 |
| 输入模拟 | PostMessage | 后台操作，不移动鼠标，ACE 不敏感 |
| 配置 | JSON | 简单，不用额外解析库 |
| 打包 | PyInstaller → sihost.exe | 伪装系统进程 |

## 依赖

```
opencv-python  numpy  pywin32
```

仅 3 个第三方包，最小化依赖风险。

## 架构

```
截图(PrintWindow) → 模板匹配识别 → 决策 → 操作(PostMessage) → 循环
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
│   ├── screenshot.py           # PrintWindow 后台截图
│   ├── recognizer.py           # OpenCV 模板匹配
│   ├── clicker.py              # PostMessage 后台点击
│   └── config.py               # JSON 配置 + 坐标缩放
└── pages/
    ├── base.py                 # 页面基类
    ├── home.py                 # 主城
    ├── dungeon.py              # 副本选择/确认
    └── battle.py               # 战斗/结算
```

## 开发阶段

### Phase 1：基础框架 ✅
- [x] PrintWindow 后台截图
- [x] OpenCV 模板匹配
- [x] PostMessage 后台点击/键盘
- [x] 页面识别器
- [x] 主循环

### Phase 2：模板采集 + 流程联调（当前）
- [ ] 在 Windows 上截取各页面特征图
- [ ] 裁剪模板填入 pages/
- [ ] 跑通全流程

### Phase 3：打包
- [ ] PyInstaller 编译为 sihost.exe
- [ ] 使用文档