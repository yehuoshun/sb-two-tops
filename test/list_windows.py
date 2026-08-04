"""
窗口诊断 — 列出所有窗口，方便确认游戏窗口标题
"""
import ctypes
import ctypes.wintypes

user32 = ctypes.windll.user32

def enum_cb(hwnd, _):
    if not user32.IsWindowVisible(hwnd):
        return True
    n = user32.GetWindowTextLengthW(hwnd) + 1
    b = ctypes.create_unicode_buffer(n)
    user32.GetWindowTextW(hwnd, b, n)
    if not b.value:
        return True
    # 获取窗口尺寸
    rect = ctypes.wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    w = rect.right - rect.left
    h = rect.bottom - rect.top
    if w > 100 and h > 100:  # 过滤太小的窗口
        print(f"hwnd={hwnd:>10}  {w}x{h}  \"{b.value}\"")
    return True

print("可见窗口（>100x100）：")
print(f"{'hwnd':>10}  {'尺寸':>10}  标题")
print("-" * 60)
cb = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)(enum_cb)
user32.EnumWindows(cb, 0)