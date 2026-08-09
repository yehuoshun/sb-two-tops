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
    wmLeftButtonDown, wmLeftButtonUp,
    wmRightButtonDown, wmRightButtonUp,
    wmMiddleButtonDown, wmMiddleButtonUp,
    wmMouseMove, wmMouseWheel,
    mkLeftButton, mkMiddleButton,
    cwpSkipInvisible, cwpSkipTransparent,
    makeLParam,
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


def _send_input_scroll(delta: int):
    """用 SendInput 模拟真实滚轮事件"""
    try:
        from ctypes.wintypes import DWORD, LONG

        class MouseInput(ctypes.Structure):
            _fields_ = [
                ("dx", LONG), ("dy", LONG),
                ("mouseData", DWORD), ("dwFlags", DWORD),
                ("time", DWORD), ("dwExtraInfo", ctypes.c_void_p),
            ]

        class INPUT(ctypes.Structure):
            _fields_ = [("type", DWORD), ("mi", MouseInput)]

        inp = INPUT()
        inp.type = 0  # INPUT_MOUSE
        inp.mi = MouseInput(0, 0, delta, 0x0800, 0, ctypes.c_void_p(0))
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
    except Exception as e:
        logger.debug(f"SendInput 滚轮失败: {e}")


class MouseClicker:
    """PostMessage 后台鼠标操作器"""

    def __init__(self, hwnd: int, scale: Tuple[float, float] = (1.0, 1.0)):
        self.hwnd = hwnd
        self.scale_x, self.scale_y = scale

    @staticmethod
    def move_to(x: int, y: int):
        """将鼠标光标移到屏幕坐标 (x, y)（Unity 游戏需要光标在滚动区域上）"""
        user32.SetCursorPos(x, y)
        time.sleep(0.02)

    def scroll(self, delta: int = -120, x: int = 0, y: int = 0):
        """滚动鼠标滚轮（SendInput + PostMessageW 兜底）

        Args:
            delta: 滚动量，负值向下，正值向上，默认 -120
            x: 光标移到该 X 坐标后再滚动
            y: 光标移到该 Y 坐标后再滚动
        """
        # Unity 游戏需要光标在滚动区域上
        if x or y:
            self.move_to(x, y)

        _send_input_scroll(delta)
        wparam = (delta << 16) & 0xFFFF0000
        lparam = makeLParam(x, y)
        user32.PostMessageW(self.hwnd, wmMouseWheel, wparam, lparam)
        time.sleep(0.03)  # 仅消抖

    def _scale(self, x: int, y: int) -> Tuple[int, int]:
        return int(x * self.scale_x), int(y * self.scale_y)

    def _resolve_child(self, x: int, y: int) -> int:
        pt = ctypes.wintypes.POINT(x, y)
        child = user32.ChildWindowFromPointEx(
            self.hwnd, pt, cwpSkipInvisible | cwpSkipTransparent)
        return child if child else self.hwnd

    def click(self, x: int, y: int, button: str = "left"):
        """在指定坐标点击（后台 PostMessage）"""
        sx, sy = self._scale(x, y)
        target = self._resolve_child(sx, sy)
        lparam = makeLParam(sx, sy)

        user32.PostMessageW(target, wmMouseMove, 0, lparam)
        time.sleep(0.02)

        if button == "left":
            user32.PostMessageW(target, wmLeftButtonDown, mkLeftButton, lparam)
            time.sleep(0.03)
            user32.PostMessageW(target, wmLeftButtonUp, 0, lparam)
        else:
            user32.PostMessageW(target, wmRightButtonDown, 0, lparam)
            time.sleep(0.03)
            user32.PostMessageW(target, wmRightButtonUp, 0, lparam)

    def mouse_down(self, button: str = "left"):
        """发送鼠标按下消息"""
        lparam = makeLParam(0, 0)
        if button == "left":
            user32.PostMessageW(self.hwnd, wmLeftButtonDown, mkLeftButton, lparam)
        elif button == "right":
            user32.PostMessageW(self.hwnd, wmRightButtonDown, 0, lparam)
        elif button == "middle":
            user32.PostMessageW(self.hwnd, wmMiddleButtonDown, mkMiddleButton, lparam)

    def mouse_up(self, button: str = "left"):
        """发送鼠标松开消息"""
        lparam = makeLParam(0, 0)
        if button == "left":
            user32.PostMessageW(self.hwnd, wmLeftButtonUp, 0, lparam)
        elif button == "right":
            user32.PostMessageW(self.hwnd, wmRightButtonUp, 0, lparam)
        elif button == "middle":
            user32.PostMessageW(self.hwnd, wmMiddleButtonUp, 0, lparam)
