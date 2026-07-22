import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SKILL = ROOT / "girlfriend-reply-coach" / "SKILL.md"


class SkillContractTests(unittest.TestCase):
    def test_skill_declares_all_three_modes_and_semantic_lock(self):
        text = SKILL.read_text(encoding="utf-8")
        for required in ("联动模式", "纯改写模式", "降级模式", "语义锁"):
            self.assertIn(required, text)

    def test_degraded_reply_requires_disclosure(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("临时版本：未经过 `goutoujunshi` 情境分析", text)

    def test_skill_uses_per_person_voice_delta_and_preserves_safety(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("people/<person-id>/voice-delta.json", text)
        self.assertIn("不得通过语气改写淡化风险", text)

    def test_skill_does_not_claim_independent_strategy_role(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertNotIn("先判断她在当前情境中表达了什么", text)
        self.assertNotIn("### 情况判断", text)


if __name__ == "__main__":
    unittest.main()
