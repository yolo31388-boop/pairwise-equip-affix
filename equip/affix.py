"""装备词缀与附魔系统"""
import random
from dataclasses import dataclass, field

QUALITY_TIERS = {"common": 0, "rare": 1, "legendary": 2}

RARITY_WEIGHTS = {"common": 50.0, "rare": 5.0, "legendary": 0.5}

ALL_SLOTS = ("weapon", "armor", "helmet", "boots", "gloves")
ARMOR_SLOTS = ("armor", "helmet", "boots", "gloves")

AFFIX_DEFS = {
    "atk": {
        "rarity": "common", "min_level": 1, "min_quality": "common",
        "slots": None, "base": 10.0,
    },
    "def": {
        "rarity": "common", "min_level": 1, "min_quality": "common",
        "slots": None, "base": 10.0,
    },
    "hp": {
        "rarity": "common", "min_level": 1, "min_quality": "common",
        "slots": None, "base": 20.0,
    },
    "crit": {
        "rarity": "rare", "min_level": 5, "min_quality": "rare",
        "slots": None, "base": 5.0,
    },
    "lifesteal": {
        "rarity": "rare", "min_level": 5, "min_quality": "rare",
        "slots": ("weapon",), "base": 3.0,
    },
    "legendary_affix": {
        "rarity": "legendary", "min_level": 10, "min_quality": "legendary",
        "slots": None, "base": 50.0,
    },
    "weapon_only": {
        "rarity": "common", "min_level": 1, "min_quality": "common",
        "slots": ("weapon",), "base": 8.0,
    },
    "armor_only": {
        "rarity": "common", "min_level": 1, "min_quality": "common",
        "slots": ARMOR_SLOTS, "base": 8.0,
    },
}

ELEMENTAL_ENCHANTS = frozenset({"fire", "ice", "lightning"})

DEFAULT_ENCHANT_LIMIT = 2
DEFAULT_ENCHANT_DURABILITY = 100.0
DEFAULT_PITY_THRESHOLD = 10
MAX_LOCKED_AFFIXES = 2
SET_PIECES_REQUIRED = 3


@dataclass
class Enchant:
    name: str
    durability: float = DEFAULT_ENCHANT_DURABILITY
    max_durability: float = DEFAULT_ENCHANT_DURABILITY

    @property
    def active(self) -> bool:
        return self.durability > 0


@dataclass
class Equipment:
    eid: str
    name: str
    level: int = 1
    quality: str = "common"
    slot: str = "weapon"
    affixes: list = field(default_factory=list)
    enchants: list = field(default_factory=list)

    @property
    def active_enchants(self) -> list:
        return [e for e in self.enchants if isinstance(e, Enchant) and e.active]


