"""
点击模块 - PostMessage 后台点击 + 键盘

通过 PostMessage 异步投递鼠标/键盘消息到目标窗口的消息队列。
完全不移动真实鼠标，适合挂机时继续使用电脑。

单一职责：仅处理 PostMessage 消息投递，不涉及截图或识别。
"""

import ctypes
import ctypes.wintypes
import logging
import time
from typing import Dict, Tuple

logger = logging.getLogger("sb-two-tops.clicker")

# ---------- Win32 消息常量 ----------
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205
WM_MBUTTONDOWN = 0x0207
WM_MBUTTONUP = 0x0208
WM_MOUSEMOVE = 0x0200
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
MK_LBUTTON = 0x0001
MK_MBUTTON = 0x0010

# ---------- 虚拟键码 ----------
VK = {
    # 字母
    "A": 0x41, "B": 0x42, "C": 0x43, "D": 0x44,
    "E": 0x45, "F": 0x46, "G": 0x47, "H": 0x48,
    "I": 0x49, "J": 0x4A, "K": 0x4B, "L": 0x4C,
    "M": 0x4D, "N": 0x4E, "O": 0x4F, "P": 0x50,
    "Q": 0x51, "R": 0x52, "S": 0x53, "T": 0x54,
    "U": 0x55, "V": 0x56, "W": 0x57, "X": 0x58,
    "Y": 0x59, "Z": 0x5A,
    # 数字
    "0": 0x30, "1": 0x31, "2": 0x32, "3": 0x33,
    "4": 0x34, "5": 0x35, "6": 0x36, "7": 0x37,
    "8": 0x38, "9": 0x39,
    # 功能键
    "SPACE": 0x20,
    "SHIFT": 0x10,
    "CTRL": 0x11,
    "ALT": 0x12,
    "TAB": 0x09,
    "ESC": 0x1B,
    "ENTER": 0x0D,
    "BACK": 0x08,
    "LSHIFT": 0xA0,
    "RSHIFT": 0xA1,
    "LCONTROL": 0xA2,
    "RCONTROL": 0xA3,
    "LALT": 0xA4,
    "RALT": 0xA5,
}

# 游戏常用键别名
GAME_KEYS = {
    "w": "W", "a": "A", "s": "S", "d": "D",
    "e": "E", "q": "Q", "z": "Z", "r": "R",
    "space": "SPACE", "空格": "SPACE",
    "shift": "SHIFT", "闪避": "SHIFT",
    "ctrl": "CTRL", "下蹲": "CTRL",
    "tab": "TAB", "esc": "ESC",
    "螺旋飞跃": "4", "helix": "4",
}

# ---------- ctypes ----------
_CWP_SKIPINVISIBLE = 0x0001
_CWP_SKIPTRANSPARENT = 0x0004

user32 = ctypes.windll.user32
user32.PostMessageW.argtypes = [
    ctypes.wintypes.HWND, ctypes.wintypes.UINT,
    ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM,
]
user32.PostMessageW.restype = ctypes.wintypes.BOOL
user32.ChildWindowFromPointEx.argtypes = [
    ctypes.wintypes.HWND, ctypes.wintypes.POINT, ctypes.wintypes.UINT,
]
user32.ChildWindowFromPointEx.restype = ctypes.wintypes.HWND


def _make_lparam(x: int, y: int) -> int:
    return ((y & 0xFFFF) << 16) | (x & 0xFFFF)


def _resolve_vk(key_name: str) -> int:
    """将按键名解析为虚拟键码"""
    key = key_name.strip().upper()
    # 直接查 VK 表
    if key in VK:
        return VK[key]
    # 查别名
    alias = GAME_KEYS.get(key_name.strip().lower())
    if alias and alias in VK:
        return VK[alias]
    # 单字符字母
    if len(key) == 1 and "A" <= key <= "Z":
        return VK[key]
    raise ValueError(f"未知按键: {key_name}")


