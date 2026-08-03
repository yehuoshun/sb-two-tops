"""
截图模块 - PrintWindow 后台截图
"""

import ctypes
import ctypes.wintypes
import logging
from typing import Optional

import numpy as np

logger = logging.getLogger("sb-two-tops.screenshot")

PW_RENDERFULLCONTENT = 0x00000002
BI_RGB = 0
DIB_RGB_COLORS = 0


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


class BITMAPINFO(ctypes.Structure):
    _fields_ = [
        ("bmiHeader", BITMAPINFOHEADER),
        ("bmiColors", ctypes.wintypes.DWORD * 0),
    ]


user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

user32.GetWindowDC.restype = ctypes.wintypes.HDC
user32.GetWindowDC.argtypes = [ctypes.wintypes.HWND]
user32.ReleaseDC.argtypes = [ctypes.wintypes.HWND, ctypes.wintypes.HDC]
user32.PrintWindow.argtypes = [ctypes.wintypes.HWND, ctypes.wintypes.HDC, ctypes.wintypes.UINT]
user32.PrintWindow.restype = ctypes.wintypes.BOOL
user32.GetWindowRect.argtypes = [ctypes.wintypes.HWND, ctypes.POINTER(ctypes.wintypes.RECT)]
user32.GetWindowRect.restype = ctypes.wintypes.BOOL
user32.GetClientRect.argtypes = [ctypes.wintypes.HWND, ctypes.POINTER(ctypes.wintypes.RECT)]
user32.GetClientRect.restype = ctypes.wintypes.BOOL
user32.ClientToScreen.argtypes = [ctypes.wintypes.HWND, ctypes.POINTER(ctypes.wintypes.POINT)]
user32.ClientToScreen.restype = ctypes.wintypes.BOOL
user32.EnumWindows.restype = ctypes.wintypes.BOOL
user32.EnumWindows.argtypes = [
    ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND,
                       ctypes.wintypes.LPARAM),
    ctypes.wintypes.LPARAM,
]
user32.GetWindowTextW.argtypes = [ctypes.wintypes.HWND, ctypes.wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowTextLengthW.argtypes = [ctypes.wintypes.HWND]
user32.IsWindowVisible.argtypes = [ctypes.wintypes.HWND]

gdi32.CreateCompatibleDC.restype = ctypes.wintypes.HDC
gdi32.CreateCompatibleDC.argtypes = [ctypes.wintypes.HDC]
gdi32.CreateCompatibleBitmap.restype = ctypes.wintypes.HBITMAP
gdi32.CreateCompatibleBitmap.argtypes = [ctypes.wintypes.HDC, ctypes.c_int, ctypes.c_int]
gdi32.GetDIBits.argtypes = [
    ctypes.wintypes.HDC, ctypes.wintypes.HBITMAP,
    ctypes.wintypes.UINT, ctypes.wintypes.UINT,
    ctypes.c_void_p, ctypes.c_void_p, ctypes.wintypes.UINT,
]
gdi32.SelectObject.argtypes = [ctypes.wintypes.HDC, ctypes.wintypes.HGDIOBJ]
gdi32.DeleteObject.argtypes = [ctypes.wintypes.HGDIOBJ]
gdi32.DeleteDC.argtypes = [ctypes.wintypes.HDC]
gdi32.GetDIBits.argtypes = [
    ctypes.wintypes.HDC, ctypes.wintypes.HBITMAP,
    ctypes.wintypes.UINT, ctypes.wintypes.UINT,
    ctypes.c_void_p, ctypes.c_void_p,
    ctypes.wintypes.UINT,
]
gdi32.GetDIBits.restype = ctypes.c_int


class Screenshot:
    """PrintWindow 后台截图器"""

    def __init__(self, window_title: str, window_class: Optional[str] = None):
        self.window_title = window_title
        self.window_class = window_class
        self.hwnd: Optional[int] = None
        self._width: int = 0
        self._height: int = 0

    def _enum_windows_callback(self, hwnd, lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd) + 1
        buf = ctypes.create_unicode_buffer(length)
        user32.GetWindowTextW(hwnd, buf, length)
        if buf.value and self.window_title.lower() in buf.value.lower():
            self._hwnds.append(hwnd)
        return True

    def find_window(self) -> bool:
        callback_type = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
        callback = callback_type(self._enum_windows_callback)
        self._hwnds = []
        user32.EnumWindows(callback, 0)
        if self._hwnds:
            self.hwnd = self._hwnds[0]
            self._update_size()
            logger.info(f"找到窗口 (hwnd={self.hwnd})")
            return True
        logger.warning(f"未找到窗口: {self.window_title}")
        return False

    def _update_size(self):
        rect = ctypes.wintypes.RECT()
        user32.GetClientRect(self.hwnd, ctypes.byref(rect))
        self._width = rect.right - rect.left
        self._height = rect.bottom - rect.top

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def capture(self):
        """PrintWindow 截图，返回 OpenCV BGR numpy array"""
        if self.hwnd is None:
            return None

        hdc_window = user32.GetWindowDC(self.hwnd)
        hdc_mem = gdi32.CreateCompatibleDC(hdc_window)
        hbitmap = gdi32.CreateCompatibleBitmap(hdc_window, self._width, self._height)
        gdi32.SelectObject(hdc_mem, hbitmap)

        success = user32.PrintWindow(self.hwnd, hdc_mem, PW_RENDERFULLCONTENT)
        if not success:
            success = user32.PrintWindow(self.hwnd, hdc_mem, 0)

        if not success:
            gdi32.DeleteObject(hbitmap)
            gdi32.DeleteDC(hdc_mem)
            user32.ReleaseDC(self.hwnd, hdc_window)
            return None

        bmp_info = BITMAPINFO()
        bmp_info.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmp_info.bmiHeader.biWidth = self._width
        bmp_info.bmiHeader.biHeight = -self._height
        bmp_info.bmiHeader.biPlanes = 1
        bmp_info.bmiHeader.biBitCount = 32
        bmp_info.bmiHeader.biCompression = BI_RGB

        pixel_data = (ctypes.c_ubyte * (self._width * self._height * 4))()
        gdi32.GetDIBits(hdc_mem, hbitmap, 0, self._height, pixel_data, ctypes.byref(bmp_info), DIB_RGB_COLORS)

        gdi32.DeleteObject(hbitmap)
        gdi32.DeleteDC(hdc_mem)
        user32.ReleaseDC(self.hwnd, hdc_window)

        # BGRA raw → BGR numpy (OpenCV 原生格式)
        arr = np.frombuffer(pixel_data, dtype=np.uint8).reshape(self._height, self._width, 4)
        return arr[:, :, :3].copy()