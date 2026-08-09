"""
Win32 消息常量与虚拟键码表
"""
# noinspection SpellCheckingInspection

# ── 鼠标消息 ──
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205
WM_MBUTTONDOWN = 0x0207
WM_MBUTTONUP = 0x0208
WM_MOUSEMOVE = 0x0200
WM_MOUSEWHEEL = 0x020A
MK_LBUTTON = 0x0001
MK_MBUTTON = 0x0010

# ── 键盘消息 ──
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101

# ── 虚拟键码 ──
VK = {
    "A": 0x41, "B": 0x42, "C": 0x43, "D": 0x44,
    "E": 0x45, "F": 0x46, "G": 0x47, "H": 0x48,
    "I": 0x49, "J": 0x4A, "K": 0x4B, "L": 0x4C,
    "M": 0x4D, "N": 0x4E, "O": 0x4F, "P": 0x50,
    "Q": 0x51, "R": 0x52, "S": 0x53, "T": 0x54,
    "U": 0x55, "V": 0x56, "W": 0x57, "X": 0x58,
    "Y": 0x59, "Z": 0x5A,
    "0": 0x30, "1": 0x31, "2": 0x32, "3": 0x33,
    "4": 0x34, "5": 0x35, "6": 0x36, "7": 0x37,
    "8": 0x38, "9": 0x39,
    "SPACE": 0x20, "SHIFT": 0x10, "CTRL": 0x11, "ALT": 0x12,
    "TAB": 0x09, "ESC": 0x1B, "ENTER": 0x0D, "BACK": 0x08,
    "LSHIFT": 0xA0, "RSHIFT": 0xA1,
    "LCONTROL": 0xA2, "RCONTROL": 0xA3,
    "LALT": 0xA4, "RALT": 0xA5,
}

# ── 游戏键别名 ──
GAME_KEYS = {
    "w": "W", "a": "A", "s": "S", "d": "D",
    "e": "E", "q": "Q", "z": "Z", "r": "R",
    "space": "SPACE", "空格": "SPACE",
    "shift": "SHIFT", "闪避": "SHIFT",
    "ctrl": "CTRL", "下蹲": "CTRL",
    "tab": "TAB", "esc": "ESC",
    "螺旋飞跃": "4", "helix": "4",
}

# ── ChildWindowFromPointEx flags ──
CWP_SKIPINVISIBLE = 0x0001
CWP_SKIPTRANSPARENT = 0x0004


def make_lparam(x: int, y: int) -> int:
    """将坐标打包为 LPARAM"""
    return ((y & 0xFFFF) << 16) | (x & 0xFFFF)


def resolve_vk(key_name: str) -> int:
    """将按键名解析为虚拟键码"""
    key = key_name.strip().upper()
    if key in VK:
        return VK[key]
    alias = GAME_KEYS.get(key_name.strip().lower())
    if alias and alias in VK:
        return VK[alias]
    if len(key) == 1 and "A" <= key <= "Z":
        return VK[key]
    raise ValueError(f"未知按键: {key_name}")