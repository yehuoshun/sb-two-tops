"""
Guard — 扼守 dungeon config

Inherits BaseDungeon, only needs params, no logic overrides.
"""

from src.dungeons.base import BaseDungeon


class DungeonGuard(BaseDungeon):
    name = "扼守"
    max_scroll = 5
    scroll_delta = -480  # 4 格，滚动幅度大一些
    scroll_center = (600, 800)  # 卡片区域中心，光标移过去再滚
    battle_interval = 2.0
    battle_timeout = 180.0