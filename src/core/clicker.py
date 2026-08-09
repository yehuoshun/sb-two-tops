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
    wm_left_button_down, wm_left_button_up,
    wm_right_button_down, wm_right_button_up,
    wm_middle_button_down, wm_middle_button_up,
    wm_mouse_move, wm_mouse_wheel,
    mk_left_button, mk_middle_button,
    cwp_skip_invisible, cwp_skip_transparent,
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

    def scroll(self, delta: int = -120, x: int = 0, y: int = 0, times: int = 1):
        """滚动鼠标滚轮

        策略: 光标移到窗口滚动区域 + SendInput 系统级滚轮 + PostMessage 窗口后台

        Args:
            delta: 单次滚动量，负值向下，正值向上，默认 -120
            x: 滚动区域 X（窗口客户区坐标）
            y: 滚动区域 Y（窗口客户区坐标）
            times: 重复次数，默认 1
        """
        sx, sy = self._scale(x, y) if x or y else (0, 0)

        # 获取窗口屏幕位置，保证光标在窗口滚动区域上
        rect = ctypes.wintypes.RECT()
        user32.GetWindowRect(self.hwnd, ctypes.byref(rect))
        screen_x = rect.left + sx
        screen_y = rect.top + sy
        logger.debug(f"scroll: window=({rect.left},{rect.top},{rect.right},{rect.bottom}) "
                     f"client=({sx},{sy}) screen=({screen_x},{screen_y})")

        for _ in range(times):
            # 光标移到窗口滚动区域（SendInput 需要光标在窗口上）
            self.move_to(screen_x, screen_y)

            # 通道1: SendInput 系统级滚轮（Unity 需要这个）
            _send_input_scroll(delta)

            # 通道2: PostMessageW 到子窗口（后台可用）
            target = self._resolve_child(sx, sy) if (sx or sy) else self.hwnd
            wparam = (delta << 16) & 0xFFFF0000
            lparam = make_lparam(sx, sy)
            user32.PostMessageW(target, wm_mouse_wheel, wparam, lparam)

            time.sleep(0.03)

    def _scale(self, x: int, y: int) -> Tuple[int, int]:
        return int(x * self.scale_x), int(y * self.scale_y)

    def _resolve_child(self, x: int, y: int) -> int:
        pt = ctypes.wintypes.POINT(x, y)
        child = user32.ChildWindowFromPointEx(
            self.hwnd, pt, cwp_skip_invisible | cwp_skip_transparent)
        return child if child else self.hwnd

    def _send_click(self, hwnd: int, x: int, y: int, button: str):
        """向指定窗口发送点击消息"""
        lparam = make_lparam(x, y)
        user32.PostMessageW(hwnd, wm_mouse_move, 0, lparam)
        time.sleep(0.02)

        if button == "left":
            user32.PostMessageW(hwnd, wm_left_button_down, mk_left_button, lparam)
            time.sleep(0.03)
            user32.PostMessageW(hwnd, wm_left_button_up, 0, lparam)
        else:
            user32.PostMessageW(hwnd, wm_right_button_down, 0, lparam)
            time.sleep(0.03)
            user32.PostMessageW(hwnd, wm_right_button_up, 0, lparam)

    def _get_window_screen_pos(self) -> Tuple[int, int]:
        """获取窗口客户区左上角在屏幕上的坐标"""
        rect = ctypes.wintypes.RECT()
        user32.GetWindowRect(self.hwnd, ctypes.byref(rect))
        # 客户区起始位置 = 窗口位置 + 标题栏偏移（通常 30px）
        # Unity 游戏通常无边框，窗口位置 ≈ 客户区位置
        return rect.left, rect.top

    def click(self, x: int, y: int, button: str = "left"):
        """在指定坐标点击（光标移动 + PostMessage 双通道）"""
        sx, sy = self._scale(x, y)
        child = self._resolve_child(sx, sy)

        # 将光标移到窗口内的正确屏幕位置
        win_left, win_top = self._get_window_screen_pos()
        screen_x = win_left + sx
        screen_y = win_top + sy
        self.move_to(screen_x, screen_y)

        logger.debug(f"click: ({x},{y}) -> scaled ({sx},{sy}) screen=({screen_x},{screen_y}) "
                     f"child={child} main={self.hwnd} btn={button}")

        # 通道1: 发到子窗口（Unity 通常有 UnityWndClass 子窗口）
        self._send_click(child, sx, sy, button)

        # 通道2: 也发到主窗口（有些游戏主窗口处理点击）
        if child != self.hwnd:
            self._send_click(self.hwnd, sx, sy, button)

    def mouse_down(self, button: str = "left"):
        """发送鼠标按下消息"""
        lparam = make_lparam(0, 0)
        if button == "left":
            user32.PostMessageW(self.hwnd, wm_left_button_down, mk_left_button, lparam)
        elif button == "right":
            user32.PostMessageW(self.hwnd, wm_right_button_down, 0, lparam)
        elif button == "middle":
            user32.PostMessageW(self.hwnd, wm_middle_button_down, mk_middle_button, lparam)

    def mouse_up(self, button: str = "left"):
        """发送鼠标松开消息"""
        lparam = make_lparam(0, 0)
        if button == "left":
            user32.PostMessageW(self.hwnd, wm_left_button_up, 0, lparam)
        elif button == "right":
            user32.PostMessageW(self.hwnd, wm_right_button_up, 0, lparam)
        elif button == "middle":
            user32.PostMessageW(self.hwnd, wm_middle_button_up, 0, lparam)
