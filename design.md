# 设计文档 — sb-two-tops

> 两个陀螺自动化脚本设计方案。

## 目标

1. **副本自动化** — 探险、皎皎币等材料本全自动挂机
2. **连招自动化** — 战斗技能循环（后续阶段，从社区宏指令蒸馏）

## 技术选型

| 模块 | 方案 | 理由 |
|------|------|------|
| 截图 | PrintWindow (GDI) | 后台截图，不依赖窗口焦点 |
| 图像识别 | OpenCV 模板匹配 + PaddleOCR | 文字识别更灵活 |
| 输入模拟 | PostMessage | 后台操作，不移动鼠标，ACE 不敏感 |
| 配置 | JSON | 与 czn-auto 一致 |
| 打包 | PyInstaller → sihost.exe | 伪装系统进程，ACE 检测不到 |

## 架构

```
截图(PrintWindow) → 页面识别(OCR+模板匹配) → 决策 → 操作(PostMessage) → 循环
```

## 状态流转

```
主城 → 副本选择 → 确认进入 → 加载 → 战斗中(按Q) → 结算(继续挑战) → 循环
```

## 开发阶段

### Phase 1：基础框架 ✅
- [x] PrintWindow 后台截图
- [x] OpenCV 模板匹配 + PaddleOCR
- [x] PostMessage 后台点击/键盘
- [x] 页面识别器（Page pattern）
- [x] 宏指令解析
- [x] 主循环

### Phase 2：模板采集 + 流程联调
- [ ] 在 Windows 上采集各页面截图
- [ ] 裁剪特征图或配置 OCR 关键词
- [ ] 跑通全流程

### Phase 3：战斗优化
- [ ] 收集社区宏指令
- [ ] 高级连招解析

### Phase 4：打包
- [ ] PyInstaller 编译为 sihost.exe
- [ ] 使用文档