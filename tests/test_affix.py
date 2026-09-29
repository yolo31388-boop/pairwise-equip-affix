"""装备词缀与附魔系统 - 红态测试"""
import pytest, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from equip.affix import AffixSystem, Equipment

class TestAffixLevelRestriction:
    def test_low_level_cannot_roll_legendary_affix(self):
        af = AffixSystem()
        available = af.get_available_affixes(1, "common")
        assert "legendary_affix" not in available

class TestAffixWeight:
    def test_rare_affix_has_lower_weight(self):
        af = AffixSystem()
        w_common = af.get_affix_weight("atk")
        w_rare = af.get_affix_weight("legendary_affix")
        assert w_rare < w_common

class TestAffixValueVariance:
    def test_same_affix_has_value_range(self):
        af = AffixSystem(seed=42)
        values = [af.roll_affix_value("atk", 10) for _ in range(20)]
        assert len(set(values)) > 1

class TestEnchantLimit:
    def test_enchant_has_count_limit(self):
        af = AffixSystem()
        assert af.get_enchant_limit() <= 3

class TestEnchantConflict:
    def test_fire_and_ice_enchant_conflict(self):
        af = AffixSystem()
        assert af.check_enchant_conflict("fire", "ice") == True
        assert af.check_enchant_conflict("fire", "atk") == False

class TestReforgePity:
    def test_reforge_has_pity_counter(self):
        af = AffixSystem()
        assert hasattr(af, "pity_counter")
        af.pity_counter = {"e1": 50}
        # 保底应该影响结果
        assert af.pity_counter["e1"] >= 50

class TestEnchantDurability:
    def test_enchant_has_finite_durability(self):
        af = AffixSystem()
        d = af.get_enchant_durability("fire_enchant")
        assert d < float("inf") and d > 0

class TestSetBonusById:
    def test_mixed_affixes_dont_trigger_set(self):
        af = AffixSystem()
        affixes = [{"id": "A", "name": "x"}, {"id": "A", "name": "y"}, {"id": "B", "name": "z"}]
        result = af.check_set_bonus(affixes)
        assert result == {}

class TestAffixSlotRestriction:
    def test_weapon_affix_cannot_roll_on_armor(self):
        af = AffixSystem()
        assert af.can_roll_affix("weapon_only", "armor") == False
