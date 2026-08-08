# sb-two-tops

两个陀螺自动化脚本。纯 Python + Win32 API。

## 环境要求

- Python 3.12（3.13 暂不支持，因 onnxruntime 无 3.13 wheel）
- Windows（使用 Win32 API 后台操作）

## 快速开始（Windows）

```bash
# 1. 创建虚拟环境（首次）
py -3.12 -m venv venv

# 2. 激活
.\venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行测试（游戏窗口需开着）
python test/test_ocr.py

# 5. 运行主程序
python src/main.py
```

## 技术栈

| 模块 | 技术 |
|------|------|
| 截图 | DXGI (dxcam) — 后台截图，支持 DirectX 窗口 |
| 识别 | RapidOCR — 识字，自动定位点击坐标 |
| 操作 | PostMessage — 后台消息投递，不移动鼠标 |
| 配置 | JSON — 简单，无需额外解析库 |

## 目录结构

```
config.json                 # 配置（目标副本、次数等）
requirements.txt            # 依赖
src/
├── main.py                 # 主程序入口
├── core/
│   ├── screenshot.py       # DXGI (dxcam) 后台截图
│   ├── recognizer.py       # OpenCV 模板匹配（备用识图）
│   ├── ocr.py              # RapidOCR 识字模块
│   ├── clicker.py          # PostMessage 后台点击/键盘
│   └── config.py           # JSON 配置 + 坐标缩放
└── pages/
    ├── base.py             # 页面基类
    ├── home.py             # 主城页面
    ├── dungeon.py          # 副本选择页面
    └── battle.py           # 战斗/结算页面
test/
└── test_ocr.py             # OCR 识别测试
templates/
└── battle/                 # 战斗页模板（备用识图用）
```

详见 [docs/AGENT.md](docs/AGENT.md) 和 [docs/design.md](docs/design.md)。