"""
键盘模块 — SendInput + PostMessage 双通道按键

Unity 游戏不吃 PostMessage 键盘消息（lParam=0 时），
但 SendInput 需要游戏窗口在前台，ACE 可能拦截置前。

策略：两个都发，总有一个能生效。
"""

import ctypes
import logging
import time
from typing import Dict

from src.core.constants import resolve_vk, wm_key_down, wm_key_up

logger = logging.getLogger("sb-two-tops.keyboard")

user32: ctypes.WinDLL = ctypes.windll.user32


# ── 辅助函数 ──


def _make_key_lparam(vk: int, key_up: bool = False) -> int:
    """生成 WM_KEYDOWN/WM_KEYUP 的 lParam

    包含扫描码，Unity 游戏需要正确的 lParam 才能识别。
    """
    scan = user32.MapVirtualKeyW(vk, 0)  # MAPVK_VK_TO_VSC
    repeat = 1
    extended = 0
    prev_state = 1 if key_up else 0
    transition = 1 if key_up else 0
    return (
        (repeat & 0xFFFF)
        | ((scan & 0xFF) << 16)
        | (extended << 24)
        | (prev_state << 29)
        | (transition << 30)
    )


# ── 发送通道 ──


def _send_input_key(vk: int, key_down: bool):
    """通道1: SendInput 真实键盘事件（窗口需前台）"""
    try:
        class _KeyInput(ctypes.Structure):
            _fields_ = [
                ("vk_code", ctypes.c_ushort),
                ("scan_code", ctypes.c_ushort),
                ("flags", ctypes.c_ulong),
                ("timestamp", ctypes.c_ulong),
                ("extra_info", ctypes.c_void_p),
            ]

        class _KeyUnion(ctypes.Union):
            _fields_ = [("key_input", _KeyInput)]

        class _InputWrap(ctypes.Structure):
            _fields_ = [("input_type", ctypes.c_ulong), ("union_data", _KeyUnion)]

        inp = _InputWrap()
        inp.input_type = 1  # INPUT_KEYBOARD
        inp.union_data.key_input = _KeyInput(
            vk, 0, 0 if key_down else 2, 0, ctypes.c_void_p(0)
        )
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(_InputWrap))
    except Exception as e:
        logger.debug(f"SendInput 失败: {e}")


def _post_message_key(vk: int, hwnd: int, key_down: bool):
    """通道2: PostMessage 后台键盘（lParam 含扫描码）"""
    try:
        msg = wm_key_down if key_down else wm_key_up
        lparam = _make_key_lparam(vk, key_up=not key_down)
        user32.PostMessageW(hwnd, msg, vk, lparam)
    except Exception as e:
        logger.debug(f"PostMessage 失败: {e}")


def _press_key_impl(vk: int, hwnd: int, down_time: float):
    """双通道按键：SendInput + PostMessage 都发"""
    _send_input_key(vk, True)
    _post_message_key(vk, hwnd, True)
    logger.debug(f"key down: vk=0x{vk:02X}")

    if down_time > 0:
        time.sleep(down_time)

    _send_input_key(vk, False)
    _post_message_key(vk, hwnd, False)
    logger.debug(f"key up:   vk=0x{vk:02X}")


def _hold_key_impl(vk: int, hwnd: int, duration: float):
    """双通道按住：SendInput + PostMessage"""
    _send_input_key(vk, True)
    _post_message_key(vk, hwnd, True)
    logger.debug(f"key hold: vk=0x{vk:02X}")

    time.sleep(duration)

    _send_input_key(vk, False)
    _post_message_key(vk, hwnd, False)
    logger.debug(f"key release: vk=0x{vk:02X}")


# ── Keyboard 类 ──


class Keyboard:
    """双通道键盘操作器（SendInput + PostMessage）"""

    def __init__(self, hwnd: int):
        self.hwnd = hwnd
        self._held_keys: Dict[str, float] = {}

    def press_key(self, key, down_time: float = 0.05):
        """按下并松开按键"""
        vk = key if isinstance(key, int) else resolve_vk(str(key))
        _press_key_impl(vk, self.hwnd, down_time)

    def key_down(self, key):
        """按住按键"""
        if isinstance(key, int):
            vk = key
            key_name = str(vk)
        else:
            vk = resolve_vk(str(key))
            key_name = str(key).lower()
        _send_input_key(vk, True)
        _post_message_key(vk, self.hwnd, True)
        self._held_keys[key_name] = time.time()
        logger.debug(f"key down: vk=0x{vk:02X}")

    def key_up(self, key):
        """松开按键"""
        if isinstance(key, int):
            vk = key
            key_name = str(vk)
        else:
            vk = resolve_vk(str(key))
            key_name = str(key).lower()
        _send_input_key(vk, False)
        _post_message_key(vk, self.hwnd, False)
        self._held_keys.pop(key_name, None)
        logger.debug(f"key up:   vk=0x{vk:02X}")

    def hold_key(self, key, duration: float):
        """按住按键一段时间后松开"""
        vk = key if isinstance(key, int) else resolve_vk(str(key))
        _hold_key_impl(vk, self.hwnd, duration)

    def release_all(self):
        """松开所有按住的按键"""
        for key_name in list(self._held_keys.keys()):
            try:
                self.key_up(key_name)
            except ValueError:
                pass