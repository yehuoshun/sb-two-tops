"""
DXGI 截图模块 — 使用 Desktop Duplication API 截取 DirectX 游戏画面

PrintWindow / BitBlt 对 DirectX 游戏无效，DXGI Desktop Duplication 是唯一可靠方案。
"""

import ctypes
import ctypes.wintypes
import logging
from typing import Optional

import numpy as np

logger = logging.getLogger("sb-two-tops.dxgi")

# ── GUID ──
IID_IDXGIDevice = ctypes.create_string_buffer(
    b"\x54\xec\x77\xfa\xe7\x37\x2c\x44\xa5\x61\xed\x4b\x56\x78\x53\x4b")
IID_IDXGIOutput1 = ctypes.create_string_buffer(
    b"\x77\x20\x02\x00\xe7\x9a\x03\x46\xa8\x3b\xd0\xf7\x0c\x36\x2e\x7a")
IID_ID3D11Texture2D = ctypes.create_string_buffer(
    b"\x15\xf2\x80\x6f\x9b\x8a\xe2\x47\x8b\x37\xd7\xcc\xa5\xeb\x67\xb8")

# ── DXGI 常量 ──
DXGI_ERROR_WAIT_TIMEOUT = 0x887A0027
DXGI_ERROR_ACCESS_LOST = 0x887A0026

# D3D11
D3D11_SDK_VERSION = 7
D3D_DRIVER_TYPE_HARDWARE = 1
D3D11_CREATE_DEVICE_BGRA_SUPPORT = 0x20
D3D11_MAP_READ = 1

# ── 结构体 ──
class DXGI_OUTPUT_DESC(ctypes.Structure):
    _fields_ = [
        ("DeviceName", ctypes.c_wchar * 32),
        ("DesktopCoordinates", ctypes.wintypes.RECT),
        ("AttachedToDesktop", ctypes.wintypes.BOOL),
        ("Rotation", ctypes.c_uint),
        ("Monitor", ctypes.wintypes.HANDLE),
    ]

class DXGI_OUTDUPL_FRAME_INFO(ctypes.Structure):
    _fields_ = [
        ("LastPresentTime", ctypes.c_longlong),
        ("LastMouseUpdateTime", ctypes.c_longlong),
        ("AccumulatedFrames", ctypes.c_uint),
        ("RectsCoalesced", ctypes.wintypes.BOOL),
        ("ProtectedContentMaskedOut", ctypes.wintypes.BOOL),
        ("PointerPosition", ctypes.c_int * 2),
        ("TotalMetadataBufferSize", ctypes.c_uint),
        ("PointerShapeBufferSize", ctypes.c_uint),
    ]

class D3D11_MAPPED_SUBRESOURCE(ctypes.Structure):
    _fields_ = [
        ("pData", ctypes.c_void_p),
        ("RowPitch", ctypes.c_uint),
        ("DepthPitch", ctypes.c_uint),
    ]

class D3D11_TEXTURE2D_DESC(ctypes.Structure):
    _fields_ = [
        ("Width", ctypes.c_uint), ("Height", ctypes.c_uint),
        ("MipLevels", ctypes.c_uint), ("ArraySize", ctypes.c_uint),
        ("Format", ctypes.c_uint),
        ("SampleDesc_Count", ctypes.c_uint), ("SampleDesc_Quality", ctypes.c_uint),
        ("Usage", ctypes.c_uint), ("BindFlags", ctypes.c_uint),
        ("CPUAccessFlags", ctypes.c_uint), ("MiscFlags", ctypes.c_uint),
    ]


def _com_call(ptr, index, *args):
    """调用 COM 虚函数表。所有参数统一为 c_void_p。"""
    vtbl = ctypes.cast(ptr, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p)))
    n = len(args) + 1
    proto = ctypes.WINFUNCTYPE(ctypes.c_long, *([ctypes.c_void_p] * n))
    func = proto(vtbl[0][index])

    cargs = []
    for a in args:
        if isinstance(a, ctypes.c_void_p):
            cargs.append(a)
        elif a is None:
            cargs.append(ctypes.c_void_p(0))
        elif isinstance(a, int):
            cargs.append(ctypes.c_void_p(a))
        else:
            cargs.append(ctypes.cast(a, ctypes.c_void_p))
    return func(ptr, *cargs)


def _com_query(ptr, iid_buf):
    """COM QueryInterface，返回接口指针"""
    result = ctypes.c_void_p()
    hr = _com_call(ptr, 0, ctypes.cast(iid_buf, ctypes.c_void_p), ctypes.pointer(result))
    if hr < 0:
        raise OSError(f"QueryInterface 失败: 0x{hr & 0xFFFFFFFF:08X}")
    return result


