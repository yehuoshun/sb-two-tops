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

# ── GUID 结构体 ──
class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", ctypes.c_uint),
        ("Data2", ctypes.c_ushort),
        ("Data3", ctypes.c_ushort),
        ("Data4", ctypes.c_ubyte * 8),
    ]

IID_IDXGIFactory1 = GUID(0x770aae78, 0xf26f, 0x4dba,
                         (0xa8, 0x29, 0x25, 0x3c, 0x83, 0xd1, 0xb3, 0x87))
IID_IDXGIOutput1 = GUID(0x00cddea8, 0x939b, 0x4b83,
                        (0xa3, 0x40, 0xa6, 0x85, 0x22, 0xe4, 0x4c, 0x4f))
IID_ID3D11Texture2D = GUID(0x6f15aaf2, 0xd208, 0x4e89,
                           (0x9a, 0xb4, 0x48, 0x95, 0x35, 0xd3, 0x4f, 0x9c))

# ── 常量 ──
DXGI_ERROR_WAIT_TIMEOUT = 0x887A0027
DXGI_ERROR_ACCESS_LOST = 0x887A0026
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

# ── COM 函数原型 ──
# IUnknown
QI_PROTO = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p,
                               ctypes.POINTER(GUID), ctypes.POINTER(ctypes.c_void_p))

# IDXGIFactory1::EnumAdapters1
EA1_PROTO = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p,
                                ctypes.c_uint, ctypes.POINTER(ctypes.c_void_p))

# IDXGIAdapter1::EnumOutputs
EO_PROTO = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p,
                               ctypes.c_uint, ctypes.POINTER(ctypes.c_void_p))

# IDXGIOutput::GetDesc
GD_PROTO = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p,
                               ctypes.POINTER(DXGI_OUTPUT_DESC))

# IDXGIOutput1::DuplicateOutput
DO_PROTO = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p,
                               ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p))

# IDXGIOutputDuplication::AcquireNextFrame
ANF_PROTO = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p,
                                ctypes.c_uint, ctypes.POINTER(DXGI_OUTDUPL_FRAME_INFO),
                                ctypes.POINTER(ctypes.c_void_p))

# IDXGIOutputDuplication::ReleaseFrame
RF_PROTO = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p)

# ID3D11Texture2D::GetDesc
TD_PROTO = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p,
                               ctypes.POINTER(D3D11_TEXTURE2D_DESC))

# ID3D11Device::CreateTexture2D
CT2D_PROTO = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p,
                                 ctypes.POINTER(D3D11_TEXTURE2D_DESC),
                                 ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p))

# ID3D11DeviceContext::CopySubresourceRegion
CSR_PROTO = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p,
                                ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p,
                                ctypes.c_uint, ctypes.c_uint, ctypes.c_uint,
                                ctypes.c_uint)

# ID3D11DeviceContext::Map
MAP_PROTO = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p,
                                ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint,
                                ctypes.c_uint, ctypes.POINTER(D3D11_MAPPED_SUBRESOURCE))

# ID3D11DeviceContext::Unmap
UNMAP_PROTO = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p,
                                  ctypes.c_void_p, ctypes.c_uint)


