"""
截图测试 — DXGI Desktop Duplication 截图

用法: python test/test_capture.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import cv2
from src.core.dxgi_capture import DXGICapture


def main():
    print("初始化 DXGI 截图...")
    try:
        cap = DXGICapture()
    except OSError as e:
        print(f"❌ DXGI 初始化失败: {e}")
        return False

    print(f"屏幕: {cap.width}x{cap.height}")
    print("截图中...")

    img = cap.capture(timeout_ms=500)
    if img is None:
        print("❌ 截图失败（超时或无法获取帧）")
        return False

    path = "test_capture.png"
    cv2.imwrite(path, img)
    print(f"✅ 已保存: {path} ({img.shape[1]}x{img.shape[0]})")
    return True


if __name__ == "__main__":
    main()