class Clicker:
    """PostMessage 后台点击/键盘器"""

    def __init__(self, hwnd: int, post_click_wait_ms: int = 500,
                 scale: Tuple[float, float] = (1.0, 1.0)):
        self.hwnd = hwnd
        self.post_click_wait_ms = post_click_wait_ms
        self.scale_x, self.scale_y = scale
        self._held_keys: Dict[str, float] = {}  # key_name -> press_time

    # ── 鼠标 ──

    def _scale(self, x: int, y: int) -> Tuple[int, int]:
        return int(x * self.scale_x), int(y * self.scale_y)

    def _resolve_child(self, x: int, y: int) -> int:
        pt = ctypes.wintypes.POINT(x, y)
        child = user32.ChildWindowFromPointEx(
            self.hwnd, pt, _CWP_SKIPINVISIBLE | _CWP_SKIPTRANSPARENT)
        return child if child else self.hwnd

    def click(self, x: int, y: int, button: str = "left"):
        """在指定坐标点击（后台 PostMessage）"""
        sx, sy = self._scale(x, y)
        target = self._resolve_child(sx, sy)
        lparam = _make_lparam(sx, sy)

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

        time.sleep(self.post_click_wait_ms / 1000.0)

    # ── 键盘 ──

    def press_key(self, key, down_time: float = 0.05):
        """按下并松开按键

        Args:
            key: 按键名 ("W", "E", "space", "shift", 4, 等) 或虚拟键码
            down_time: 按住时长（秒）
        """
        if isinstance(key, int):
            vk = key
        else:
            vk = _resolve_vk(str(key))
        user32.PostMessageW(self.hwnd, WM_KEYDOWN, vk, 0)
        if down_time > 0:
            time.sleep(down_time)
        user32.PostMessageW(self.hwnd, WM_KEYUP, vk, 0)
        time.sleep(self.post_click_wait_ms / 1000.0)

    def key_down(self, key):
        """按住按键（不松开）

        Args:
            key: 按键名 或 虚拟键码
        """
        if isinstance(key, int):
            vk = key
            key_name = str(vk)
        else:
            vk = _resolve_vk(str(key))
            key_name = str(key).lower()
        user32.PostMessageW(self.hwnd, WM_KEYDOWN, vk, 0)
        self._held_keys[key_name] = time.time()

    def key_up(self, key):
        """松开按键

        Args:
            key: 按键名 或 虚拟键码
        """
        if isinstance(key, int):
            vk = key
            key_name = str(vk)
        else:
            vk = _resolve_vk(str(key))
            key_name = str(key).lower()
        user32.PostMessageW(self.hwnd, WM_KEYUP, vk, 0)
        self._held_keys.pop(key_name, None)

    def hold_key(self, key, duration: float):
        """按住按键一段时间后松开

        Args:
            key: 按键名
            duration: 按住时长（秒）
        """
        if isinstance(key, int):
            vk = key
        else:
            vk = _resolve_vk(str(key))
        user32.PostMessageW(self.hwnd, WM_KEYDOWN, vk, 0)
        time.sleep(duration)
        user32.PostMessageW(self.hwnd, WM_KEYUP, vk, 0)

    # ── 快捷操作 ──

    def move_forward(self, duration: float):
        """向前移动（按住 W）"""
        self.hold_key("W", duration)

    def move_back(self, duration: float):
        """向后移动（按住 S）"""
        self.hold_key("S", duration)

    def move_left(self, duration: float):
        """向左移动（按住 A）"""
        self.hold_key("A", duration)

    def move_right(self, duration: float):
        """向右移动（按住 D）"""
        self.hold_key("D", duration)

    # ── 鼠标操作（游戏内攻击/瞄准，不移动坐标）──

    def _mouse_down(self, button: str):
        """发送鼠标按下消息（不移动坐标）"""
        lparam = _make_lparam(0, 0)
        if button == "left":
            user32.PostMessageW(self.hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lparam)
        elif button == "right":
            user32.PostMessageW(self.hwnd, WM_RBUTTONDOWN, 0, lparam)
        elif button == "middle":
            user32.PostMessageW(self.hwnd, WM_MBUTTONDOWN, MK_MBUTTON, lparam)

    def _mouse_up(self, button: str):
        """发送鼠标松开消息"""
        lparam = _make_lparam(0, 0)
        if button == "left":
            user32.PostMessageW(self.hwnd, WM_LBUTTONUP, 0, lparam)
        elif button == "right":
            user32.PostMessageW(self.hwnd, WM_RBUTTONUP, 0, lparam)
        elif button == "middle":
            user32.PostMessageW(self.hwnd, WM_MBUTTONUP, 0, lparam)

    def attack(self):
        """攻击（左键单击）"""
        self._mouse_down("left")
        time.sleep(0.03)
        self._mouse_up("left")
        time.sleep(self.post_click_wait_ms / 1000.0)

    def attack_heavy(self, duration: float = 0.5):
        """重击/特殊攻击（按住左键）"""
        self._mouse_down("left")
        time.sleep(duration)
        self._mouse_up("left")
        time.sleep(self.post_click_wait_ms / 1000.0)

    def ranged_attack(self):
        """远程武器攻击（右键单击）"""
        self._mouse_down("right")
        time.sleep(0.03)
        self._mouse_up("right")
        time.sleep(self.post_click_wait_ms / 1000.0)

    def ranged_attack_hold(self, duration: float):
        """远程武器按住攻击"""
        self._mouse_down("right")
        time.sleep(duration)
        self._mouse_up("right")

    def lock_target(self):
        """锁定目标（中键单击）"""
        self._mouse_down("middle")
        time.sleep(0.03)
        self._mouse_up("middle")
        time.sleep(self.post_click_wait_ms / 1000.0)

    # ── 键盘快捷操作 ──

    def use_skill(self):
        """小技能 E"""
        self.press_key("E", down_time=0.03)

    def use_ultimate(self):
        """大招 Q"""
        self.press_key("Q", down_time=0.03)

    def use_geniemon(self):
        """魔灵技能 Z"""
        self.press_key("Z", down_time=0.03)

    def helix_leap(self):
        """螺旋飞跃 4"""
        self.press_key("4", down_time=0.03)

    def dodge(self):
        """闪避 SHIFT"""
        self.press_key("SHIFT", down_time=0.05)

    def jump(self):
        """跳跃 SPACE"""
        self.press_key("SPACE", down_time=0.03)

    def reload(self):
        """换弹 R"""
        self.press_key("R", down_time=0.03)

    # ── 状态 ──

    def release_all(self):
        """松开所有按住的按键"""
        for key_name in list(self._held_keys.keys()):
            try:
                self.key_up(key_name)
            except ValueError:
                pass