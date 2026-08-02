"""截图模块 — 基于 mss 捕获游戏窗口"""

import mss
import mss.tools
import numpy as np
import win32gui
import win32con
from pathlib import Path
from typing import Optional, Tuple


def find_window(title_keyword: str) -> Optional[int]:
    """按标题关键字查找游戏窗口句柄"""
    def callback(hwnd, ctx):
        if win32gui.IsWindowVisible(hwnd):
            text = win32gui.GetWindowText(hwnd)
            if title_keyword.lower() in text.lower():
                ctx.append(hwnd)
        return True

    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    return hwnds[0] if hwnds else None


def get_window_rect(hwnd: int) -> Optional[Tuple[int, int, int, int]]:
    """获取窗口客户区坐标 (left, top, right, bottom)"""
    try:
        rect = win32gui.GetClientRect(hwnd)
        left, top = win32gui.ClientToScreen(hwnd, (0, 0))
        right = left + rect[2]
        bottom = top + rect[3]
        return (left, top, right, bottom)
    except:
        return None


class Capturer:
    """窗口截图器"""

    def __init__(self, window_title: str = "二重螺旋"):
        self.window_title = window_title
        self.hwnd: Optional[int] = None
        self.sct = mss.mss()

    def find_game_window(self) -> bool:
        """查找游戏窗口"""
        self.hwnd = find_window(self.window_title)
        return self.hwnd is not None

    def capture(self) -> Optional[np.ndarray]:
        """截取游戏窗口区域，返回 BGRA numpy array"""
        if self.hwnd is None:
            if not self.find_game_window():
                return None

        rect = get_window_rect(self.hwnd)
        if rect is None:
            return None

        left, top, right, bottom = rect
        monitor = {"left": left, "top": top, "width": right - left, "height": bottom - top}
        img = self.sct.grab(monitor)
        return np.array(img)

    def capture_region(self, bbox: Tuple[int, int, int, int]) -> Optional[np.ndarray]:
        """
        截取窗口内指定区域
        bbox: (x, y, w, h) 相对窗口左上角
        """
        full = self.capture()
        if full is None:
            return None
        x, y, w, h = bbox
        return full[y:y+h, x:x+w]

    def save(self, img: np.ndarray, path: str = "debug.png"):
        """保存截图到文件"""
        mss.tools.to_png(img.rgb, img.shape[1], img.shape[0], output=path)
        print(f"截图已保存: {path}")

    def close(self):
        self.sct.close()