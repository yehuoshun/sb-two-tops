# 开发进度 — sb-two-tops

> 最后更新: 2026-08-05

## 完成情况

### ✅ Phase 1：基础框架（已完成）
- DXGI (dxcam) 后台截图 (screenshot.py)
- OpenCV 模板匹配 + 结构检测 (recognizer.py)
- PostMessage 后台点击/键盘 (clicker.py) — 含 WASD、技能、鼠标攻击
- 页面识别器（pages/）
- 主循环 + 状态管理 (main.py)
- 配置管理 (config.py)

### 🚧 Phase 2：模板采集 + 流程联调（进行中）

#### 2026-08-05 完成
- 截图引擎改为 **dxcam**（替代 PrintWindow）
- **战斗页检测**：双模板匹配（"探险"+"当前轮次"），零误报
- **主城检测**：右上角图标行结构检测（主城8图标 vs 战斗4图标）
- **副本选择页检测**：图标行数量检测（约2图标）+ 三个tab按钮(委托/夜航手册/委托密函)
- 自包含测试 `test/test_detect.py` — 4/4 全部通过
- 按键系统完善：WASD 走位、技能(E/Q/Z)、左键攻击、右键远程攻击、中键锁敌、螺旋飞跃(4)
- 文档拆分：`docs/AGENT.md` `CODE_STYLE.md` `design.md` `progress.md`
- 全部 PyCharm 零警告达成
- 废弃模板清理

#### 2026-08-09 完成
- **clicker**: 新增 `scroll()` 滚轮方法（PostMessage WM_MOUSEWHEEL）
- **recognizer**: 新增 `locate()` 全图模板定位，返回中心坐标
- **dungeon**: `select_dungeon` 改为模板匹配+滚动重试+回退坐标（跨调用跟踪滚动次数）
- **main**: 传截图给 `select_dungeon`，支持滚动重试流程
- **config**: 加 `dungeon.templates` 配置段，零硬编码模板路径

#### 待完成
- [ ] 裁剪 **探险·无尽** 卡片模板 → `templates/dungeon/tanxian.png`
- [ ] 采集 **确认进入** 截图 + 裁模板
- [ ] 采集 **结算** 截图 + 裁模板
- [ ] 跑通全流程

### ⏳ Phase 3：打包（未开始）
- PyInstaller 编译为 sihost.exe
- 使用文档

## 测试

```bash
# 自包含页面检测测试（无需截图）
python test/test_detect.py

# 页面检测测试（需截图）
python test/test_detect.py --image 截图.png
python test/test_detect.py --image 截图.png --debug
```

## 页面检测方案

| 页面     | 检测方式       | 特征                   |
|----------|----------------|------------------------|
| 主城     | 图标行结构检测 | 右上角~8图标           |
| 战斗     | 双模板匹配     | "探险"+"当前轮次"      |
| 副本选择 | 图标行数量     | 右上角~2图标 + tab按钮 |

## 环境问题

- **Python**: 3.13
- **GitHub**: 网络不稳定，有时无法直接 git push/pull