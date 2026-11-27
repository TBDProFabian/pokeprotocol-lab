"""Offline checks for final Golisopod independent stress audit."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import stress_golisopod as audit
from evolve import parse_team,locked

class StressAuditTests(unittest.TestCase):
    def test_archive_contains_valid_six_and_locked_golisopod(self):
        for label,path in audit.CHALLENGERS.items():
            if label=="V2 evolved":
                continue
            team=parse_team(path.read_text(encoding="utf8"))
            self.assertTrue(locked(team),label)
            self.assertEqual(len(team),6)
    def test_recent_registered_winners_reconstruct_from_full_sheets(self):
        with tempfile.TemporaryDirectory() as d,patch.object(audit,"OUT",Path(d)):
            opponents=audit.winner_ots()
            self.assertEqual(len(opponents),2)
            for path in opponents.values():
                self.assertEqual(len(parse_team(path.read_text(encoding="utf8"))),6)
    def test_laic_published_team_has_six_inferred_valid_stat_point_sets(self):
        path=audit.ARCHETYPES["LAIC champion published-set proxy"]
        team=parse_team(path.read_text(encoding="utf8"))
        self.assertEqual(len(team),6)
        self.assertIn("- Electro Shot",next(x.text for x in team if x.species=="Archaludon"))
        self.assertIn("- Hypnosis",next(x.text for x in team if x.species=="Politoed"))
        self.assertIn("Relaxed Nature",next(x.text for x in team if x.species=="Rillaboom"))

    def test_fixed_preview_patch_required(self):
        self.assertEqual(audit.FIX,"POKEPROTOCOL_WEATHER_PREVIEW_V2")
        self.assertNotEqual(audit.FAST_FIELD,audit.HOLDOUT)

if __name__=="__main__":
    unittest.main()
