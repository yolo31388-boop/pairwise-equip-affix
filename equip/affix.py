"""装备词缀与附魔系统 - 含9个bug"""
import random
from dataclasses import dataclass, field

@dataclass
class Equipment:
    eid: str
    name: str
    level: int = 1
    quality: str = "common"
    slot: str = "weapon"
    affixes: list = field(default_factory=list)
    enchants: list = field(default_factory=list)  # bug4: 无限叠加

class AffixSystem:
    def __init__(self, seed=42):
        self.rng = random.Random(seed)
        self.affix_pool: dict = {}  # bug1: 无等级分层

    def get_available_affixes(self, equip_level: int, quality: str) -> list:
        # bug1: 无等级区分
        return ["atk", "def", "hp", "crit", "legendary_affix"]

    def get_affix_weight(self, affix: str) -> float:
        # bug2: 平均权重
        return 1.0

    def roll_affix_value(self, affix: str, level: int) -> float:
        # bug3: 固定值
        return level * 10.0

    def get_enchant_limit(self) -> int:
        # bug4: 无上限
        return 999

    def check_enchant_conflict(self, e1: str, e2: str) -> bool:
        # bug5: 无冲突
        return False

    def reforge_affix(self, eid: str, affix_index: int, locked: list) -> dict:
        # bug6: 完全随机无保底
        return {"new_value": self.rng.randint(1, 100)}

    def get_enchant_durability(self, enchant: str) -> float:
        # bug7: 无耐久
        return float("inf")

    def check_set_bonus(self, affixes: list) -> dict:
        # bug8: 不看ID只看数量
        if len(affixes) >= 3:
            return {"bonus": "3piece"}
        return {}

    def can_roll_affix(self, affix: str, slot: str) -> bool:
        # bug9: 跨部位
        return True
