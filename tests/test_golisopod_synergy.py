"""Protect Mega Golisopod from old base-Salamence move / sand item mistakes."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from evolve import parse_team
from check_golisopod_synergy import problems

ROOT=Path(__file__).resolve().parents[1]
base=(ROOT/"teams/golisopod-current.txt").read_text(encoding="utf8")

def set_salamence(text,item="Sitrus Berry",move="Heat Wave"):
    from evolve import stringify,SetBlock
    parts=list(parse_team(text))
    i=next(i for i,p in enumerate(parts) if p.species=="Salamence")
    lines=parts[i].text.splitlines()
    lines[0]="Salamence @ "+item
    for j,line in enumerate(lines):
        if line in ("- Hyper Voice","- Heat Wave","- Air Slash"):
            lines[j]="- "+move
    parts[i]=SetBlock("\n".join(lines))
    return stringify(tuple(parts))

old=set_salamence(base,"Focus Sash","Hyper Voice")

class TeamQuality(unittest.TestCase):
    def test_detect_both_carryovers(self):
        issues=problems(parse_team(old))
        self.assertTrue(any("Aerilate" in i for i in issues))
        self.assertTrue(any("Focus Sash" in i for i in issues))
    def test_repaired_base_salamence_passes(self):
        for item in ("Sitrus Berry","Haban Berry"):
            for move in ("Air Slash","Heat Wave"):
                self.assertEqual(problems(parse_team(set_salamence(old,item,move))),[])
    def test_still_blocks_mega_salamence(self):
        x=set_salamence(old,"Salamencite","Heat Wave")
        self.assertTrue(any("only Mega Stone" in i for i in problems(parse_team(x))))
    def test_no_sand_removes_sash_conflict(self):
        x=old.replace("Ability: Sand Stream","Ability: Unnerve")
        issues=problems(parse_team(x))
        self.assertFalse(any("Focus Sash" in i for i in issues))

if __name__=="__main__":
    unittest.main()
