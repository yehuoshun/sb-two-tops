# 开发进度 — sb-two-tops

> 最后更新: 2026-08-09

## 完成情况

### ✅ Phase 1：基础框架（已完成）
- MSS 后台截图 + 窗口置前 (screenshot.py)
- OpenCV 模板匹配 + 图标计数 (recognizer.py)
- RapidOCR 识字模块 (ocr.py)
- PostMessage 后台点击 + 光标移动 (clicker.py)
- SendInput + PostMessage 双通道键盘 (keyboard.py)
- 页面识别器（pages/）
- 主循环 + 状态机 (main.py)
- 配置管理 (config.py)
- 日志系统 (logging_config.py) — 控制台+文件双输出，session ID

### ✅ Phase 2：OCR 识字 + 流程联调（已完成）

#### 2026-08-09 完成
- 全流程跑通：主城 → 按 L → 滚动找扼守 → 点击 → 选难度
- 键盘双通道（SendInput + PostMessage 含扫描码 lParam）
- 鼠标点击前光标移动（SetCursorPos + PostMessage）
- 滚轮双通道（PostMessage 子窗口 + SendInput）
- 窗口置前三重降级（SetForegroundWindow → SwitchToThisWindow → AttachThreadInput）
- 页面检测全 OCR 化（去掉图标计数依赖）
- 日志系统（控制台 INFO+，文件 DEBUG+，RotatingFileHandler）
- 截图诊断（亮度、尺寸、图标计数、异常截图保存）
- 全屏 OCR dump（找不到目标时输出所有文字）
- 首次截图暗画面自动重试
- PyCharm 零警告清理

### ⏳ Phase 3：全自动循环（待开始）
- [ ] 确认进入页面 OCR 识别 + 点击
- [ ] 战斗循环（检测战斗→按 Q 技能→检测结束）
- [ ] 结算页面 OCR 识别 + 点击继续
- [ ] 完整自动循环（主城→副本→战斗→结算→重复）
- [ ] 多副本支持（配置切换）
- [ ] 异常处理（窗口丢失、ACE 检测、网络断连）

### ⏳ Phase 4：打包（未开始）
- PyInstaller 编译为 sihost.exe
- 使用文档

## 测试

```bash
# 激活虚拟环境
.\venv\Scripts\activate

# 完整流程测试（主城→选择→难度）
python test/test_dungeon_select.py

# OCR 识别测试
python test/test_ocr.py
```

## 页面检测方案

| 页面 | 检测方式 | 特征 |
|------|----------|------|
| 主城 | 图标行 ≥ 3 | 不同城市图标数不同（A城8个，B城5个） |
| 副本选择 | OCR 顶部 tab 栏 | "委托" @ (500, 40, 200, 60) |
| ESC 菜单 | OCR 中间区域 | "背包"、"商店" |
| 战斗 | 双模板匹配 | "探险"+"当前轮次" |
| 确认进入 | OCR | "确认"、"开始"、"挑战"、"进入" |
| 结算 | OCR | "继续"、"结算"、"领取" |

## 关键技术决策

### 键盘
Unity 不吃 PostMessage 键盘（lParam=0 时不认）。
-> 双通道：SendInput（真实输入）+ PostMessage（含 MapVirtualKeyW 扫描码）

### 鼠标点击
PostMessage 不移光标，Unity 可能检查光标位置。
-> SetCursorPos 先移光标再发 PostMessage，子窗口+主窗口双通道。

### 窗口置前
ACE 拦截 SetForegroundWindow。
-> 三重降级：SetForegroundWindow → SwitchToThisWindow → AttachThreadInput

### 页面检测
图标计数不同城市差异大（A城8个，B城5个）。
-> OCR 为主，图标计数阈值降低到 3 仅作辅助。

## 环境要求

- **Python**: 3.12+（onnxruntime 已支持 3.13）
- **依赖**: `pip install -r requirements.txt`（opencv, numpy, pywin32, rapidocr, onnxruntime, mss）
- **首次运行**: RapidOCR 自动下载模型（~30MB）
- **游戏**: 窗口化 1920x1080，ACE 反作弊