"""
截图测试 — 交互式选窗口，BitBlt 屏幕截图

用法: python test/test_capture.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import ctypes
import ctypes.wintypes
import cv2
import numpy as np

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

user32.GetClassNameW.argtypes = [ctypes.wintypes.HWND, ctypes.wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowTextW.argtypes = [ctypes.wintypes.HWND, ctypes.wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowTextLengthW.argtypes = [ctypes.wintypes.HWND]
user32.IsWindowVisible.argtypes = [ctypes.wintypes.HWND]
user32.GetWindowRect.argtypes = [ctypes.wintypes.HWND, ctypes.POINTER(ctypes.wintypes.RECT)]
user32.EnumWindows.argtypes = [
    ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM),
    ctypes.wintypes.LPARAM,
]
user32.GetDC.restype = ctypes.wintypes.HDC
user32.GetDC.argtypes = [ctypes.wintypes.HWND]
user32.ReleaseDC.argtypes = [ctypes.wintypes.HWND, ctypes.wintypes.HDC]

gdi32.CreateCompatibleDC.restype = ctypes.wintypes.HDC
gdi32.CreateCompatibleDC.argtypes = [ctypes.wintypes.HDC]
gdi32.CreateCompatibleBitmap.restype = ctypes.wintypes.HBITMAP
gdi32.CreateCompatibleBitmap.argtypes = [ctypes.wintypes.HDC, ctypes.c_int, ctypes.c_int]
gdi32.SelectObject.argtypes = [ctypes.wintypes.HDC, ctypes.wintypes.HGDIOBJ]
gdi32.DeleteObject.argtypes = [ctypes.wintypes.HGDIOBJ]
gdi32.DeleteDC.argtypes = [ctypes.wintypes.HDC]
gdi32.BitBlt.argtypes = [
    ctypes.wintypes.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    ctypes.wintypes.HDC, ctypes.c_int, ctypes.c_int, ctypes.wintypes.DWORD,
]
gdi32.BitBlt.restype = ctypes.wintypes.BOOL
gdi32.GetDIBits.argtypes = [
    ctypes.wintypes.HDC, ctypes.wintypes.HBITMAP,
    ctypes.wintypes.UINT, ctypes.wintypes.UINT,
    ctypes.c_void_p, ctypes.c_void_p, ctypes.wintypes.UINT,
]
gdi32.GetDIBits.restype = ctypes.c_int

SRCCOPY = 0x00CC0020
DIB_RGB_COLORS = 0
BI_RGB = 0


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", ctypes.wintypes.DWORD),
        ("biWidth", ctypes.wintypes.LONG),
        ("biHeight", ctypes.wintypes.LONG),
        ("biPlanes", ctypes.wintypes.WORD),
        ("biBitCount", ctypes.wintypes.WORD),
        ("biCompression", ctypes.wintypes.DWORD),
        ("biSizeImage", ctypes.wintypes.DWORD),
        ("biXPelsPerMeter", ctypes.wintypes.LONG),
        ("biYPelsPerMeter", ctypes.wintypes.LONG),
        ("biClrUsed", ctypes.wintypes.DWORD),
        ("biClrImportant", ctypes.wintypes.DWORD),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [
        ("bmiHeader", BITMAPINFOHEADER),
        ("bmiColors", ctypes.wintypes.DWORD * 0),
    ]


def get_window_class(hwnd):
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buf, 256)
    return buf.value


def get_window_title(hwnd):
    n = user32.GetWindowTextLengthW(hwnd) + 1
    buf = ctypes.create_unicode_buffer(n)
    user32.GetWindowTextW(hwnd, buf, n)
    return buf.value


def get_window_rect(hwnd):
    rect = ctypes.wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return rect.left, rect.top, rect.right, rect.bottom


def list_windows():
    windows = []
    def cb(h, _):
        if not user32.IsWindowVisible(h):
            return True
        title = get_window_title(h)
        if not title:
            return True
        cls = get_window_class(h)
        left, top, right, bottom = get_window_rect(h)
        w = right - left
        h = bottom - top
        if w > 100 and h > 100:
            windows.append((h, title, cls, w, h, left, top))
        return True
    cb_type = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
    user32.EnumWindows(cb_type(cb), 0)
    return windows


def capture_screen_region(x, y, w, h):
    """BitBlt 从屏幕 DC 截取指定区域"""
    hdc_screen = user32.GetDC(0)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
    hbitmap = gdi32.CreateCompatibleBitmap(hdc_screen, w, h)
    gdi32.SelectObject(hdc_mem, hbitmap)

    ok = gdi32.BitBlt(hdc_mem, 0, 0, w, h, hdc_screen, x, y, SRCCOPY)
    if not ok:
        gdi32.DeleteObject(hbitmap)
        gdi32.DeleteDC(hdc_mem)
        user32.ReleaseDC(0, hdc_screen)
        return None

    bmp_info = BITMAPINFO()
    bmp_info.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmp_info.bmiHeader.biWidth = w
    bmp_info.bmiHeader.biHeight = -h
    bmp_info.bmiHeader.biPlanes = 1
    bmp_info.bmiHeader.biBitCount = 32
    bmp_info.bmiHeader.biCompression = BI_RGB

    pixels = (ctypes.c_ubyte * (w * h * 4))()
    gdi32.GetDIBits(hdc_mem, hbitmap, 0, h, pixels, ctypes.byref(bmp_info), DIB_RGB_COLORS)

    gdi32.DeleteObject(hbitmap)
    gdi32.DeleteDC(hdc_mem)
    user32.ReleaseDC(0, hdc_screen)

    arr = np.frombuffer(pixels, dtype=np.uint8).reshape(h, w, 4)
    return arr[:, :, :3].copy()


def main():
    windows = list_windows()
    if not windows:
        print("❌ 没有找到 >100x100 的可见窗口")
        return False

    print(f"{'#':<3} {'尺寸':<12} {'类名':<25} 标题")
    print("-" * 80)
    for i, (hwnd, title, cls, w, h, x, y) in enumerate(windows):
        # 截断长标题
        t = title[:40] + "..." if len(title) > 40 else title
        print(f"{i:<3} {w}x{h:<8} {cls:<25} {t}")

    idx = input("\n输入编号: ").strip()
    if not idx.isdigit() or int(idx) >= len(windows):
        print("❌ 无效")
        return False

    hwnd, title, cls, w, h, x, y = windows[int(idx)]
    print(f"\n选中: \"{title}\" ({cls}) {w}x{h} @ ({x},{y})")

    # 截图
    img = capture_screen_region(x, y, w, h)
    if img is None:
        print("❌ 截图失败")
        return False

    path = "test_capture.png"
    cv2.imwrite(path, img)
    print(f"✅ 已保存: {path} ({img.shape[1]}x{img.shape[0]})")
    return True


if __name__ == "__main__":
    main()