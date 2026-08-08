"""
键盘模块 — PostMessage 后台按键

仅处理键盘操作（press, hold, release）。
无固定等待 — 调用方自行轮询状态。
"""

import ctypes
import ctypes.wintypes
import logging
import time
from typing import Dict

from src.core.constants import (
    WM_KEYDOWN, WM_KEYUP, resolve_vk,
)

logger = logging.getLogger("sb-two-tops.keyboard")

user32: ctypes.WinDLL = ctypes.windll.user32
user32.PostMessageW.argtypes = [
    ctypes.wintypes.HWND, ctypes.wintypes.UINT,
    ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM,
]
user32.PostMessageW.restype = ctypes.wintypes.BOOL


class Keyboard:
    """PostMessage 后台键盘操作器"""

    def __init__(self, hwnd: int):
        self.hwnd = hwnd
        self._held_keys: Dict[str, float] = {}

    def press_key(self, key, down_time: float = 0.05):
        """按下并松开按键"""
        vk = key if isinstance(key, int) else resolve_vk(str(key))
        user32.PostMessageW(self.hwnd, WM_KEYDOWN, vk, 0)
        if down_time > 0:
            time.sleep(down_time)
        user32.PostMessageW(self.hwnd, WM_KEYUP, vk, 0)

    def key_down(self, key):
        """按住按键"""
        if isinstance(key, int):
            vk = key
            key_name = str(vk)
        else:
            vk = resolve_vk(str(key))
            key_name = str(key).lower()
        user32.PostMessageW(self.hwnd, WM_KEYDOWN, vk, 0)
        self._held_keys[key_name] = time.time()

    def key_up(self, key):
        """松开按键"""
        if isinstance(key, int):
            vk = key
            key_name = str(vk)
        else:
            vk = resolve_vk(str(key))
            key_name = str(key).lower()
        user32.PostMessageW(self.hwnd, WM_KEYUP, vk, 0)
        self._held_keys.pop(key_name, None)

    def hold_key(self, key, duration: float):
        """按住按键一段时间后松开"""
        vk = key if isinstance(key, int) else resolve_vk(str(key))
        user32.PostMessageW(self.hwnd, WM_KEYDOWN, vk, 0)
        time.sleep(duration)
        user32.PostMessageW(self.hwnd, WM_KEYUP, vk, 0)

    def release_all(self):
        """松开所有按住的按键"""
        for key_name in list(self._held_keys.keys()):
            try:
                self.key_up(key_name)
            except ValueError:
                pass