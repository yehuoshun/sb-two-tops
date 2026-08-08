"""
副本模块注册表 — 按名称查找副本类
"""

from src.dungeons.扼守 import Dungeon扼守
from src.dungeons.探险 import Dungeon探险

_DUNGEON_MAP = {
    "扼守": Dungeon扼守,
    "探险": Dungeon探险,
}


def get_dungeon(name: str):
    """按名称获取副本类

    Raises:
        ValueError: 未知副本名
    """
    cls = _DUNGEON_MAP.get(name)
    if cls is None:
        raise ValueError(f"未知副本: {name}，可用: {list(_DUNGEON_MAP.keys())}")
    return cls


def register_dungeon(name: str, cls):
    """注册新副本"""
    _DUNGEON_MAP[name] = cls