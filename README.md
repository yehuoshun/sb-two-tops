# sb-two-tops

两个陀螺自动化脚本。纯 Python + Win32 API。

## 快速开始（Windows）

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 测试截图（游戏窗口需开着）
python test/test_capture.py

# 3. 运行主程序
python src/main.py
```

## 技术栈

- **截图**: PrintWindow 后台截图
- **识别**: OpenCV 模板匹配
- **操作**: PostMessage 后台点击/键盘
- **依赖**: 仅 opencv-python + numpy + pywin32

## 目录结构

```
config.json                 # 配置（目标副本、次数等）
src/main.py                 # 主程序入口
src/core/                   # 核心模块（截图/识别/点击/配置）
src/pages/                  # 页面识别器
test/test_capture.py        # 截图测试
test/crop_template.py       # 交互式模板裁剪
test/test_match.py          # 模板匹配验证
templates/battle/btn_exit.png  # 战斗页退出按钮模板
```

详见 [agent.md](agent.md) 和 [design.md](design.md)。