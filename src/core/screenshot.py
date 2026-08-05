"""
截图模块 — DXGI Desktop Duplication 后台截图

使用 dxcam 库封装 DXGI 桌面复制 API，替代 PrintWindow。
支持 DirectX 游戏后台截图，窗口不可最小化但可被遮挡。

依赖: dxcam (pip install dxcam)
"""

import logging
from typing import Optional

import numpy as np
import win32gui
import win32con

logger = logging.getLogger("sb-two-tops.screenshot")


class Screenshot:
    """DXGI 后台截图器（基于 dxcam）"""

    def __init__(self, window_title: str, window_class: Optional[str] = None):
        self.window_title = window_title
        self.window_class = window_class
        self.hwnd: Optional[int] = None
        self._width: int = 0
        self._height: int = 0
        self._camera = None
        self._dxcam_imported = False

    def _import_dxcam(self) -> bool:
        """延迟导入 dxcam，只在首次截图时加载"""
        if self._dxcam_imported:
            return True
        try:
            import dxcam
            self._camera = dxcam.create(output_idx=0)
            self._dxcam_imported = True
            logger.info("dxcam 初始化成功")
            return True
        except ImportError:
            logger.error("dxcam 未安装，请执行: pip install dxcam")
            return False
        except Exception as e:
            logger.error(f"dxcam 初始化失败: {e}")
            return False

    def find_window(self) -> bool:
        """通过窗口标题查找游戏窗口句柄"""
        hwnd = win32gui.FindWindow(None, self.window_title)
        if not hwnd:
            # 模糊匹配：遍历所有可见窗口
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
        """重新查找窗口（用于恢复丢失的窗口句柄）"""
        logger.info("重新查找窗口...")
        self.hwnd = None
        return self.find_window()

    def _update_size(self):
        """更新窗口客户区尺寸"""
        rect = win32gui.GetClientRect(self.hwnd)
        self._width = rect[2] - rect[0]
        self._height = rect[3] - rect[1]

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def capture(self) -> Optional[np.ndarray]:
        """DXGI 截图 — 截取窗口客户区画面

        Returns:
            OpenCV BGR numpy array (H, W, 3)，失败返回 None
        """
        if self.hwnd is None:
            return None

        if not self._import_dxcam():
            return None

        if self._camera is None:
            logger.error("dxcam 未初始化")
            return None

        # 获取窗口在屏幕上的位置（客户区）
        try:
            # 检查窗口是否最小化
            if win32gui.IsIconic(self.hwnd):
                logger.warning("窗口已最小化，无法截图")
                return None

            # 获取客户区在屏幕上的位置
            pt = win32gui.ClientToScreen(self.hwnd, (0, 0))
            left, top = pt
            right = left + self._width
            bottom = top + self._height

            frame = self._camera.grab(region=(left, top, right, bottom))
            if frame is None:
                logger.debug("dxcam 截图返回空")
                return None

            # dxcam 返回 RGB (H, W, 3)，转 BGR 给 OpenCV
            if frame.shape[2] == 3:
                return frame[:, :, ::-1].copy()  # RGB → BGR
            return frame[:, :, :3].copy()

        except Exception as e:
            logger.error(f"截图失败: {e}")
            return None