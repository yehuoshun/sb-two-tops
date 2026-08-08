"""
截图模块 — PrintWindow 后台截图

使用 Win32 PrintWindow API 截取窗口客户区画面。
对部分 DirectX 游戏可能返回黑屏，但零依赖、稳定无崩溃。

API 与 dxcam 版本兼容，只需替换实现。
"""

import ctypes
import ctypes.wintypes
import logging
from typing import Optional

import numpy as np
import win32gui

logger = logging.getLogger("sb-two-tops.screenshot")

# ---------- Win32 API ----------
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

# PrintWindow 常量
PW_CLIENTONLY = 1

user32.PrintWindow.argtypes = [
    ctypes.wintypes.HWND, ctypes.wintypes.HDC, ctypes.wintypes.UINT,
]
user32.PrintWindow.restype = ctypes.wintypes.BOOL

# 位图信息头
class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", ctypes.wintypes.DWORD),
        ("biWidth", ctypes.wintypes.LONG),
        ("biHeight", ctypes.wintypes.LONG),
        ("biPlanes", ctypes.wintypes.WORD),
        ("biBitCount", ctypes.wintypes.WORD),
        ("biCompression", ctypes.wintypes.DWORD),
        ("biSizeImage", ctypes.wintypes.DWORD),
        ("biXPelsPerMeter", ctypes.wintypes.LONG),
        ("biYPelsPerMeter", ctypes.wintypes.LONG),
        ("biClrUsed", ctypes.wintypes.DWORD),
        ("biClrImportant", ctypes.wintypes.DWORD),
    ]


BI_RGB = 0
DIB_RGB_COLORS = 0
SRCCOPY = 0x00CC0020


class Screenshot:
    """PrintWindow 后台截图器"""

    def __init__(self, window_title: str, window_class: Optional[str] = None):
        self.window_title = window_title
        self.window_class = window_class
        self.hwnd: Optional[int] = None
        self._width: int = 0
        self._height: int = 0

    def find_window(self) -> bool:
        """通过窗口标题查找游戏窗口句柄"""
        self.hwnd = win32gui.FindWindow(None, self.window_title)
        if not self.hwnd:
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
        """PrintWindow 截图 — 截取窗口客户区画面

        Returns:
            OpenCV BGR numpy array (H, W, 3)，失败返回 None
        """
        if self.hwnd is None:
            return None

        try:
            # 检查窗口是否最小化
            if win32gui.IsIconic(self.hwnd):
                logger.warning("窗口已最小化，无法截图")
                return None

            w, h = self._width, self._height
            if w <= 0 or h <= 0:
                return None

            # 获取窗口 DC
            hdc_window = user32.GetDC(self.hwnd)
            if not hdc_window:
                logger.error("GetDC 失败")
                return None

            # 创建兼容 DC 和位图
            hdc_mem = gdi32.CreateCompatibleDC(hdc_window)
            hbmp = gdi32.CreateCompatibleBitmap(hdc_window, w, h)
            if not hbmp:
                user32.ReleaseDC(self.hwnd, hdc_window)
                gdi32.DeleteDC(hdc_mem)
                logger.error("CreateCompatibleBitmap 失败")
                return None

            # 选中位图到内存 DC
            gdi32.SelectObject(hdc_mem, hbmp)

            # 用 PrintWindow 将窗口内容渲染到位图
            user32.PrintWindow(self.hwnd, hdc_mem, PW_CLIENTONLY)

            # 读取位图数据
            bmp_header = BITMAPINFOHEADER()
            bmp_header.biSize = ctypes.sizeof(BITMAPINFOHEADER)
            bmp_header.biWidth = w
            bmp_header.biHeight = -h  # 负值表示自上而下
            bmp_header.biPlanes = 1
            bmp_header.biBitCount = 32
            bmp_header.biCompression = BI_RGB
            bmp_header.biSizeImage = 0

            # 分配缓冲区
            buf_size = w * h * 4
            buf = ctypes.create_string_buffer(buf_size)

            ret = gdi32.GetDIBits(
                hdc_mem, hbmp, 0, h, buf,
                ctypes.byref(bmp_header), DIB_RGB_COLORS,
            )
            if not ret:
                logger.error("GetDIBits 失败")
                # 清理
                gdi32.DeleteObject(hbmp)
                gdi32.DeleteDC(hdc_mem)
                user32.ReleaseDC(self.hwnd, hdc_window)
                return None

            # 转换为 numpy 数组 (BGRA → BGR)
            img = np.frombuffer(buf, dtype=np.uint8).reshape(h, w, 4)
            result = img[:, :, :3].copy()  # 去掉 alpha 通道

            # 清理
            gdi32.DeleteObject(hbmp)
            gdi32.DeleteDC(hdc_mem)
            user32.ReleaseDC(self.hwnd, hdc_window)

            return result

        except Exception as e:
            logger.error(f"截图失败: {e}")
            return None