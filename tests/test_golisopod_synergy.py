"""Protect Mega Golisopod from old base-Salamence move / sand item mistakes."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from evolve import parse_team
from check_golisopod_synergy import problems

ROOT=Path(__file__).resolve().parents[1]
old=(ROOT/"teams/golisopod-current.txt").read_text(encoding="utf8")

def fix(text,item="Sitrus Berry",move="Heat Wave"):
    return text.replace("Salamence @ Focus Sash","Salamence @ "+item).replace("- Hyper Voice","- "+move)

class TeamQuality(unittest.TestCase):
    def test_detect_both_carryovers(self):
        issues=problems(parse_team(old))
        self.assertTrue(any("Aerilate" in i for i in issues))
        self.assertTrue(any("Focus Sash" in i for i in issues))
    def test_repaired_base_salamence_passes(self):
        for item in ("Sitrus Berry","Haban Berry"):
            for move in ("Air Slash","Heat Wave"):
                self.assertEqual(problems(parse_team(fix(old,item,move))),[])
    def test_still_blocks_mega_salamence(self):
        x=fix(old).replace("Salamence @ Sitrus Berry","Salamence @ Salamencite")
        self.assertTrue(any("only Mega Stone" in i for i in problems(parse_team(x))))
    def test_no_sand_removes_sash_conflict(self):
        x=old.replace("Ability: Sand Stream","Ability: Unnerve")
        issues=problems(parse_team(x))
        self.assertFalse(any("Focus Sash" in i for i in issues))

if __name__=="__main__":
    unittest.main()
