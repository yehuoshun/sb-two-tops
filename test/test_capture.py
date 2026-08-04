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
    import ctypes
    import ctypes.wintypes
    user32 = ctypes.windll.user32

    # 先列出所有候选窗口
    windows = []
    def cb(h, _):
        if not user32.IsWindowVisible(h):
            return True
        n = user32.GetWindowTextLengthW(h) + 1
        b = ctypes.create_unicode_buffer(n)
        user32.GetWindowTextW(h, b, n)
        if not b.value:
            return True
        rect = ctypes.wintypes.RECT()
        user32.GetWindowRect(h, ctypes.byref(rect))
        w = rect.right - rect.left
        h = rect.bottom - rect.top
        if w > 200 and h > 200:
            windows.append((h, b.value, w, h))
        return True

    cb_type = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
    user32.EnumWindows(cb_type(cb), 0)

    print("选择窗口:")
    for i, (hwnd, title, w, h) in enumerate(windows):
        print(f"  [{i}] {w}x{h}  \"{title}\"")

    idx = input("\n输入编号: ").strip()
    if not idx.isdigit() or int(idx) >= len(windows):
        print("❌ 无效")
        return False

    hwnd = windows[int(idx)][0]

    # 直接用指定 hwnd 截图
    from src.core.screenshot import Screenshot
    cap = Screenshot("")
    cap.hwnd = hwnd
    cap._update_size()

    print(f"截图: {cap.width}x{cap.height}")
    img = cap.capture()
    if img is None:
        print("❌ 截图失败")
        return False

    import cv2
    path = "test_capture.png"
    cv2.imwrite(path, img)
    print(f"✅ 已保存: {path}")
    return True


if __name__ == "__main__":
    main()