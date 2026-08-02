"""
点击模块 - PostMessage 后台点击

通过 PostMessage 异步投递鼠标/键盘消息到目标窗口的消息队列。
完全不移动真实鼠标，适合挂机时继续使用电脑。

实现要点：
  1. ChildWindowFromPointEx 解析坐标命中的渲染子窗口
  2. 先发 WM_MOUSEMOVE 帮助依赖 hover 状态的界面更新
  3. 坐标自动从 1920×1080 基准缩放到实际窗口尺寸

单一职责：仅处理 PostMessage 消息投递，不涉及截图或识别。
"""

import ctypes
import ctypes.wintypes
import logging
import time
from typing import Tuple

logger = logging.getLogger("sb-two-tops.clicker")

# ---------- Win32 消息常量 ----------
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205
WM_MOUSEMOVE = 0x0200
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
MK_LBUTTON = 0x0001

# ChildWindowFromPointEx 标志
CWP_SKIPINVISIBLE = 0x0001
CWP_SKIPDISABLED = 0x0002
CWP_SKIPTRANSPARENT = 0x0004

# 基准分辨率
BASE_WIDTH = 1920
BASE_HEIGHT = 1080

# ---------- ctypes 签名 ----------
user32 = ctypes.windll.user32
user32.PostMessageW.argtypes = [ctypes.wintypes.HWND, ctypes.wintypes.UINT, ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM]
user32.PostMessageW.restype = ctypes.wintypes.BOOL
user32.ChildWindowFromPointEx.argtypes = [ctypes.wintypes.HWND, ctypes.wintypes.POINT, ctypes.wintypes.UINT]
user32.ChildWindowFromPointEx.restype = ctypes.wintypes.HWND
user32.ScreenToClient.argtypes = [ctypes.wintypes.HWND, ctypes.POINTER(ctypes.wintypes.POINT)]
user32.ScreenToClient.restype = ctypes.wintypes.BOOL
user32.ClientToScreen.argtypes = [ctypes.wintypes.HWND, ctypes.POINTER(ctypes.wintypes.POINT)]
user32.ClientToScreen.restype = ctypes.wintypes.BOOL
user32.GetClientRect.argtypes = [ctypes.wintypes.HWND, ctypes.POINTER(ctypes.wintypes.RECT)]
user32.GetClientRect.restype = ctypes.wintypes.BOOL


def _make_lparam(x: int, y: int) -> int:
    """打包坐标 → LPARAM（低 16 位 x，高 16 位 y）"""
    return ((y & 0xFFFF) << 16) | (x & 0xFFFF)


class Clicker:
    """PostMessage 后台点击器"""

    def __init__(self, hwnd: int, post_click_wait_ms: int = 500, scale: Tuple[float, float] = (1.0, 1.0)):
        self.hwnd = hwnd
        self.post_click_wait_ms = post_click_wait_ms
        self.scale_x, self.scale_y = scale

    def _scale(self, x: int, y: int) -> Tuple[int, int]:
        """从基准分辨率缩放到实际窗口坐标"""
        return int(x * self.scale_x), int(y * self.scale_y)

    def _resolve_child(self, x: int, y: int) -> int:
        """解析坐标命中的子窗口句柄（Unity/UE 游戏）"""
        pt = ctypes.wintypes.POINT(x, y)
        child = user32.ChildWindowFromPointEx(self.hwnd, pt, CWP_SKIPINVISIBLE | CWP_SKIPTRANSPARENT)
        return child if child else self.hwnd

    def click(self, x: int, y: int, button: str = "left"):
        """在指定坐标点击（后台 PostMessage）"""
        sx, sy = self._scale(x, y)
        target = self._resolve_child(sx, sy)
        lparam = _make_lparam(sx, sy)

        # 先发鼠标移动
        user32.PostMessageW(target, WM_MOUSEMOVE, 0, lparam)
        time.sleep(0.02)

        # 点击
        if button == "left":
            user32.PostMessageW(target, WM_LBUTTONDOWN, MK_LBUTTON, lparam)
            time.sleep(0.03)
            user32.PostMessageW(target, WM_LBUTTONUP, 0, lparam)
        else:
            user32.PostMessageW(target, WM_RBUTTONDOWN, 0, lparam)
            time.sleep(0.03)
            user32.PostMessageW(target, WM_RBUTTONUP, 0, lparam)

        time.sleep(self.post_click_wait_ms / 1000.0)

    def press_key(self, key: int):
        """发送键盘按键消息（虚拟键码）"""
        user32.PostMessageW(self.hwnd, WM_KEYDOWN, key, 0)
        time.sleep(0.05)
        user32.PostMessageW(self.hwnd, WM_KEYUP, key, 0)
        time.sleep(self.post_click_wait_ms / 1000.0)