class DXGICapture:
    """DXGI Desktop Duplication 截图器"""

    def __init__(self):
        self._device = None
        self._context = None
        self._duplication = None
        self._width = 0
        self._height = 0
        self._init_dxgi()

    def _init_dxgi(self):
        d3d11 = ctypes.windll.d3d11

        feature_levels = (ctypes.c_uint * 1)(0x9300)
        device_ptr = ctypes.c_void_p()
        context_ptr = ctypes.c_void_p()
        fl_ptr = ctypes.c_uint()

        hr = d3d11.D3D11CreateDevice(
            None, D3D_DRIVER_TYPE_HARDWARE, None, D3D11_CREATE_DEVICE_BGRA_SUPPORT,
            feature_levels, 1, D3D11_SDK_VERSION,
            ctypes.byref(device_ptr), ctypes.byref(fl_ptr), ctypes.byref(context_ptr),
        )
        if hr < 0:
            raise OSError(f"D3D11CreateDevice 失败: 0x{hr & 0xFFFFFFFF:08X}")

        self._device = device_ptr
        self._context = context_ptr

        # device → IDXGIDevice → GetAdapter → EnumOutputs → IDXGIOutput1
        dxgi_device = _com_query(device_ptr, IID_IDXGIDevice)

        adapter = ctypes.c_void_p()
        _com_call(dxgi_device, 7, ctypes.pointer(adapter))

        output = ctypes.c_void_p()
        _com_call(adapter, 7, ctypes.c_void_p(0), ctypes.pointer(output))

        output1 = _com_query(output, IID_IDXGIOutput1)

        desc = DXGI_OUTPUT_DESC()
        _com_call(output1, 10, ctypes.pointer(desc))
        self._width = desc.DesktopCoordinates.right - desc.DesktopCoordinates.left
        self._height = desc.DesktopCoordinates.bottom - desc.DesktopCoordinates.top

        duplication = ctypes.c_void_p()
        hr = _com_call(output1, 22, device_ptr, ctypes.pointer(duplication))
        if hr < 0:
            raise OSError(f"DuplicateOutput 失败: 0x{hr & 0xFFFFFFFF:08X}")
        self._duplication = duplication

        logger.info(f"DXGI 初始化完成 ({self._width}x{self._height})")

    def capture(self, timeout_ms: int = 100) -> Optional[np.ndarray]:
        if self._duplication is None:
            return None

        frame_info = DXGI_OUTDUPL_FRAME_INFO()
        resource = ctypes.c_void_p()

        hr = _com_call(self._duplication, 8, ctypes.c_void_p(timeout_ms),
                       ctypes.pointer(frame_info), ctypes.pointer(resource))

        if hr == DXGI_ERROR_WAIT_TIMEOUT:
            return None
        if hr == DXGI_ERROR_ACCESS_LOST:
            logger.error("DXGI access lost")
            self._duplication = None
            return None
        if hr < 0:
            return None

        try:
            texture = _com_query(resource, IID_ID3D11Texture2D)

            tex_desc = D3D11_TEXTURE2D_DESC()
            _com_call(texture, 10, ctypes.pointer(tex_desc))

            staging_desc = D3D11_TEXTURE2D_DESC()
            staging_desc.Width = tex_desc.Width
            staging_desc.Height = tex_desc.Height
            staging_desc.MipLevels = 1
            staging_desc.ArraySize = 1
            staging_desc.Format = tex_desc.Format
            staging_desc.SampleDesc_Count = 1
            staging_desc.Usage = 3
            staging_desc.CPUAccessFlags = D3D11_MAP_READ

            staging = ctypes.c_void_p()
            hr = _com_call(self._device, 5, ctypes.pointer(staging_desc),
                           ctypes.c_void_p(0), ctypes.pointer(staging))
            if hr < 0:
                return None

            _com_call(self._context, 47, staging, texture, ctypes.c_void_p(0))

            mapped = D3D11_MAPPED_SUBRESOURCE()
            _com_call(self._context, 14, staging, ctypes.c_void_p(0),
                      ctypes.c_void_p(D3D11_MAP_READ), ctypes.c_void_p(0),
                      ctypes.pointer(mapped))

            width = tex_desc.Width
            height = tex_desc.Height
            pitch = mapped.RowPitch

            if pitch == width * 4:
                buf = ctypes.cast(mapped.pData,
                                  ctypes.POINTER(ctypes.c_ubyte * (width * height * 4)))
                arr = np.frombuffer(buf.contents, dtype=np.uint8).reshape(height, width, 4)
                result = arr[:, :, :3].copy()
            else:
                raw = (ctypes.c_ubyte * (pitch * height)).from_address(mapped.pData)
                arr = np.frombuffer(raw, dtype=np.uint8).reshape(height, pitch)
                arr = arr[:, :width * 4].reshape(height, width, 4)
                result = arr[:, :, :3].copy()

            _com_call(self._context, 15, staging, ctypes.c_void_p(0))
            return result

        finally:
            _com_call(self._duplication, 9)

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height