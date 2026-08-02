# sb-two-tops

两个陀螺自动化脚本。纯 Python + Win32 API。

## 技术栈

- **截图**: PrintWindow 后台截图
- **识别**: OpenCV 模板匹配
- **操作**: PostMessage 后台点击/键盘
- **依赖**: 仅 opencv-python + numpy + pywin32

## 快速开始

```bash
pip install -r requirements.txt
python src/main.py
```

详见 [agent.md](agent.md) 和 [design.md](design.md)。