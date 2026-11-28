"""Regression tests: prevent Mega Salamence carryover on the base Salamence build."""
from pathlib import Path
import sys, unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import audit_base_salamence as a
from evolve import parse_team,exclusive_mega_golisopod

class BaseSalamenceTests(unittest.TestCase):
    def test_original_has_known_inherited_flaw(self):
        text=a.TEAM.read_text(encoding="utf8")
        block=next(p for p in parse_team(text) if p.species=="Salamence")
        self.assertEqual(block.item,"Focus Sash")
        self.assertIn("- Hyper Voice",block.text)
        self.assertIn("Tyranitar @ Chople Berry",text)
    def test_variants_change_only_salamence(self):
        original=parse_team(a.TEAM.read_text(encoding="utf8"))
        for item,move in a.CONFIGS.values():
            changed=parse_team(a.revise(a.TEAM.read_text(encoding="utf8"),item,move))
            self.assertTrue(exclusive_mega_golisopod(changed))
            for p,q in zip(original,changed):
                if p.species=="Salamence":
                    self.assertIn("@ "+item,q.text)
                    self.assertIn("- "+move,q.text)
                    self.assertIn("- Tailwind",q.text)
                else:
                    self.assertEqual(p.text,q.text)
    def test_selection_excludes_old_carryover(self):
        self.assertNotIn("legacy sash hyper voice",a.ELIGIBLE)
        self.assertNotIn("sash heat wave control",a.ELIGIBLE)
        self.assertEqual(len(a.ELIGIBLE),4)
    def test_rejects_drifted_team(self):
        with self.assertRaises(RuntimeError):
            a.revise(a.TEAM.read_text().replace("- Hyper Voice","- Air Slash"),"Haban Berry","Heat Wave")

if __name__=="__main__":
    unittest.main()
