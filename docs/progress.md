# 开发进度 — sb-two-tops

> 最后更新: 2026-08-05

## 完成情况

### ✅ Phase 1：基础框架（已完成）
- DXGI (dxcam) 后台截图 (screenshot.py)
- OpenCV 模板匹配 (recognizer.py)
- PostMessage 后台点击/键盘 (clicker.py) — 含 WASD 走位、技能、鼠标攻击
- 页面识别器基类 + 各页面桩 (pages/)
- 主循环 + 状态管理 (main.py)
- 配置管理 (config.py)

### 🚧 Phase 2：模板采集 + 流程联调（进行中）

#### 2026-08-05 本轮完成
- 截图引擎改为 **dxcam**（替代 PrintWindow），解决 DirectX 游戏黑屏问题
- 战斗页检测：双模板匹配（"探险" + "当前轮次"），灰度二值化预处理
- 自包含测试 `test/test_detect.py` — 4/4 全部通过
- 模板已部署：`templates/battle/battle_tanxian.png` + `battle_dangqianlunci.png`
- 旧模板 `btn_exit.png` 已删除
- `test/` 目录清理，旧测试文件已移除
- 按键系统完善：WASD 走位、技能(E/Q/Z)、鼠标(左键攻击/右键瞄准/中键锁敌)、螺旋飞跃(4)
- 全部 PyCharm 零警告达成

#### 待完成
- [ ] 采集 **主城** 截图 + 裁模板
- [ ] 采集 **副本选择** 截图 + 裁模板
- [ ] 采集 **确认进入** 截图 + 裁模板
- [ ] 采集 **结算** 截图 + 裁模板
- [ ] 填入各页面点击坐标到 `config.json`
- [ ] 跑通全流程

### ⏳ Phase 3：打包（未开始）
- PyCharm 编译为 sihost.exe
- 使用文档

## 测试

```bash
# 自包含页面检测测试（无需截图）
python test/test_detect.py

# 页面检测测试（需截图）
python test/test_detect.py --image 截图.png
python test/test_detect.py --image 截图.png --debug
```

## 环境问题

### Windows 开发环境
- **Python**: 3.13
- **GitHub**: 网络不稳定，有时无法直接 git push/pull