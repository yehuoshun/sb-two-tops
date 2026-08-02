"""截图测试 — 用 mss 截全屏并保存"""

import mss
import numpy as np


def capture(path: str = "screenshot.png"):
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # 主显示器
        img = sct.grab(monitor)
        arr = np.array(img)[:, :, :3]  # BGRA → BGR

        import cv2
        cv2.imwrite(path, arr)
        print(f"截图已保存: {path} ({arr.shape[1]}x{arr.shape[0]})")


if __name__ == "__main__":
    capture()