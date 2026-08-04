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
IID_IDXGIOutput = ctypes.create_string_buffer(
    b"\xe0\x2d\xed\xae\xd1\x90\xf0\x4a\xb1\x08\x48\x80\x60\x9e\x2c\xaa")
IID_IDXGIOutput1 = ctypes.create_string_buffer(
    b"\x77\x20\x02\x00\xe7\x9a\x03\x46\xa8\x3b\xd0\xf7\x0c\x36\x2e\x7a")
IID_IDXGIOutputDuplication = ctypes.create_string_buffer(
    b"\x9e\x6b\xc1\x19\x6f\x26\xa2\x47\xa1\x63\xe7\xe8\x3a\x9e\x51\x10")
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
D3D11_MAP_WRITE_DISCARD = 4
DXGI_FORMAT_B8G8R8A8_UNORM = 87

# ── 结构体 ──
class DXGI_RATIONAL(ctypes.Structure):
    _fields_ = [("Numerator", ctypes.c_uint), ("Denominator", ctypes.c_uint)]

class DXGI_MODE_DESC(ctypes.Structure):
    _fields_ = [
        ("Width", ctypes.c_uint), ("Height", ctypes.c_uint),
        ("RefreshRate", DXGI_RATIONAL), ("Format", ctypes.c_uint),
        ("ScanlineOrdering", ctypes.c_uint), ("Scaling", ctypes.c_uint),
    ]

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
        ("PointerPosition", ctypes.c_int * 2),  # POINT
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


class DXGICapture:
    """DXGI Desktop Duplication 截图器"""

    def __init__(self):
        self._device = None
        self._context = None
        self._duplication = None
        self._output_desc = None
        self._width = 0
        self._height = 0
        self._init_dxgi()

    def _init_dxgi(self):
        """初始化 DXGI Desktop Duplication"""
        d3d11 = ctypes.windll.d3d11
        dxgi = ctypes.windll.dxgi

        # D3D11CreateDevice
        feature_levels = (ctypes.c_uint * 1)(0x9300)  # D3D_FEATURE_LEVEL_11_0
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

        # device → IDXGIDevice
        dxgi_device = self._query_interface(device_ptr, IID_IDXGIDevice)
        # IDXGIDevice.GetAdapter
        adapter = ctypes.c_void_p()
        self._call_vtbl(dxgi_device, 7, ctypes.byref(adapter))  # GetAdapter

        # IDXGIAdapter.EnumOutputs
        output = ctypes.c_void_p()
        self._call_vtbl(adapter, 7, 0, ctypes.byref(output))  # EnumOutputs

        # IDXGIOutput → IDXGIOutput1
        output1 = self._query_interface(output, IID_IDXGIOutput1)

        # IDXGIOutput1.GetDesc
        desc = DXGI_OUTPUT_DESC()
        self._call_vtbl(output1, 10, ctypes.byref(desc))  # GetDesc (IDXGIOutput1)
        self._output_desc = desc
        self._width = desc.DesktopCoordinates.right - desc.DesktopCoordinates.left
        self._height = desc.DesktopCoordinates.bottom - desc.DesktopCoordinates.top

        # IDXGIOutput1.DuplicateOutput
        duplication = ctypes.c_void_p()
        hr = self._call_vtbl(output1, 22, device_ptr, ctypes.byref(duplication))
        if hr < 0:
            raise OSError(f"DuplicateOutput 失败: 0x{hr & 0xFFFFFFFF:08X}")
        self._duplication = duplication

        logger.info(f"DXGI 初始化完成 ({self._width}x{self._height})")

    @staticmethod
    def _query_interface(ptr, iid):
        """COM QueryInterface"""
        result = ctypes.c_void_p()
        hr = DXGICapture._call_vtbl(ptr, 0, iid, ctypes.byref(result))
        if hr < 0:
            raise OSError(f"QueryInterface 失败: 0x{hr & 0xFFFFFFFF:08X}")
        return result

    @staticmethod
    def _call_vtbl(ptr, index, *args):
        """调用 COM 虚函数表"""
        vtbl = ctypes.cast(ptr, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p)))
        func = ctypes.cast(vtbl[0][index], ctypes.CFUNCTYPE(ctypes.c_long, ctypes.c_void_p, *[type(a) for a in args]))
        return func(ptr, *args)

    def capture(self, timeout_ms: int = 100) -> Optional[np.ndarray]:
        """截取一帧，返回 BGR numpy array"""
        if self._duplication is None:
            return None

        frame_info = DXGI_OUTDUPL_FRAME_INFO()
        resource = ctypes.c_void_p()

        hr = self._call_vtbl(
            self._duplication, 8,  # AcquireNextFrame
            timeout_ms, ctypes.byref(frame_info), ctypes.byref(resource),
        )

        if hr == DXGI_ERROR_WAIT_TIMEOUT:
            return None
        if hr == DXGI_ERROR_ACCESS_LOST:
            logger.error("DXGI access lost, 需要重新初始化")
            self._duplication = None
            return None
        if hr < 0:
            return None

        try:
            # resource → ID3D11Texture2D
            texture = self._query_interface(resource, IID_ID3D11Texture2D)

            # 获取纹理描述
            tex_desc = D3D11_TEXTURE2D_DESC()
            self._call_vtbl(texture, 10, ctypes.byref(tex_desc))  # GetDesc

            # 创建 staging texture
            staging_desc = D3D11_TEXTURE2D_DESC()
            staging_desc.Width = tex_desc.Width
            staging_desc.Height = tex_desc.Height
            staging_desc.MipLevels = 1
            staging_desc.ArraySize = 1
            staging_desc.Format = tex_desc.Format
            staging_desc.SampleDesc_Count = 1
            staging_desc.Usage = 3  # D3D11_USAGE_STAGING
            staging_desc.CPUAccessFlags = D3D11_MAP_READ

            staging = ctypes.c_void_p()
            hr = self._call_vtbl(self._device, 5, ctypes.byref(staging_desc),
                                 None, ctypes.byref(staging))  # CreateTexture2D
            if hr < 0:
                return None

            # 复制到 staging
            self._call_vtbl(self._context, 47, staging, texture, 0)  # CopySubresourceRegion

            # Map
            mapped = D3D11_MAPPED_SUBRESOURCE()
            self._call_vtbl(self._context, 14, staging, 0, D3D11_MAP_READ, 0,
                            ctypes.byref(mapped))  # Map

            width = tex_desc.Width
            height = tex_desc.Height
            pitch = mapped.RowPitch

            # 读取像素 (BGRA → BGR)
            if pitch == width * 4:
                buf = ctypes.cast(mapped.pData, ctypes.POINTER(ctypes.c_ubyte * (width * height * 4)))
                arr = np.frombuffer(buf.contents, dtype=np.uint8).reshape(height, width, 4)
                result = arr[:, :, :3].copy()
            else:
                # RowPitch 可能大于 width*4（对齐）
                raw = (ctypes.c_ubyte * (pitch * height)).from_address(mapped.pData)
                arr = np.frombuffer(raw, dtype=np.uint8).reshape(height, pitch)
                arr = arr[:, :width * 4].reshape(height, width, 4)
                result = arr[:, :, :3].copy()

            # Unmap
            self._call_vtbl(self._context, 15, staging, 0)  # Unmap

            return result

        finally:
            # ReleaseFrame
            self._call_vtbl(self._duplication, 9)  # ReleaseFrame

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height