"""Offline guards for the final one-move Archaludon comparison."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import verify_final_arch_move as m
from evolve import parse_team,locked

class ArchMoveTests(unittest.TestCase):
    def test_each_variant_changes_only_one_move(self):
        team=m.ROOT_TEAM.read_text(encoding="utf8")
        self.assertTrue(locked(parse_team(team)))
        for move in m.MOVES:
            changed=m.replace_electro(team,move)
            self.assertTrue(locked(parse_team(changed)))
            self.assertEqual(changed.count("- "+move),1)
            self.assertEqual(changed.replace("- "+move,"- Electro Shot"),team)
    def test_cannot_ablate_missing_move(self):
        with self.assertRaises(RuntimeError):
            m.replace_electro(m.ROOT_TEAM.read_text().replace("- Electro Shot","- Protect"),"Flash Cannon")

if __name__=="__main__":
    unittest.main()