def _vtbl_call(ptr, index, proto):
    """获取 COM vtable 函数指针并包装为 proto 类型"""
    vtbl = ctypes.cast(ptr, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p)))
    return proto(vtbl[0][index])


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
        dxgi = ctypes.windll.dxgi

        # 1. D3D11CreateDevice
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

        # 2. CreateDXGIFactory1
        factory = ctypes.c_void_p()
        hr = dxgi.CreateDXGIFactory1(ctypes.byref(IID_IDXGIFactory1), ctypes.byref(factory))
        if hr < 0:
            raise OSError(f"CreateDXGIFactory1 失败: 0x{hr & 0xFFFFFFFF:08X}")

        # 3. EnumAdapters1(0)
        adapter = ctypes.c_void_p()
        ea1 = _vtbl_call(factory, 12, EA1_PROTO)
        hr = ea1(factory, 0, ctypes.byref(adapter))
        if hr < 0:
            raise OSError(f"EnumAdapters1 失败: 0x{hr & 0xFFFFFFFF:08X}")

        # 4. EnumOutputs(0)
        output = ctypes.c_void_p()
        eo = _vtbl_call(adapter, 7, EO_PROTO)
        hr = eo(adapter, 0, ctypes.byref(output))
        if hr < 0:
            raise OSError(f"EnumOutputs 失败: 0x{hr & 0xFFFFFFFF:08X}")

        # 5. output → IDXGIOutput1
        output1 = ctypes.c_void_p()
        qi = _vtbl_call(output, 0, QI_PROTO)
        hr = qi(output, ctypes.byref(IID_IDXGIOutput1), ctypes.byref(output1))
        if hr < 0:
            raise OSError(f"QueryInterface(IDXGIOutput1) 失败: 0x{hr & 0xFFFFFFFF:08X}")

        # 6. GetDesc
        desc = DXGI_OUTPUT_DESC()
        gd = _vtbl_call(output1, 7, GD_PROTO)
        gd(output1, ctypes.byref(desc))
        self._width = desc.DesktopCoordinates.right - desc.DesktopCoordinates.left
        self._height = desc.DesktopCoordinates.bottom - desc.DesktopCoordinates.top

        # 7. DuplicateOutput
        duplication = ctypes.c_void_p()
        do = _vtbl_call(output1, 22, DO_PROTO)
        hr = do(output1, device_ptr, ctypes.byref(duplication))
        if hr < 0:
            raise OSError(f"DuplicateOutput 失败: 0x{hr & 0xFFFFFFFF:08X}")
        self._duplication = duplication

        logger.info(f"DXGI 初始化完成 ({self._width}x{self._height})")

    def capture(self, timeout_ms: int = 100) -> Optional[np.ndarray]:
        if self._duplication is None:
            return None

        frame_info = DXGI_OUTDUPL_FRAME_INFO()
        resource = ctypes.c_void_p()

        anf = _vtbl_call(self._duplication, 4, ANF_PROTO)
        hr = anf(self._duplication, timeout_ms, ctypes.byref(frame_info), ctypes.byref(resource))

        if hr == DXGI_ERROR_WAIT_TIMEOUT:
            return None
        if hr == DXGI_ERROR_ACCESS_LOST:
            logger.error("DXGI access lost")
            self._duplication = None
            return None
        if hr < 0:
            return None

        try:
            # resource → ID3D11Texture2D
            texture = ctypes.c_void_p()
            qi = _vtbl_call(resource, 0, QI_PROTO)
            qi(resource, ctypes.byref(IID_ID3D11Texture2D), ctypes.byref(texture))

            # GetDesc
            tex_desc = D3D11_TEXTURE2D_DESC()
            td = _vtbl_call(texture, 10, TD_PROTO)
            td(texture, ctypes.byref(tex_desc))

            # Create staging texture
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
            ct2d = _vtbl_call(self._device, 5, CT2D_PROTO)
            hr = ct2d(self._device, ctypes.byref(staging_desc), None, ctypes.byref(staging))
            if hr < 0:
                return None

            # CopySubresourceRegion
            csr = _vtbl_call(self._context, 47, CSR_PROTO)
            csr(self._context, staging, 0, 0, 0, 0, texture, 0, None)

            # Map
            mapped = D3D11_MAPPED_SUBRESOURCE()
            m = _vtbl_call(self._context, 14, MAP_PROTO)
            m(self._context, staging, 0, D3D11_MAP_READ, 0, ctypes.byref(mapped))

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

            # Unmap
            um = _vtbl_call(self._context, 15, UNMAP_PROTO)
            um(self._context, staging, 0)

            return result

        finally:
            rf = _vtbl_call(self._duplication, 10, RF_PROTO)
            rf(self._duplication)

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height