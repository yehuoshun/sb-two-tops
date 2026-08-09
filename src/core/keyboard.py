"""
键盘模块 — keybd_event 前台键盘按键

仅处理键盘操作（press, hold, release）。
无固定等待 — 调用方自行轮询状态。
"""

import ctypes
import logging
import time
from typing import Dict

from src.core.constants import resolve_vk

logger = logging.getLogger("sb-two-tops.keyboard")

user32: ctypes.WinDLL = ctypes.windll.user32


# ── keybd_event 键盘 ──
# Unity 游戏不吃 PostMessage 键盘消息，keybd_event 发真实输入


def _send_input_key(vk: int, key_down: bool):
    """用 keybd_event 发送真实键盘事件（Unity 兼容）"""
    try:
        if key_down:
            user32.keybd_event(vk, 0, 0, 0)
        else:
            user32.keybd_event(vk, 0, 2, 0)
    except Exception as e:
        logger.debug(f"keybd_event 失败: {e}")


class Keyboard:
    """keybd_event 前台键盘操作器（Unity 兼容）"""

    def __init__(self, hwnd: int):
        _ = hwnd  # API 兼容，后期可能恢复 hwnd 绑定
        self._held_keys: Dict[str, float] = {}

    @staticmethod
    def press_key(key, down_time: float = 0.05):
        """按下并松开按键"""
        vk = key if isinstance(key, int) else resolve_vk(str(key))
        _send_input_key(vk, True)
        if down_time > 0:
            time.sleep(down_time)
        _send_input_key(vk, False)

    def key_down(self, key):
        """按住按键"""
        if isinstance(key, int):
            vk = key
            key_name = str(vk)
        else:
            vk = resolve_vk(str(key))
            key_name = str(key).lower()
        _send_input_key(vk, True)
        self._held_keys[key_name] = time.time()

    def key_up(self, key):
        """松开按键"""
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
        """按住按键一段时间后松开"""
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