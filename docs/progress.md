# 开发进度 — sb-two-tops

> 最后更新: 2026-08-09

## 完成情况

### ✅ Phase 1：基础框架（已完成）
- DXGI (dxcam) 后台截图 (screenshot.py)
- OpenCV 模板匹配 + 结构检测 (recognizer.py)
- RapidOCR 识字模块 (ocr.py)
- PostMessage 后台点击/键盘 (clicker.py) — 含 WASD、技能、鼠标攻击、滚轮
- 页面识别器（pages/）
- 主循环 + 状态管理 (main.py)
- 配置管理 (config.py)

### 🚧 Phase 2：OCR 识字 + 流程联调（进行中）

#### 2026-08-09 完成
- **clicker**: 新增 `scroll()` 滚轮方法（PostMessage WM_MOUSEWHEEL）
- **recognizer**: 新增 `locate()` 全图模板定位
- **ocr**: 新增 RapidOCR 识字模块，支持区域限定搜索
- **dungeon**: `select_dungeon` 改为 OCR 识字 + 滚动重试
- **dungeon**: `_ensure_commission_mode` 委托/灾厄模式自动切换（OCR 检测）
- **main**: 集成 OCR，传入各页面模块
- **config**: 支持单目标副本配置
- **test**: 新增 `test_ocr.py` — 实时截图 + OCR 识别测试
- **cleanup**: 删除废弃 `dxgi_capture.py`、空 `__init__.py`、废弃 `templates/ensemble/`
- **docs**: 更新 README、progress.md

#### 待完成
- [ ] 采集 **确认进入** 截图 + OCR 识别确认按钮
- [ ] 采集 **结算** 截图 + OCR 识别继续按钮
- [ ] 跑通全流程（主城→副本选择→确认→战斗→结算→循环）

### ⏳ Phase 3：打包（未开始）
- PyInstaller 编译为 sihost.exe
- 使用文档

## 测试

```bash
# 激活虚拟环境
.\venv\Scripts\activate

# OCR 识别测试（游戏窗口需开着）
python test/test_ocr.py

# 查看详细 OCR 结果
python test/test_ocr.py --debug
```

## 页面检测方案

| 页面 | 检测方式 | 特征 |
|------|---------|------|
| 主城 | 图标行结构检测 | 右上角~8图标 |
| 战斗 | 双模板匹配 | "探险"+"当前轮次" |
| 副本选择 | 图标行数量 | 右上角~2图标 + OCR 识字 |

## 环境要求

- **Python**: 3.12（3.13 暂不支持，onnxruntime 无 wheel）
- **依赖**: `pip install -r requirements.txt`
- **首次运行**: RapidOCR 自动下载模型（~30MB）