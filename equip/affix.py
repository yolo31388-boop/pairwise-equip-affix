"""装备词缀与附魔系统 - 修复版"""
import random
from dataclasses import dataclass, field

# 词缀品质权重：传说0.5% / 稀有5% / 普通50%（其余为填充权重）
QUALITY_WEIGHTS = {
    "legendary": 0.005,
    "rare": 0.05,
    "common": 0.50,
}

# 词缀表：品质、最低装备等级、允许部位
AFFIX_TABLE = {
    "atk":             {"quality": "common",    "min_level": 1,  "slots": {"weapon", "ring"}},
    "def":             {"quality": "common",    "min_level": 1,  "slots": {"armor", "helmet", "shield"}},
    "hp":              {"quality": "common",    "min_level": 1,  "slots": {"armor", "helmet", "shield", "ring"}},
    "crit":            {"quality": "rare",      "min_level": 10, "slots": {"weapon", "ring"}},
    "weapon_only":     {"quality": "rare",      "min_level": 1,  "slots": {"weapon"}},
    "legendary_affix": {"quality": "legendary", "min_level": 50, "slots": {"weapon"}},
}

# 附魔冲突组：同组互斥（火/冰/雷），攻/防类可共存
ENCHANT_CONFLICT_GROUPS = [
    {"fire", "ice", "lightning"},
]

ENCHANT_LIMIT = 2
ENCHANT_DURABILITY = 100.0
VALUE_VARIANCE = 0.20  # ±20% 浮动
PITY_THRESHOLD = 50    # 洗练保底：50次必出目标品质


@dataclass
class Equipment:
    eid: str
    name: str
    level: int = 1
    quality: str = "common"
    slot: str = "weapon"
    affixes: list = field(default_factory=list)
    enchants: list = field(default_factory=list)  # 最多 ENCHANT_LIMIT 个


class AffixSystem:
    def __init__(self, seed=42):
        self.rng = random.Random(seed)
        self.affix_pool: dict = dict(AFFIX_TABLE)
        self.pity_counter: dict = {}  # 洗练保底计数器 {eid: 次数}

    # bug1 修复：按装备等级和品质分层
    def get_available_affixes(self, equip_level: int, quality: str) -> list:
        quality_rank = {"common": 0, "rare": 1, "legendary": 2}
        equip_rank = quality_rank.get(quality, 0)
        return [
            name for name, meta in self.affix_pool.items()
            if meta["min_level"] <= equip_level
            and quality_rank[meta["quality"]] <= equip_rank
        ]

    # bug2 修复：按品质加权，稀有概率低
    def get_affix_weight(self, affix: str) -> float:
        meta = self.affix_pool.get(affix)
        if meta is None:
            return QUALITY_WEIGHTS["common"]
        return QUALITY_WEIGHTS[meta["quality"]]

    # bug3 修复：基础值 ±20% 浮动，有极品次品
    def roll_affix_value(self, affix: str, level: int) -> float:
        base = level * 10.0
        factor = self.rng.uniform(1.0 - VALUE_VARIANCE, 1.0 + VALUE_VARIANCE)
        return round(base * factor, 2)

    # bug4 修复：附魔数量上限
    def get_enchant_limit(self) -> int:
        return ENCHANT_LIMIT

    def add_enchant(self, equip: Equipment, enchant: str) -> bool:
        if len(equip.enchants) >= self.get_enchant_limit():
            return False
        for existing in equip.enchants:
            name = existing["name"] if isinstance(existing, dict) else existing
            if self.check_enchant_conflict(name, enchant):
                return False
        equip.enchants.append({"name": enchant, "durability": ENCHANT_DURABILITY})
        return True

    # bug5 修复：冲突规则（火/冰/雷互斥，攻/防可共存）
    def check_enchant_conflict(self, e1: str, e2: str) -> bool:
        if e1 == e2:
            return True
        for group in ENCHANT_CONFLICT_GROUPS:
            if e1 in group and e2 in group:
                return True
        return False

    # bug6 修复：洗练支持锁定1-2条 + 保底计数器
    def reforge_affix(self, eid: str, affix_index: int, locked: list,
                      target_quality: str = "rare") -> dict:
        locked = locked or []
        if len(locked) > 2:
            raise ValueError("最多锁定2条词缀")
        count = self.pity_counter.get(eid, 0) + 1
        if count >= PITY_THRESHOLD:
            # 保底：必出目标品质
            quality = target_quality
            self.pity_counter[eid] = 0
        else:
            roll = self.rng.random()
            if roll < QUALITY_WEIGHTS["legendary"]:
                quality = "legendary"
            elif roll < QUALITY_WEIGHTS["legendary"] + QUALITY_WEIGHTS["rare"]:
                quality = "rare"
            else:
                quality = "common"
            self.pity_counter[eid] = 0 if quality == target_quality else count
        return {
            "affix_index": affix_index,
            "locked": list(locked),
            "quality": quality,
            "new_value": self.rng.randint(1, 100),
        }

    # bug7 修复：附魔有耐久，使用中消耗
    def get_enchant_durability(self, enchant: str) -> float:
        return ENCHANT_DURABILITY

    def consume_enchant_durability(self, equip: Equipment, amount: float = 1.0) -> None:
        remaining = []
        for ench in equip.enchants:
            if isinstance(ench, dict):
                ench["durability"] = ench.get("durability", ENCHANT_DURABILITY) - amount
                if ench["durability"] > 0:
                    remaining.append(ench)
            else:
                remaining.append(ench)
        equip.enchants = remaining

    # bug8 修复：套装按词缀ID分组，同ID达到数量才触发
    def check_set_bonus(self, affixes: list) -> dict:
        counts: dict = {}
        for affix in affixes:
            affix_id = affix.get("id") if isinstance(affix, dict) else affix
            counts[affix_id] = counts.get(affix_id, 0) + 1
        return {affix_id: "3piece" for affix_id, count in counts.items() if count >= 3}

    # bug9 修复：词缀部位限制
    def can_roll_affix(self, affix: str, slot: str) -> bool:
        meta = self.affix_pool.get(affix)
        if meta is None:
            return False
        return slot in meta["slots"]
