"""
Explore — 探险 dungeon config

Inherits BaseDungeon, only needs params, no logic overrides.
"""

from src.dungeons.base import BaseDungeon


class DungeonExplore(BaseDungeon):
    name = "探险"
    max_scroll = 3
    scroll_delta = -480
    scroll_center = (600, 800)
    battle_interval = 2.0
    battle_timeout = 180.0