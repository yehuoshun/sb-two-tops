"""
键盘模块 — SendInput 前台键盘按键

仅处理键盘操作（press, hold, release）。
无固定等待 — 调用方自行轮询状态。
"""

import ctypes.wintypes
import logging
import time
from typing import Dict

from src.core.constants import resolve_vk

logger = logging.getLogger("sb-two-tops.keyboard")

user32: ctypes.WinDLL = ctypes.windll.user32


# ── SendInput 键盘 ──
# Unity 游戏不吃 PostMessage 键盘消息，需用 SendInput 发真实键盘事件


class _KeyboardInput(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.wintypes.WORD),
        ("wScan", ctypes.wintypes.WORD),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p),
    ]


class _Input(ctypes.Structure):
    _fields_ = [("type", ctypes.wintypes.DWORD), ("u", "_InputUnion")]


class _InputUnion(ctypes.Union):
    _fields_ = [("ki", _KeyboardInput)]


INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002


def _send_input_key(vk: int, key_down: bool):
    """用 SendInput 发送真实键盘事件（Unity 兼容）"""
    try:
        inp = _Input()
        inp.type = INPUT_KEYBOARD
        inp.u.ki = _KeyboardInput(vk, 0, 0 if key_down else KEYEVENTF_KEYUP, 0, ctypes.c_void_p(0))
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(_Input))
    except Exception as e:
        logger.debug(f"SendInput 键盘失败: {e}")


class Keyboard:
    """SendInput 前台键盘操作器（Unity 兼容）"""

    def __init__(self, hwnd: int):
        _ = hwnd  # API 兼容，后期可能恢复 hwnd 绑定
        self._held_keys: Dict[str, float] = {}

    @staticmethod
    def press_key(key, down_time: float = 0.05):
        """按下并松开按键（SendInput，Unity 兼容）"""
        vk = key if isinstance(key, int) else resolve_vk(str(key))
        _send_input_key(vk, True)
        if down_time > 0:
            time.sleep(down_time)
        _send_input_key(vk, False)

    def key_down(self, key):
        """按住按键（SendInput，Unity 兼容）"""
        if isinstance(key, int):
            vk = key
            key_name = str(vk)
        else:
            vk = resolve_vk(str(key))
            key_name = str(key).lower()
        _send_input_key(vk, True)
        self._held_keys[key_name] = time.time()

    def key_up(self, key):
        """松开按键（SendInput，Unity 兼容）"""
        if isinstance(key, int):
            vk = key
            key_name = str(vk)
        else:
            vk = resolve_vk(str(key))
            key_name = str(key).lower()
        _send_input_key(vk, False)
        self._held_keys.pop(key_name, None)

    @staticmethod
    def hold_key(key, duration: float):
        """按住按键一段时间后松开（SendInput，Unity 兼容）"""
        vk = key if isinstance(key, int) else resolve_vk(str(key))
        _send_input_key(vk, True)
        time.sleep(duration)
        _send_input_key(vk, False)

    def release_all(self):
        """松开所有按住的按键"""
        for key_name in list(self._held_keys.keys()):
            try:
                self.key_up(key_name)
            except ValueError:
                pass