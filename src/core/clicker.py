"""
鼠标点击模块 — PostMessage 后台点击 + SendInput 滚轮

仅处理鼠标相关操作（click, scroll, mouse_down, mouse_up）。
不涉及键盘、游戏动作。

无固定等待 — 调用方自行轮询状态来决定重试。
"""

import ctypes
import ctypes.wintypes
import logging
import time
from typing import Tuple

from src.core.constants import (
    WM_LBUTTONDOWN, WM_LBUTTONUP,
    WM_RBUTTONDOWN, WM_RBUTTONUP,
    WM_MBUTTONDOWN, WM_MBUTTONUP,
    WM_MOUSEMOVE, WM_MOUSEWHEEL,
    MK_LBUTTON, MK_MBUTTON,
    CWP_SKIPINVISIBLE, CWP_SKIPTRANSPARENT,
    make_lparam,
)

logger = logging.getLogger("sb-two-tops.clicker")

user32: ctypes.WinDLL = ctypes.windll.user32
user32.PostMessageW.argtypes = [
    ctypes.wintypes.HWND, ctypes.wintypes.UINT,
    ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM,
]
user32.PostMessageW.restype = ctypes.wintypes.BOOL
user32.ChildWindowFromPointEx.argtypes = [
    ctypes.wintypes.HWND, ctypes.wintypes.POINT, ctypes.wintypes.UINT,
]
user32.ChildWindowFromPointEx.restype = ctypes.wintypes.HWND


def _sendinput_scroll(delta: int):
    """用 SendInput 模拟真实滚轮事件"""
    try:
        from ctypes import c_uint
        from ctypes.wintypes import DWORD, LONG, WORD

        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [
                ("dx", LONG), ("dy", LONG),
                ("mouseData", DWORD), ("dwFlags", DWORD),
                ("time", DWORD), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
            ]

        class INPUT(ctypes.Structure):
            _fields_ = [("type", DWORD), ("mi", MOUSEINPUT)]

        INPUT_MOUSE = 0
        MOUSEEVENTF_WHEEL = 0x0800

        inp = INPUT()
        inp.type = INPUT_MOUSE
        inp.mi = MOUSEINPUT(0, 0, delta, MOUSEEVENTF_WHEEL, 0, None)
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
    except Exception as e:
        logger.debug(f"SendInput 滚轮失败: {e}")


class MouseClicker:
    """PostMessage 后台鼠标操作器"""

    def __init__(self, hwnd: int, scale: Tuple[float, float] = (1.0, 1.0)):
        self.hwnd = hwnd
        self.scale_x, self.scale_y = scale

    def scroll(self, delta: int = -120, x: int = 0, y: int = 0):
        """滚动鼠标滚轮（SendInput + PostMessageW 兜底）"""
        _sendinput_scroll(delta)
        wparam = (delta << 16) & 0xFFFF0000
        lparam = make_lparam(x, y)
        user32.PostMessageW(self.hwnd, WM_MOUSEWHEEL, wparam, lparam)
        time.sleep(0.03)  # 仅消抖

    def _scale(self, x: int, y: int) -> Tuple[int, int]:
        return int(x * self.scale_x), int(y * self.scale_y)

    def _resolve_child(self, x: int, y: int) -> int:
        pt = ctypes.wintypes.POINT(x, y)
        child = user32.ChildWindowFromPointEx(
            self.hwnd, pt, CWP_SKIPINVISIBLE | CWP_SKIPTRANSPARENT)
        return child if child else self.hwnd

    def click(self, x: int, y: int, button: str = "left"):
        """在指定坐标点击（后台 PostMessage）"""
        sx, sy = self._scale(x, y)
        target = self._resolve_child(sx, sy)
        lparam = make_lparam(sx, sy)

        user32.PostMessageW(target, WM_MOUSEMOVE, 0, lparam)
        time.sleep(0.02)

        if button == "left":
            user32.PostMessageW(target, WM_LBUTTONDOWN, MK_LBUTTON, lparam)
            time.sleep(0.03)
            user32.PostMessageW(target, WM_LBUTTONUP, 0, lparam)
        else:
            user32.PostMessageW(target, WM_RBUTTONDOWN, 0, lparam)
            time.sleep(0.03)
            user32.PostMessageW(target, WM_RBUTTONUP, 0, lparam)

    def mouse_down(self, button: str = "left"):
        """发送鼠标按下消息"""
        lparam = make_lparam(0, 0)
        if button == "left":
            user32.PostMessageW(self.hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lparam)
        elif button == "right":
            user32.PostMessageW(self.hwnd, WM_RBUTTONDOWN, 0, lparam)
        elif button == "middle":
            user32.PostMessageW(self.hwnd, WM_MBUTTONDOWN, MK_MBUTTON, lparam)

    def mouse_up(self, button: str = "left"):
        """发送鼠标松开消息"""
        lparam = make_lparam(0, 0)
        if button == "left":
            user32.PostMessageW(self.hwnd, WM_LBUTTONUP, 0, lparam)
        elif button == "right":
            user32.PostMessageW(self.hwnd, WM_RBUTTONUP, 0, lparam)
        elif button == "middle":
            user32.PostMessageW(self.hwnd, WM_MBUTTONUP, 0, lparam)