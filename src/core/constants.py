"""
Win32 消息常量与虚拟键码表

所有标识符使用驼峰命名，避免 PyCharm 拼写检查警告。
"""

# 鼠标消息
wmLeftButtonDown = 0x0201
wmLeftButtonUp = 0x0202
wmRightButtonDown = 0x0204
wmRightButtonUp = 0x0205
wmMiddleButtonDown = 0x0207
wmMiddleButtonUp = 0x0208
wmMouseMove = 0x0200
wmMouseWheel = 0x020A
mkLeftButton = 0x0001
mkMiddleButton = 0x0010

# 键盘消息
wmKeyDown = 0x0100
wmKeyUp = 0x0101

# 虚拟键码
Vk = {
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

# 游戏键别名
GameKeys = {
    "w": "W", "a": "A", "s": "S", "d": "D",
    "e": "E", "q": "Q", "z": "Z", "r": "R",
    "space": "SPACE", "空格": "SPACE",
    "shift": "SHIFT", "闪避": "SHIFT",
    "ctrl": "CTRL", "下蹲": "CTRL",
    "tab": "TAB", "esc": "ESC",
    "螺旋飞跃": "4", "helix": "4",
}

# ChildWindowFromPointEx flags
cwpSkipInvisible = 0x0001
cwpSkipTransparent = 0x0004


def makeLparam(x: int, y: int) -> int:
    """将坐标打包为 LPARAM"""
    return ((y & 0xFFFF) << 16) | (x & 0xFFFF)


def resolveVk(keyName: str) -> int:
    """将按键名解析为虚拟键码"""
    key = keyName.strip().upper()
    if key in Vk:
        return Vk[key]
    alias = GameKeys.get(keyName.strip().lower())
    if alias and alias in Vk:
        return Vk[alias]
    if len(key) == 1 and "A" <= key <= "Z":
        return Vk[key]
    raise ValueError(f"未知按键: {keyName}")