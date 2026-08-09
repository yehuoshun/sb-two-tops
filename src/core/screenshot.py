"""
截图模块 — MSS 后台截图

基于 mss 库，支持 DXGI 桌面复制，兼容 DirectX 游戏。
相比 dxcam 更稳定，相比 PrintWindow 能截到 DirectX 画面。

依赖: pip install mss
"""

import ctypes
import logging
from typing import Optional

import numpy as np
import win32gui

logger = logging.getLogger("sb-two-tops.screenshot")

user32: ctypes.WinDLL = ctypes.windll.user32


class Screenshot:
    """MSS 后台截图器"""

    def __init__(self, window_title: str, window_class: Optional[str] = None):
        self.window_title = window_title
        self.window_class = window_class
        self.hwnd: Optional[int] = None
        self._width: int = 0
        self._height: int = 0
        self._sct = None

    def _init_mss(self) -> bool:
        """延迟初始化 mss"""
        if self._sct is not None:
            return True
        try:
            import mss
            self._sct = mss.MSS()
            logger.info("MSS 初始化成功")
            return True
        except ImportError:
            logger.error("mss 未安装，请执行: pip install mss")
            return False
        except Exception as e:
            logger.error(f"MSS 初始化失败: {e}")
            return False

    def find_window(self) -> bool:
        """通过窗口标题查找游戏窗口句柄"""
        self.hwnd = win32gui.FindWindow(None, self.window_title)
        if not self.hwnd:
            def enum_cb(h, _):
                if win32gui.IsWindowVisible(h):
                    t = win32gui.GetWindowText(h)
                    if self.window_title.lower() in t.lower():
                        self.hwnd = h
                        return False
                return True
            win32gui.EnumWindows(enum_cb, 0)

        if self.hwnd:
            self._update_size()
            title = win32gui.GetWindowText(self.hwnd)
            logger.info(f"找到窗口: \"{title}\" (hwnd={self.hwnd}) {self._width}x{self._height}")
            return True

        logger.warning(f"未找到窗口: {self.window_title}")
        return False

    def reload_window(self) -> bool:
        logger.info("重新查找窗口...")
        self.hwnd = None
        return self.find_window()

    def _update_size(self):
        hwnd = self.hwnd
        assert hwnd is not None, "_update_size called before find_window"
        rect = win32gui.GetClientRect(hwnd)
        self._width = rect[2] - rect[0]
        self._height = rect[3] - rect[1]

    def bring_to_foreground(self) -> bool:
        """将游戏窗口提到前台（多级尝试）

        策略:
            1. SetForegroundWindow (标准 API，但 ACE 可能拦截)
            2. SwitchToThisWindow (降级 API，ACE 管不到)
            3. 附加到窗口输入线程后 SetForegroundWindow

        Returns:
            bool: 是否成功
        """
        if self.hwnd is None:
            return False

        # 1. SetForegroundWindow
        try:
            if win32gui.SetForegroundWindow(self.hwnd):
                return True
        except Exception:
            pass

        logger.debug("SetForegroundWindow 失败，尝试 SwitchToThisWindow")

        # 2. SwitchToThisWindow (ACE 不管这个)
        try:
            user32.SwitchToThisWindow(self.hwnd, True)
            import time
            time.sleep(0.05)
            return True
        except Exception:
            pass

        # 3. AttachThreadInput
        try:
            game_tid = win32gui.GetWindowThreadProcessId(self.hwnd)[0]
            cur_tid = win32gui.GetWindowThreadProcessId(0)[0]
            if game_tid != cur_tid:
                user32.AttachThreadInput(cur_tid, game_tid, True)
                win32gui.SetForegroundWindow(self.hwnd)
                user32.AttachThreadInput(cur_tid, game_tid, False)
                return True
        except Exception:
            pass

        logger.warning("窗口置前失败（ACE 拦截）")
        return False

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def capture(self) -> Optional[np.ndarray]:
        """MSS 截图 — 截取窗口客户区画面

        Returns:
            OpenCV BGR numpy array (H, W, 3)，失败返回 None
        """
        if self.hwnd is None:
            logger.warning("截图失败: hwnd 为空")
            return None

        if not self._init_mss():
            return None

        try:
            if win32gui.IsIconic(self.hwnd):
                logger.warning("窗口已最小化，无法截图")
                return None

            # 将游戏窗口提到前台，确保 MSS 截到的是游戏画面
            self.bring_to_foreground()

            # 获取客户区在屏幕上的位置
            pt = win32gui.ClientToScreen(self.hwnd, (0, 0))
            left, top = pt
            right = left + self._width
            bottom = top + self._height

            monitor = {
                "left": left,
                "top": top,
                "width": self._width,
                "height": self._height,
            }
            sct_img = self._sct.grab(monitor)

            # MSS 返回 BGRA，转 BGR
            img = np.array(sct_img)
            bgr = img[:, :, :3].copy()

            logger.debug(
                f"截图: {self._width}x{self._height} "
                f"mean={bgr.mean():.0f} "
                f"region=({left},{top},{right},{bottom})"
            )
            return bgr

        except Exception as e:
            logger.error(f"截图失败: {e}")
            return None