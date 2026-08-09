# sb-two-tops

两个陀螺自动化脚本。纯 Python + Win32 API。

## 环境要求

- Python 3.12+（onnxruntime 已支持 3.13）
- Windows（使用 Win32 API 后台操作）

## 快速开始（Windows）

```bash
# 1. 创建虚拟环境（首次）
py -3.12 -m venv venv

# 2. 激活
.\venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行完整流程测试（游戏窗口需开着，在主城界面）
python test/test_dungeon_select.py

# 5. 运行主程序
python src/main.py
```

## 技术栈

| 模块 | 技术 |
|------|------|
| 截图 | MSS — 后台截图，兼容 DirectX 窗口 |
| 识别 | RapidOCR — 识字，自动定位点击坐标 |
| 点击 | PostMessage 后台 + SendInput 光标移动，双通道 |
| 键盘 | SendInput + PostMessage（含 lParam 扫描码），Unity 兼容 |
| 日志 | 控制台 INFO+，文件 DEBUG+，自动 RotatingFileHandler |
| 配置 | JSON — 简单，无需额外解析库 |

## 目录结构

```
config.json                 # 配置（目标副本、次数等）
requirements.txt            # 依赖
logs/                       # 日志文件 + 调试截图（自动生成）
src/
├── main.py                 # 主程序入口（状态机主循环）
├── core/
│   ├── config.py           # JSON 配置 + 坐标缩放
│   ├── screenshot.py       # MSS 后台截图 + 窗口置前
│   ├── recognizer.py       # OpenCV 模板匹配（备用识图）
│   ├── ocr.py              # RapidOCR 识字模块
│   ├── clicker.py          # PostMessage 后台点击 + 滚轮
│   ├── keyboard.py         # SendInput + PostMessage 双通道键盘
│   ├── game_controller.py  # 游戏动作控制器（组合点击+键盘）
│   └── logging_config.py   # 日志系统配置（控制台+文件，session ID）
├── pages/
│   ├── base.py             # 页面基类
│   ├── home.py             # 主城页面（图标行检测）
│   ├── dungeon.py          # 副本选择页面（OCR 检测）
│   ├── esc_menu.py         # ESC 菜单页面（OCR 检测）
│   └── battle.py           # 战斗/结算页面
├── dungeons/
│   ├── __init__.py         # 副本注册表
│   ├── base.py             # 副本基类（选择/确认/战斗/结算）
│   ├── guard.py            # 扼守 配置
│   └── explore.py          # 探险 配置
test/
├── test_dungeon_select.py  # 完整流程测试（主城→选择→难度）
└── test_ocr.py             # OCR 识别测试
templates/                  # UI 特征图模板（备用）
```

详见 [docs/AGENT.md](docs/AGENT.md)。

## 依赖

```
opencv-python>=4.9.0
numpy>=2.5.1
pywin32>=312
rapidocr
onnxruntime
mss
```

## 页面检测

基于 OCR 识字，不用图标计数。

| 页面 | 检测方式 | 特征文字 |
|------|----------|----------|
| 主城 | 图标行 ≥ 3 | 无（不同城市图标数不同） |
| 副本选择 | OCR | "委托" 在顶部 tab 栏 |
| ESC 菜单 | OCR | "背包"、"商店" |
| 战斗 | OCR + 模板匹配 | "探险" + "当前轮次" |
| 确认进入 | OCR | "确认"、"开始"、"挑战" |
| 结算 | OCR | "继续"、"结算"、"领取" |

## 输入方案

| 操作 | 技术 | 说明 |
|------|------|------|
| 键盘 | SendInput + PostMessage 双通道 | Unity 兼容，含扫描码 lParam |
| 鼠标点击 | PostMessage + SetCursorPos | 光标移动后再点，Unity 兼容 |
| 鼠标滚轮 | PostMessage 子窗口 + SendInput | 大滚动量，times 参数可配 |

## 日志

会话启动自动生成 `logs/sb-two-tops_YYYY-MM-DD_SESSIONID.log`

- 控制台: INFO+，格式 `[LEVEL] HH:MM:SS [module] message`
- 文件: DEBUG+，保留 30 天
- 调试截图: 页面未知/失败时自动保存到 `logs/`
- 全屏 OCR dump: 找不到目标时输出所有文字