class AffixSystem:
    def __init__(self, seed=42):
        self.rng = random.Random(seed)
        self.affix_pool: dict = dict(AFFIX_DEFS)
        self.pity_counter: dict = {}
        self.pity_threshold = DEFAULT_PITY_THRESHOLD
        self.max_locked = MAX_LOCKED_AFFIXES
        self.enchant_limit = DEFAULT_ENCHANT_LIMIT
        self.enchant_max_durability = DEFAULT_ENCHANT_DURABILITY
        self._equipments: dict = {}

    def register_equipment(self, equip: Equipment) -> None:
        self._equipments[equip.eid] = equip

    def get_available_affixes(self, equip_level: int, quality: str, slot: str = None) -> list:
        tier = QUALITY_TIERS.get(quality, 0)
        result = []
        for affix, definition in self.affix_pool.items():
            if equip_level < definition["min_level"]:
                continue
            if QUALITY_TIERS[definition["min_quality"]] > tier:
                continue
            if slot is not None and not self.can_roll_affix(affix, slot):
                continue
            result.append(affix)
        return result

    def get_affix_weight(self, affix: str) -> float:
        definition = self.affix_pool.get(affix)
        if definition is None:
            return 1.0
        return RARITY_WEIGHTS[definition["rarity"]]

    def roll_affix_value(self, affix: str, level: int) -> float:
        base = level * self.affix_pool.get(affix, {}).get("base", 10.0)
        multiplier = self.rng.uniform(0.8, 1.2)
        return round(base * multiplier, 2)

    def _value_grade(self, multiplier: float) -> str:
        if multiplier >= 1.1:
            return "极品"
        if multiplier <= 0.9:
            return "次品"
        return "普通"

    def roll_affix(self, affix: str, level: int) -> dict:
        base = level * self.affix_pool.get(affix, {}).get("base", 10.0)
        multiplier = self.rng.uniform(0.8, 1.2)
        return {
            "id": affix,
            "value": round(base * multiplier, 2),
            "multiplier": round(multiplier, 3),
            "grade": self._value_grade(multiplier),
            "rarity": self.affix_pool.get(affix, {}).get("rarity", "common"),
        }

    def roll_random_affix(self, equip_level: int, quality: str, slot: str) -> dict:
        pool = self.get_available_affixes(equip_level, quality, slot)
        if not pool:
            return {}
        weights = [self.get_affix_weight(affix) for affix in pool]
        chosen = self.rng.choices(pool, weights=weights, k=1)[0]
        return self.roll_affix(chosen, equip_level)

    def roll_equipment_affixes(self, equip: Equipment, count: int) -> list:
        rolled = []
        for _ in range(count):
            entry = self.roll_random_affix(equip.level, equip.quality, equip.slot)
            if entry:
                rolled.append(entry)
        equip.affixes.extend(rolled)
        return rolled

    def get_enchant_limit(self) -> int:
        return self.enchant_limit

    def check_enchant_conflict(self, e1: str, e2: str) -> bool:
        return e1 in ELEMENTAL_ENCHANTS and e2 in ELEMENTAL_ENCHANTS

    def add_enchant(self, equip: Equipment, enchant: str) -> dict:
        active = equip.active_enchants
        if len(active) >= self.get_enchant_limit():
            return {"ok": False, "reason": "enchant_limit_reached"}
        for existing in active:
            if existing.name == enchant or self.check_enchant_conflict(existing.name, enchant):
                return {"ok": False, "reason": "enchant_conflict", "conflict_with": existing.name}
        entry = Enchant(enchant, self.enchant_max_durability, self.enchant_max_durability)
        equip.enchants.append(entry)
        return {"ok": True, "enchant": entry}

    def get_enchant_durability(self, enchant) -> float:
        if isinstance(enchant, Enchant):
            return enchant.durability
        return float(self.enchant_max_durability)

    def consume_enchant_durability(self, equip: Equipment, amount: float = 1.0, name: str = None) -> list:
        expired = []
        for entry in equip.enchants:
            if not isinstance(entry, Enchant) or not entry.active:
                continue
            if name is not None and entry.name != name:
                continue
            entry.durability = max(0.0, entry.durability - amount)
            if not entry.active:
                expired.append(entry.name)
        return expired

    def on_equipment_use(self, equip: Equipment, amount: float = 1.0) -> list:
        return self.consume_enchant_durability(equip, amount)

    def replenish_enchant(self, equip: Equipment, name: str, amount: float = None) -> float:
        for entry in equip.enchants:
            if isinstance(entry, Enchant) and entry.name == name:
                refill = entry.max_durability if amount is None else amount
                entry.durability = min(entry.max_durability, entry.durability + refill)
                return entry.durability
        return 0.0

    def reforge_affix(self, eid: str, affix_index: int, locked: list = None,
                      target_quality: str = "rare") -> dict:
        locked = list(locked or [])
        if len(locked) > self.max_locked:
            raise ValueError(f"at most {self.max_locked} affixes can be locked")

        equip = self._equipments.get(eid)
        if affix_index in locked:
            current = equip.affixes[affix_index] if equip and affix_index < len(equip.affixes) else None
            return {"locked": True, "affix": current}

        count = self.pity_counter.get(eid, 0) + 1
        self.pity_counter[eid] = count
        guaranteed = count >= self.pity_threshold

        if guaranteed:
            rarity = target_quality
            self.pity_counter[eid] = 0
        else:
            rarities = list(RARITY_WEIGHTS)
            rarity = self.rng.choices(rarities, weights=[RARITY_WEIGHTS[r] for r in rarities], k=1)[0]

        level = equip.level if equip else 1
        pool = self.get_available_affixes(level, self._rarity_as_quality(rarity),
                                          equip.slot if equip else None)
        affix = self.rng.choice(pool) if pool else "atk"
        result = self.roll_affix(affix, level)
        result["rarity"] = rarity
        result["guaranteed"] = guaranteed
        result["pity"] = self.pity_counter[eid]
        if equip is not None and affix_index < len(equip.affixes):
            equip.affixes[affix_index] = result
        result["new_value"] = result["value"]
        return result

    @staticmethod
    def _rarity_as_quality(rarity: str) -> str:
        if rarity in QUALITY_TIERS:
            return rarity
        return "common"

    def check_set_bonus(self, affixes: list) -> dict:
        groups: dict = {}
        for affix in affixes:
            set_id = affix.get("id") if isinstance(affix, dict) else getattr(affix, "set_id", None)
            if set_id is None:
                continue
            groups[set_id] = groups.get(set_id, 0) + 1
        for set_id, count in groups.items():
            if count >= SET_PIECES_REQUIRED:
                return {"bonus": f"{set_id}_3piece", "set_id": set_id, "count": count}
        return {}

    def can_roll_affix(self, affix: str, slot: str) -> bool:
        definition = self.affix_pool.get(affix)
        if definition is None:
            return not affix.endswith("_only") or affix.startswith(slot)
        allowed_slots = definition.get("slots")
        if allowed_slots is None:
            return True
        return slot in allowed_slots
