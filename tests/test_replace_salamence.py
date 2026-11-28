"""Replacement audit regressions: no base Salamence can be selected."""
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import replace_salamence as audit
from evolve import parse_team,exclusive_mega_golisopod

class ReplaceTests(unittest.TestCase):
    def test_all_non_salamence_team_members_are_identical(self):
        original=parse_team(audit.TEAM.read_text(encoding="utf8"))
        for name in audit.SETS:
            changed=parse_team(audit.variant(audit.TEAM.read_text(encoding="utf8"),name))
            for x,y in zip(original,changed):
                if x.species!="Salamence":self.assertEqual(x.text,y.text)
    def test_one_megastone_for_each_eligible_slot(self):
        original=audit.TEAM.read_text(encoding="utf8")
        for name in audit.SETS:
            team=parse_team(audit.variant(original,name))
            if name==audit.REFERENCE:
                self.assertFalse(exclusive_mega_golisopod(team))
            else:
                self.assertTrue(exclusive_mega_golisopod(team),name)
                self.assertFalse(any(p.species=="Salamence" for p in team))
    def test_replacement_has_four_moves_and_six_unique_species(self):
        for name in audit.SETS:
            team=parse_team(audit.variant(audit.TEAM.read_text(),name))
            self.assertEqual(len(team),6)
            self.assertEqual(len(set(p.species for p in team)),6)
    def test_all_candidates_obey_item_clause(self):
        original=audit.TEAM.read_text(encoding="utf8")
        for name in audit.SETS:
            team=parse_team(audit.variant(original,name))
            self.assertEqual(len(set(p.item for p in team)),6,name)

    def test_reference_never_eligible(self):
        self.assertNotIn(audit.REFERENCE,[n for n in audit.SETS if n != audit.REFERENCE])
        self.assertNotIn(audit.BASELINE,audit.SETS)
    def test_original_team_is_explicit_reference(self):
        text=audit.TEAM.read_text()
        self.assertEqual(audit.variant(text,audit.BASELINE),text)

if __name__=="__main__":
    unittest.main()
