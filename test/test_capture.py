"""
截图测试 — 验证 PrintWindow 能否截到游戏窗口

用法: python test/test_capture.py
输出: test_capture_*.png
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.screenshot import Screenshot
import cv2


def main():
    cap = Screenshot("二重螺旋")

    if not cap.find_window():
        print("❌ 未找到游戏窗口，请确保游戏正在运行")
        return False

    # 确认找到的是哪个窗口
    import ctypes
    n = ctypes.windll.user32.GetWindowTextLengthW(cap.hwnd) + 1
    b = ctypes.create_unicode_buffer(n)
    ctypes.windll.user32.GetWindowTextW(cap.hwnd, b, n)
    print(f"匹配窗口: \"{b.value}\" hwnd={cap.hwnd} {cap.width}x{cap.height}")

    img = cap.capture()
    if img is None:
        print("❌ 截图失败")
        return False

    path = "test_capture.png"
    cv2.imwrite(path, img)
    print(f"✅ 截图成功: {img.shape[1]}x{img.shape[0]}")
    print(f"   已保存: {path}")
    return True


if __name__ == "__main__":
    main()