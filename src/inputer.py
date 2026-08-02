"""输入模拟模块 — 键盘鼠标操作"""

import time
import re
from typing import List, Optional

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False


# 键名映射（pyautogui 格式）
KEY_MAP = {
    # 字母
    "q": "q", "w": "w", "e": "e", "r": "r", "t": "t",
    "a": "a", "s": "s", "d": "d", "f": "f", "g": "g",
    # 数字
    "1": "1", "2": "2", "3": "3", "4": "4", "5": "5",
    # 功能键
    "shift": "shift", "ctrl": "ctrl", "alt": "alt",
    "space": "space", "tab": "tab", "enter": "enter",
    # 鼠标
    "click": "click", "rclick": "rightclick",
}


class Inputer:
    """输入模拟器"""

    def __init__(self, method: str = "sendinput"):
        self.method = method
        self._use_win32 = (method == "sendinput")
        if self._use_win32:
            self._init_win32()

    def _init_win32(self):
        """初始化 win32 SendInput"""
        try:
            import win32api
            import win32con
            self.win32api = win32api
            self.win32con = win32con
            self._use_win32 = True
        except ImportError:
            print("win32api 不可用，回退到 pyautogui")
            self._use_win32 = False

    def _key_down(self, key: str):
        if self._use_win32:
            vk = self._key_to_vk(key)
            if vk:
                self.win32api.keybd_event(vk, 0, 0, 0)
        elif HAS_PYAUTOGUI:
            pyautogui.keyDown(key)

    def _key_up(self, key: str):
        if self._use_win32:
            vk = self._key_to_vk(key)
            if vk:
                self.win32api.keybd_event(vk, 0, self.win32con.KEYEVENTF_KEYUP, 0)
        elif HAS_PYAUTOGUI:
            pyautogui.keyUp(key)

    def _key_to_vk(self, key: str) -> Optional[int]:
        """字母键转虚拟键码"""
        if len(key) == 1 and 'a' <= key.lower() <= 'z':
            return ord(key.lower()) - 32  # 'A' = 65
        return None

    def press_key(self, key: str, interval: float = 0.05):
        """按下并释放一个键"""
        mapped = KEY_MAP.get(key.lower(), key)
        self._key_down(mapped)
        time.sleep(interval)
        self._key_up(mapped)

    def click(self, x: int, y: int, button: str = "left"):
        """在指定坐标点击"""
        if self._use_win32:
            import win32api
            import win32con
            win32api.SetCursorPos((x, y))
            btn_down = win32con.MOUSEEVENTF_LEFTDOWN if button == "left" else win32con.MOUSEEVENTF_RIGHTDOWN
            btn_up = win32con.MOUSEEVENTF_LEFTUP if button == "left" else win32con.MOUSEEVENTF_RIGHTUP
            win32api.mouse_event(btn_down, 0, 0, 0, 0)
            time.sleep(0.05)
            win32api.mouse_event(btn_up, 0, 0, 0, 0)
        elif HAS_PYAUTOGUI:
            pyautogui.click(x, y, button=button)

    def send_keys(self, keys: str, interval: float = 0.05):
        """依次按下多个键"""
        for key in keys:
            self.press_key(key, interval)

    def parse_and_execute(self, combo_str: str, interval: float = 0.1):
        """
        解析并执行宏指令字符串
        格式: "q" → 按Q
              "eee, qaq" → 按E三次, 停一下, 按Q-A-Q
              "q(hold:1.0)" → 按住Q 1秒后释放
        """
        # 拆分逗号分隔的指令
        parts = [p.strip() for p in combo_str.split(",")]
        for part in parts:
            if not part:
                continue

            # 检查是否有 hold 指令
            hold_match = re.match(r'^(\w)\(hold:([\d.]+)\)$', part)
            if hold_match:
                key = hold_match.group(1)
                duration = float(hold_match.group(2))
                self._key_down(key)
                time.sleep(duration)
                self._key_up(key)
                continue

            # 普通按键序列
            for ch in part:
                self.press_key(ch.lower())
                time.sleep(interval)